import {
  AuthenticationExpiredError,
  expireSession,
  refreshAccessTokenWithQueue,
  request,
  resolveApiUrl,
  shouldExpireSessionAfterRefreshError,
} from '@/api/http'
import { getAccessToken } from '@/utils/token'
import {
  isUnknownRecord,
  normalizeChatMessagePage,
  normalizeChatSession,
  normalizeChatSessionPage,
  parseChatSseData,
  readString,
} from '@/utils/chatSessions'
import { ChatSseParser } from '@/utils/chatSse'
import { compactParams } from '@/utils/contracts'
import type {
  ChatMessagePage,
  ChatMessagePayload,
  ChatRetryPayload,
  ChatSession,
  ChatSessionCreatePayload,
  ChatSessionQuery,
  ChatSessionRenamePayload,
  ChatStreamEvent,
  ChatStreamResult,
  ChatContext,
} from '@/types/chat'

export interface ChatStreamHandlers {
  onEvent: (event: ChatStreamEvent) => void
}

function readErrorMessage(value: unknown, fallback: string): string {
  if (!isUnknownRecord(value)) {
    return fallback
  }

  const message = readString(value, ['message', 'detail', 'error'])
  if (message) {
    return message
  }

  const nested = value.data
  if (isUnknownRecord(nested)) {
    return readString(nested, ['message', 'detail', 'error']) || fallback
  }

  return fallback
}

async function parseResponseError(response: Response): Promise<string> {
  const fallback = `请求失败（${response.status}）`
  const text = await response.text().catch(() => '')

  if (!text) {
    return fallback
  }

  try {
    const parsed: unknown = JSON.parse(text)
    return readErrorMessage(parsed, text)
  } catch {
    return text
  }
}

async function fetchWithAuth(
  url: string,
  init: RequestInit,
  signal?: AbortSignal,
): Promise<Response> {
  const execute = (token: string): Promise<Response> =>
    fetch(url, {
      ...init,
      signal,
      headers: {
        ...init.headers,
        Authorization: `Bearer ${token}`,
      },
    })

  let response = await execute(getAccessToken())

  if (response.status !== 401) {
    return response
  }

  let token: string
  try {
    token = await refreshAccessTokenWithQueue()
  } catch (error) {
    if (shouldExpireSessionAfterRefreshError(error)) {
      expireSession()
    }
    throw error
  }

  response = await execute(token)

  if (response.status === 401) {
    expireSession()
    throw new AuthenticationExpiredError('登录状态已失效，请重新登录')
  }

  return response
}

export function buildChatStreamHeaders(requestId: string): Record<string, string> {
  return {
    Accept: 'text/event-stream',
    'Content-Type': 'application/json',
    'Idempotency-Key': requestId,
    'X-Request-ID': requestId,
  }
}

async function streamChatRequest(
  path: string,
  requestId: string,
  payload: ChatMessagePayload | ChatRetryPayload | undefined,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<ChatStreamResult> {
  const response = await fetchWithAuth(
    resolveApiUrl(path),
    {
      method: 'POST',
      headers: buildChatStreamHeaders(requestId),
      body: payload ? JSON.stringify(payload) : undefined,
    },
    signal,
  )

  if (!response.ok) {
    throw new Error(await parseResponseError(response))
  }

  if (!response.body) {
    throw new Error('服务端未返回可读取的流')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  const parser = new ChatSseParser()
  let receivedDone = false

  const dispatch = (events: ChatStreamEvent[]): void => {
    for (const event of events) {
      handlers.onEvent(event)

      if (event.event === 'done') {
        receivedDone = true
      }

      if (event.event === 'error') {
        const data = parseChatSseData(event)
        throw new Error(readErrorMessage(data, '回答生成失败'))
      }
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    dispatch(parser.push(decoder.decode(value, { stream: true })))
  }

  dispatch(parser.push(decoder.decode()))
  dispatch(parser.flush())

  if (!receivedDone && !signal?.aborted) {
    throw new Error('回答连接已断开，请重试')
  }

  return {
    completed: receivedDone,
  }
}

export async function fetchChatSessions(
  query: ChatSessionQuery,
): Promise<ReturnType<typeof normalizeChatSessionPage>> {
  const result = await request<unknown>({
    url: '/ai/chat/sessions',
    method: 'GET',
    params: compactParams(query),
  })

  return normalizeChatSessionPage(result)
}

export async function fetchChatSession(id: number): Promise<ChatSession> {
  const result = await request<unknown>({
    url: `/ai/chat/sessions/${id}`,
    method: 'GET',
  })
  const session = normalizeChatSession(result)

  if (!session) {
    throw new Error('会话数据格式不正确')
  }

  return session
}

export async function createChatSession(
  payload: ChatSessionCreatePayload,
): Promise<ChatSession> {
  const result = await request<unknown>({
    url: '/ai/chat/sessions',
    method: 'POST',
    data: payload,
  })
  const session = normalizeChatSession(result)

  if (!session) {
    throw new Error('创建会话失败：返回数据格式不正确')
  }

  return session
}

export async function renameChatSession(
  id: number,
  payload: ChatSessionRenamePayload,
): Promise<ChatSession | null> {
  const result = await request<unknown>({
    url: `/ai/chat/sessions/${id}`,
    method: 'PATCH',
    data: payload,
  })

  return normalizeChatSession(result)
}

export async function updateChatSessionContext(
  id: number,
  context: ChatContext,
): Promise<ChatSession | null> {
  const result = await request<unknown>({
    url: `/ai/chat/sessions/${id}/context`,
    method: 'PATCH',
    data: context,
  })

  return normalizeChatSession(result)
}

export function deleteChatSession(id: number): Promise<void> {
  return request<void>({
    url: `/ai/chat/sessions/${id}`,
    method: 'DELETE',
  })
}

export async function fetchChatMessages(
  sessionId: number,
  query: {
    before_sequence?: number
    page_size: number
  },
): Promise<ChatMessagePage> {
  const result = await request<unknown>({
    url: `/ai/chat/sessions/${sessionId}/messages`,
    method: 'GET',
    params: compactParams(query),
  })

  return normalizeChatMessagePage(result, sessionId)
}

export function streamChatMessage(
  sessionId: number,
  payload: ChatMessagePayload,
  requestId: string,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<ChatStreamResult> {
  return streamChatRequest(
    `/ai/chat/sessions/${sessionId}/messages`,
    requestId,
    payload,
    handlers,
    signal,
  )
}

export function retryChatAssistant(
  assistantId: string,
  requestId: string,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<ChatStreamResult> {
  const payload: ChatRetryPayload = {
    stream: true,
  }

  return streamChatRequest(
    `/ai/chat/messages/${encodeURIComponent(assistantId)}/retry`,
    requestId,
    payload,
    handlers,
    signal,
  )
}

export function stopChatAssistant(assistantId: string): Promise<void> {
  return request<void>({
    url: `/ai/chat/messages/${encodeURIComponent(assistantId)}/stop`,
    method: 'POST',
    silentError: true,
  })
}
