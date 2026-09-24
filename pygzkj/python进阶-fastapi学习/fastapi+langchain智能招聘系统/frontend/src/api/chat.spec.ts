import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  buildChatStreamHeaders,
  retryChatAssistant,
} from '@/api/chat'

describe('chat API', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('为流式请求生成稳定的 Idempotency-Key', () => {
    expect(buildChatStreamHeaders('request-123')).toMatchObject({
      'Idempotency-Key': 'request-123',
      'X-Request-ID': 'request-123',
    })
  })

  it('retry 发送 stream:true，并复用同一 requestId', async () => {
    vi.stubGlobal('localStorage', {
      getItem: () => 'access-token',
      setItem: () => undefined,
      removeItem: () => undefined,
    })

    const fetchMock = vi.fn<typeof fetch>(async () =>
      new Response(
        'event: done\ndata: {"status":"completed"}\n\n',
        {
          status: 200,
          headers: {
            'Content-Type': 'text/event-stream',
          },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const events: string[] = []
    await retryChatAssistant('assistant-1', 'retry-request-1', {
      onEvent: (event) => {
        events.push(event.event)
      },
    })

    expect(events).toEqual(['done'])
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0] ?? []
    const headers = new Headers(init?.headers)

    expect(String(url)).toContain('/ai/chat/messages/assistant-1/retry')
    expect(headers.get('Idempotency-Key')).toBe('retry-request-1')
    expect(headers.get('X-Request-ID')).toBe('retry-request-1')
    expect(headers.get('Authorization')).toBe('Bearer access-token')
    expect(JSON.parse(String(init?.body))).toEqual({ stream: true })
  })
})
