import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import * as chatApi from '@/api/chat'
import { useChatStore } from '@/stores/chat'
import type { ChatMessage, ChatSession } from '@/types/chat'

vi.mock('@/api/chat', () => ({
  createChatSession: vi.fn(),
  deleteChatSession: vi.fn(),
  fetchChatMessages: vi.fn(),
  fetchChatSession: vi.fn(),
  fetchChatSessions: vi.fn(),
  renameChatSession: vi.fn(),
  retryChatAssistant: vi.fn(),
  stopChatAssistant: vi.fn(),
  streamChatMessage: vi.fn(),
  updateChatSessionContext: vi.fn(),
}))

describe('chat store retry', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('历史 FAILED 助手消息缺少 assistant_id 时使用本地 id 重试', async () => {
    const store = useChatStore()
    const session: ChatSession = {
      id: 7,
      title: '历史会话',
      context: {
        job_id: 11,
      },
      created_at: '2026-09-20T10:00:00.000Z',
      updated_at: '2026-09-20T10:00:00.000Z',
    }
    const userMessage: ChatMessage = {
      id: 500,
      session_id: 7,
      role: 'USER',
      content: '请分析这位候选人',
      sequence: 10,
      status: 'COMPLETED',
      citations: [],
      created_at: '2026-09-20T10:00:00.000Z',
    }
    const assistantMessage: ChatMessage = {
      id: 501,
      session_id: 7,
      role: 'ASSISTANT',
      content: '',
      sequence: 11,
      status: 'FAILED',
      citations: [],
      created_at: '2026-09-20T10:00:01.000Z',
      assistant_id: null,
      error_message: '回答生成失败',
    }

    store.sessions = [session]
    store.activeSessionId = session.id
    store.messagesBySession = {
      [session.id]: [userMessage, assistantMessage],
    }

    let boundRequestId = ''
    vi.mocked(chatApi.retryChatAssistant).mockImplementation(
      async (assistantId, requestId, handlers) => {
        boundRequestId = requestId
        const localAssistant = store.messagesBySession[session.id].find(
          (message) => message.id === assistantMessage.id,
        )

        expect(assistantId).toBe('501')
        expect(localAssistant?.request_id).toBe(requestId)
        expect(localAssistant?.status).toBe('PENDING')
        handlers.onEvent({
          event: 'done',
          data: JSON.stringify({ status: 'completed' }),
        })

        return {
          completed: true,
        }
      },
    )

    await store.retryMessage(session.id, assistantMessage.id)

    expect(chatApi.retryChatAssistant).toHaveBeenCalledTimes(1)
    expect(chatApi.streamChatMessage).not.toHaveBeenCalled()
    expect(chatApi.createChatSession).not.toHaveBeenCalled()

    const messages = store.messagesBySession[session.id]
    expect(messages.filter((message) => message.role === 'USER')).toHaveLength(1)
    expect(messages).toHaveLength(2)
    expect(messages[1].request_id).toBe(boundRequestId)
    expect(messages[1].status).toBe('COMPLETED')
  })
})
