import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createChatSession,
  deleteChatSession,
  fetchChatMessages,
  fetchChatSession,
  fetchChatSessions,
  renameChatSession,
  retryChatAssistant,
  stopChatAssistant,
  streamChatMessage,
  updateChatSessionContext,
  type ChatStreamHandlers,
} from '@/api/chat'
import type {
  ChatContext,
  ChatMessage,
  ChatMessageId,
  ChatMessagePayload,
  ChatProgress,
  ChatSession,
  ChatStreamEvent,
} from '@/types/chat'
import {
  createChatRequestId,
  isAbortError,
  mergeChatCitations,
  mergeChatContexts,
  normalizeCitation,
  normalizeCitations,
  parseChatSseData,
  readNumber,
  readRecord,
  readString,
  resolveDoneMessageStatus,
  resolveHistoryBeforeSequence,
  upsertChatMessages,
} from '@/utils/chatSessions'
import { getErrorMessage } from '@/utils/error'

function moveSessionToTop(
  sessions: readonly ChatSession[],
  session: ChatSession,
): ChatSession[] {
  return [session, ...sessions.filter((item) => item.id !== session.id)]
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const sessionsLoading = ref(false)
  const sessionsLoadingMore = ref(false)
  const sessionsError = ref('')
  const sessionTotal = ref(0)
  const sessionPage = ref(1)
  const sessionKeyword = ref('')
  const creatingSession = ref(false)

  const activeSessionId = ref<number | null>(null)
  const sessionDetailLoading = ref(false)
  const sessionDetailError = ref('')

  const messagesBySession = ref<Record<number, ChatMessage[]>>({})
  const messageLoadingBySession = ref<Record<number, boolean>>({})
  const messageErrorBySession = ref<Record<number, string>>({})
  const hasMoreBySession = ref<Record<number, boolean>>({})
  const nextBeforeSequenceBySession = ref<Record<number, number | null>>({})
  const progressBySession = ref<Record<number, ChatProgress | null>>({})
  const sendingSessionIds = ref<number[]>([])

  const streamControllers = new Map<number, AbortController>()
  let sessionRequestSequence = 0

  const activeSession = computed(
    () =>
      sessions.value.find((session) => session.id === activeSessionId.value) ??
      null,
  )
  const activeMessages = computed(() =>
    activeSessionId.value
      ? messagesBySession.value[activeSessionId.value] ?? []
      : [],
  )
  const activeMessageLoading = computed(() =>
    activeSessionId.value
      ? messageLoadingBySession.value[activeSessionId.value] === true
      : false,
  )
  const activeMessageError = computed(() =>
    activeSessionId.value
      ? messageErrorBySession.value[activeSessionId.value] ?? ''
      : '',
  )
  const activeHasMore = computed(() =>
    activeSessionId.value
      ? hasMoreBySession.value[activeSessionId.value] === true
      : false,
  )
  const activeProgress = computed(() =>
    activeSessionId.value
      ? progressBySession.value[activeSessionId.value] ?? null
      : null,
  )
  const activeSending = computed(() =>
    activeSessionId.value
      ? sendingSessionIds.value.includes(activeSessionId.value)
      : false,
  )

  function isSessionSending(sessionId: number): boolean {
    return sendingSessionIds.value.includes(sessionId)
  }

  function getMessages(sessionId: number): ChatMessage[] {
    return messagesBySession.value[sessionId] ?? []
  }

  function setMessages(sessionId: number, messages: ChatMessage[]): void {
    messagesBySession.value = {
      ...messagesBySession.value,
      [sessionId]: messages,
    }
  }

  function setSending(sessionId: number, sending: boolean): void {
    if (sending) {
      if (!sendingSessionIds.value.includes(sessionId)) {
        sendingSessionIds.value = [...sendingSessionIds.value, sessionId]
      }
      return
    }

    sendingSessionIds.value = sendingSessionIds.value.filter(
      (item) => item !== sessionId,
    )
  }

  function updateSessionInList(session: ChatSession): void {
    sessions.value = moveSessionToTop(sessions.value, session)
  }

  function patchAssistant(
    sessionId: number,
    requestId: string,
    updater: (message: ChatMessage) => ChatMessage,
  ): void {
    const current = getMessages(sessionId)
    let changed = false

    const next = current.map((message) => {
      if (
        message.role !== 'ASSISTANT' ||
        message.request_id !== requestId
      ) {
        return message
      }

      changed = true
      return updater(message)
    })

    if (changed) {
      setMessages(sessionId, next)
    }
  }

  function updateMessageById(
    sessionId: number,
    messageId: ChatMessageId,
    updater: (message: ChatMessage) => ChatMessage,
  ): void {
    const current = getMessages(sessionId)
    let changed = false

    const next = current.map((message) => {
      if (message.id !== messageId) {
        return message
      }

      changed = true
      return updater(message)
    })

    if (changed) {
      setMessages(sessionId, next)
    }
  }

  async function loadSessions(
    options: {
      reset?: boolean
      keyword?: string
    } = {},
  ): Promise<void> {
    const reset = options.reset !== false
    const keyword = options.keyword ?? sessionKeyword.value
    const nextPage = reset ? 1 : sessionPage.value + 1
    const requestSequence = ++sessionRequestSequence

    if (reset) {
      sessionsLoading.value = true
    } else {
      sessionsLoadingMore.value = true
    }
    sessionsError.value = ''

    try {
      const result = await fetchChatSessions({
        page: nextPage,
        page_size: 20,
        keyword,
      })

      if (requestSequence !== sessionRequestSequence) {
        return
      }

      sessionKeyword.value = keyword
      sessionTotal.value = result.total
      sessionPage.value = result.page || nextPage

      if (reset) {
        sessions.value = result.items
      } else {
        const existingIds = new Set(sessions.value.map((item) => item.id))
        sessions.value = [
          ...sessions.value,
          ...result.items.filter((item) => !existingIds.has(item.id)),
        ]
      }
    } catch (error) {
      if (requestSequence === sessionRequestSequence) {
        sessionsError.value = getErrorMessage(error)
      }
    } finally {
      if (requestSequence === sessionRequestSequence) {
        sessionsLoading.value = false
        sessionsLoadingMore.value = false
      }
    }
  }

  async function loadMoreSessions(): Promise<void> {
    if (
      sessionsLoading.value ||
      sessionsLoadingMore.value ||
      sessions.value.length >= sessionTotal.value
    ) {
      return
    }

    await loadSessions({
      reset: false,
      keyword: sessionKeyword.value,
    })
  }

  async function loadMessages(
    sessionId: number,
    options: { older?: boolean } = {},
  ): Promise<void> {
    const older = options.older === true
    const current = getMessages(sessionId)
    const beforeSequence = older
      ? resolveHistoryBeforeSequence(
          nextBeforeSequenceBySession.value[sessionId],
          current[0]?.sequence,
        )
      : undefined

    if (older && !beforeSequence) {
      return
    }

    messageLoadingBySession.value = {
      ...messageLoadingBySession.value,
      [sessionId]: true,
    }
    messageErrorBySession.value = {
      ...messageErrorBySession.value,
      [sessionId]: '',
    }

    try {
      const result = await fetchChatMessages(sessionId, {
        before_sequence: beforeSequence,
        page_size: older ? 30 : 50,
      })
      const next = older
        ? upsertChatMessages(current, result.items)
        : result.items

      setMessages(sessionId, next)
      hasMoreBySession.value = {
        ...hasMoreBySession.value,
        [sessionId]: result.has_more === true,
      }
      nextBeforeSequenceBySession.value = {
        ...nextBeforeSequenceBySession.value,
        [sessionId]: result.next_before_sequence ?? null,
      }
    } catch (error) {
      messageErrorBySession.value = {
        ...messageErrorBySession.value,
        [sessionId]: getErrorMessage(error),
      }
    } finally {
      messageLoadingBySession.value = {
        ...messageLoadingBySession.value,
        [sessionId]: false,
      }
    }
  }

  async function selectSession(sessionId: number): Promise<void> {
    activeSessionId.value = sessionId
    sessionDetailLoading.value = true
    sessionDetailError.value = ''

    const [detail, messages] = await Promise.allSettled([
      fetchChatSession(sessionId),
      loadMessages(sessionId),
    ])

    if (detail.status === 'fulfilled') {
      const current = sessions.value.find((item) => item.id === sessionId)
      updateSessionInList({
        ...(current ?? detail.value),
        ...detail.value,
        context: mergeChatContexts(
          detail.value.context,
          current?.context ?? {},
        ),
      })
    } else {
      sessionDetailError.value = getErrorMessage(detail.reason)
    }

    if (messages.status === 'rejected') {
      sessionDetailError.value = getErrorMessage(messages.reason)
    }

    sessionDetailLoading.value = false
  }

  function startNewSession(): void {
    activeSessionId.value = null
    sessionDetailError.value = ''
  }

  async function createSession(
    context: ChatContext,
    title = '新会话',
  ): Promise<ChatSession | null> {
    creatingSession.value = true
    sessionsError.value = ''

    try {
      const session = await createChatSession({
        title,
        context,
      })
      updateSessionInList(session)
      activeSessionId.value = session.id
      setMessages(session.id, [])
      nextBeforeSequenceBySession.value = {
        ...nextBeforeSequenceBySession.value,
        [session.id]: null,
      }
      sessionTotal.value += 1
      return session
    } catch (error) {
      sessionsError.value = getErrorMessage(error)
      return null
    } finally {
      creatingSession.value = false
    }
  }

  async function renameSession(
    sessionId: number,
    title: string,
  ): Promise<boolean> {
    const normalized = title.trim()
    if (!normalized) {
      return false
    }

    try {
      const result = await renameChatSession(sessionId, { title: normalized })
      const current = sessions.value.find((item) => item.id === sessionId)
      const nextSession: ChatSession = {
        ...(current ?? {
          id: sessionId,
          context: {},
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
        ...(result ?? {}),
        title: result?.title || normalized,
        context: mergeChatContexts(
          result?.context ?? {},
          current?.context ?? {},
        ),
        updated_at: result?.updated_at || new Date().toISOString(),
      }
      updateSessionInList(nextSession)
      return true
    } catch (error) {
      sessionsError.value = getErrorMessage(error)
      return false
    }
  }

  async function updateContext(
    sessionId: number,
    context: ChatContext,
  ): Promise<void> {
    const current = sessions.value.find((item) => item.id === sessionId)
    if (!current) {
      return
    }

    const previousContext = current.context
    updateSessionInList({
      ...current,
      context,
      updated_at: new Date().toISOString(),
    })

    try {
      const result = await updateChatSessionContext(sessionId, context)
      updateSessionInList({
        ...current,
        ...(result ?? {}),
        context: mergeChatContexts(result?.context ?? {}, context),
        updated_at: result?.updated_at || new Date().toISOString(),
      })
    } catch (error) {
      sessionsError.value = getErrorMessage(error)
      updateSessionInList({
        ...current,
        context: previousContext,
      })
    }
  }

  async function removeSession(sessionId: number): Promise<void> {
    streamControllers.get(sessionId)?.abort()
    await deleteChatSession(sessionId)
    const index = sessions.value.findIndex((item) => item.id === sessionId)
    sessions.value = sessions.value.filter((item) => item.id !== sessionId)
    sessionTotal.value = Math.max(0, sessionTotal.value - 1)

    const nextMessages = { ...messagesBySession.value }
    delete nextMessages[sessionId]
    messagesBySession.value = nextMessages

    const nextBeforeSequences = { ...nextBeforeSequenceBySession.value }
    delete nextBeforeSequences[sessionId]
    nextBeforeSequenceBySession.value = nextBeforeSequences

    if (activeSessionId.value !== sessionId) {
      return
    }

    const nextSession =
      sessions.value[index] ?? sessions.value[index - 1] ?? null
    if (nextSession) {
      await selectSession(nextSession.id)
    } else {
      startNewSession()
    }
  }

  function getNextSequence(sessionId: number): number {
    const current = getMessages(sessionId)
    return current.reduce(
      (max, message) => Math.max(max, message.sequence),
      0,
    ) + 1
  }

  function handleStreamEvent(
    sessionId: number,
    requestId: string,
    event: ChatStreamEvent,
  ): void {
    const data = parseChatSseData(event)

    if (event.event === 'meta') {
      const assistantId =
        readString(data, ['assistant_id', 'assistant_message_id']) ?? null
      const serverMessageId = readNumber(data, ['message_id'])
      const sequence = readNumber(data, [
        'sequence_no',
        'sequence',
        'message_sequence',
      ])

      patchAssistant(sessionId, requestId, (message) => ({
        ...message,
        id: serverMessageId ?? message.id,
        assistant_id: assistantId ?? message.assistant_id,
        sequence: sequence ?? message.sequence,
        status: 'STREAMING',
      }))
      return
    }

    if (event.event === 'progress') {
      const progressRecord = readRecord(data, ['progress']) ?? data
      const progress: ChatProgress = {
        stage: readString(progressRecord, ['stage', 'phase']),
        message: readString(progressRecord, ['message', 'text', 'status']),
        percent: readNumber(progressRecord, ['percent', 'progress']) ?? null,
      }
      progressBySession.value = {
        ...progressBySession.value,
        [sessionId]: progress,
      }
      return
    }

    if (event.event === 'citation') {
      if (Array.isArray(data.citations)) {
        const citations = normalizeCitations(data.citations)
        if (citations.length) {
          patchAssistant(sessionId, requestId, (message) => ({
            ...message,
            citations: mergeChatCitations(message.citations, citations),
          }))
        }
        return
      }

      const citationValue = data.citation ?? data
      const citation = normalizeCitation(citationValue)
      if (!citation) {
        return
      }

      patchAssistant(sessionId, requestId, (message) => ({
        ...message,
        citations: mergeChatCitations(message.citations, [citation]),
      }))
      return
    }

    if (event.event === 'delta') {
      const nestedDelta = readRecord(data, ['delta'])
      const delta =
        readString(data, ['content', 'text']) ??
        readString(nestedDelta ?? {}, ['content', 'text']) ??
        (typeof data.delta === 'string' ? data.delta : '')

      patchAssistant(sessionId, requestId, (message) => ({
        ...message,
        content: `${message.content}${delta}`,
        status: 'STREAMING',
      }))
      return
    }

    if (event.event === 'done') {
      const finalContent = readString(data, ['content', 'answer', 'text'])
      const assistantId = readString(data, [
        'assistant_id',
        'assistant_message_id',
      ])
      const messageId = readNumber(data, ['message_id'])
      const sequence = readNumber(data, [
        'sequence_no',
        'sequence',
        'message_sequence',
      ])
      const citations = normalizeCitations(data.citations)
      const status = resolveDoneMessageStatus(data)

      patchAssistant(sessionId, requestId, (message) => ({
        ...message,
        id: messageId ?? message.id,
        assistant_id: assistantId ?? message.assistant_id,
        sequence: sequence ?? message.sequence,
        content:
          finalContent && finalContent.length >= message.content.length
            ? finalContent
            : message.content,
        status,
        citations: citations.length
          ? mergeChatCitations(message.citations, citations)
          : message.citations,
        degraded: typeof data.degraded === 'boolean' ? data.degraded : message.degraded,
        error_message: null,
      }))
      progressBySession.value = {
        ...progressBySession.value,
        [sessionId]: null,
      }
      return
    }

    if (event.event === 'error') {
      const errorMessage =
        readString(data, ['message', 'detail', 'error']) || '回答生成失败'
      patchAssistant(sessionId, requestId, (message) => ({
        ...message,
        status: 'FAILED',
        error_message: errorMessage,
      }))
      progressBySession.value = {
        ...progressBySession.value,
        [sessionId]: null,
      }
    }
  }

  async function runAssistantStream(options: {
    sessionId: number
    requestId: string
    context: ChatContext
    content: string
    assistantId?: string | null
  }): Promise<void> {
    const { sessionId, requestId, context, content, assistantId } = options
    const controller = new AbortController()
    streamControllers.set(sessionId, controller)
    setSending(sessionId, true)
    progressBySession.value = {
      ...progressBySession.value,
      [sessionId]: null,
    }

    const handlers: ChatStreamHandlers = {
      onEvent: (event) => {
        handleStreamEvent(sessionId, requestId, event)
      },
    }

    try {
      if (assistantId) {
        await retryChatAssistant(
          assistantId,
          requestId,
          handlers,
          controller.signal,
        )
      } else {
        const payload: ChatMessagePayload = {
          content,
          stream: true,
          context,
        }
        await streamChatMessage(
          sessionId,
          payload,
          requestId,
          handlers,
          controller.signal,
        )
      }
    } catch (error) {
      if (isAbortError(error) || controller.signal.aborted) {
        patchAssistant(sessionId, requestId, (message) => ({
          ...message,
          status: 'STOPPED',
        }))
      } else {
        patchAssistant(sessionId, requestId, (message) => ({
          ...message,
          status: 'FAILED',
          error_message: getErrorMessage(error),
        }))
      }
    } finally {
      streamControllers.delete(sessionId)
      setSending(sessionId, false)
      progressBySession.value = {
        ...progressBySession.value,
        [sessionId]: null,
      }
    }
  }

  async function maybeGenerateTitle(
    session: ChatSession,
    content: string,
  ): Promise<void> {
    const defaultTitles = new Set(['', '新会话'])
    if (!defaultTitles.has(session.title.trim())) {
      return
    }

    const title = content.replace(/\s+/g, ' ').trim().slice(0, 26)
    if (!title) {
      return
    }

    const current = sessions.value.find((item) => item.id === session.id)
    if (current) {
      updateSessionInList({
        ...current,
        title,
        updated_at: new Date().toISOString(),
      })
    }

    try {
      const result = await renameChatSession(session.id, { title })
      if (result) {
        updateSessionInList(result)
      }
    } catch {
      // 本地标题已更新，重命名失败不阻塞当前回答。
    }
  }

  async function sendMessage(
    content: string,
    context: ChatContext,
  ): Promise<void> {
    const normalized = content.trim()
    if (!normalized || creatingSession.value) {
      return
    }

    let session = activeSession.value

    if (!session) {
      const title = normalized.length > 26 ? `${normalized.slice(0, 26)}...` : normalized
      session = await createSession(context, title)
      if (!session) {
        return
      }
    }

    if (isSessionSending(session.id)) {
      return
    }

    void maybeGenerateTitle(session, normalized)

    const requestId = createChatRequestId()
    const createdAt = new Date().toISOString()
    const userSequence = getNextSequence(session.id)
    const userMessage: ChatMessage = {
      id: `local-user-${requestId}`,
      session_id: session.id,
      role: 'USER',
      content: normalized,
      sequence: userSequence,
      status: 'COMPLETED',
      citations: [],
      created_at: createdAt,
      request_id: requestId,
      client_id: requestId,
    }
    const assistantMessage: ChatMessage = {
      id: `local-assistant-${requestId}`,
      session_id: session.id,
      role: 'ASSISTANT',
      content: '',
      sequence: userSequence + 1,
      status: 'PENDING',
      citations: [],
      created_at: new Date(Date.now() + 1).toISOString(),
      request_id: requestId,
      client_id: requestId,
    }

    setMessages(
      session.id,
      upsertChatMessages(getMessages(session.id), [
        userMessage,
        assistantMessage,
      ]),
    )

    await runAssistantStream({
      sessionId: session.id,
      requestId,
      context,
      content: normalized,
    })
  }

  async function stopSession(sessionId: number): Promise<void> {
    const assistant = [...getMessages(sessionId)]
      .reverse()
      .find(
        (message) =>
          message.role === 'ASSISTANT' &&
          (message.status === 'PENDING' || message.status === 'STREAMING'),
      )

    streamControllers.get(sessionId)?.abort()

    if (assistant) {
      updateMessageById(sessionId, assistant.id, (message) => ({
        ...message,
        status: 'STOPPED',
      }))
    }

    if (assistant?.assistant_id) {
      try {
        await stopChatAssistant(assistant.assistant_id)
      } catch {
        // 本地流已停止，服务端停止失败不覆盖当前消息状态。
      }
    }
  }

  async function retryMessage(
    sessionId: number,
    messageId: ChatMessageId,
  ): Promise<void> {
    if (isSessionSending(sessionId)) {
      return
    }

    const messages = getMessages(sessionId)
    const assistant = messages.find(
      (message) => message.id === messageId && message.role === 'ASSISTANT',
    )
    if (!assistant) {
      return
    }

    const previousRequestId = assistant.request_id
    const previousClientId = assistant.client_id
    const requestId = createChatRequestId()
    const retryAssistantId = assistant.assistant_id ?? String(assistant.id)
    const assistantIndex = messages.findIndex(
      (message) => message.id === messageId,
    )
    const linkedUserMessage = messages.find(
      (message) =>
        message.role === 'USER' &&
        ((previousRequestId && message.request_id === previousRequestId) ||
          (previousClientId && message.client_id === previousClientId)),
    )
    const userMessage =
      linkedUserMessage ??
      messages
        .slice(0, assistantIndex)
        .reverse()
        .find((message) => message.role === 'USER')
    const content = userMessage?.content ?? ''
    const context =
      activeSession.value?.context ??
      sessions.value.find((item) => item.id === sessionId)?.context ??
      {}

    updateMessageById(sessionId, messageId, (message) => ({
      ...message,
      content: '',
      citations: [],
      error_message: null,
      request_id: requestId,
      client_id: requestId,
      status: 'PENDING',
    }))

    await runAssistantStream({
      sessionId,
      requestId,
      context,
      content,
      assistantId: retryAssistantId,
    })
  }

  return {
    sessions,
    sessionsLoading,
    sessionsLoadingMore,
    sessionsError,
    sessionTotal,
    sessionKeyword,
    creatingSession,
    activeSessionId,
    activeSession,
    sessionDetailLoading,
    sessionDetailError,
    messagesBySession,
    activeMessages,
    activeMessageLoading,
    activeMessageError,
    activeHasMore,
    activeProgress,
    activeSending,
    isSessionSending,
    loadSessions,
    loadMoreSessions,
    selectSession,
    startNewSession,
    createSession,
    renameSession,
    updateContext,
    removeSession,
    loadMessages,
    sendMessage,
    stopSession,
    retryMessage,
  }
})
