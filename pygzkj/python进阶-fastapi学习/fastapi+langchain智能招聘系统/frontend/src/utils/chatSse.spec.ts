import { describe, expect, it } from 'vitest'
import { ChatSseParser } from '@/utils/chatSse'

describe('ChatSseParser', () => {
  it('解析跨 chunk 的 SSE 事件', () => {
    const parser = new ChatSseParser()

    expect(parser.push('event: meta\ndata: {"assistant_')).toEqual([])
    expect(parser.push('id":"a-1"}\n\n')).toEqual([
      {
        event: 'meta',
        data: '{"assistant_id":"a-1"}',
        id: undefined,
        retry: undefined,
      },
    ])
  })

  it('支持 CRLF、注释和多行 data', () => {
    const parser = new ChatSseParser()
    const events = parser.push(
      ': keep-alive\r\nevent: delta\r\ndata: 第一行\r\ndata: 第二行\r\n\r\n',
    )

    expect(events).toEqual([
      {
        event: 'delta',
        data: '第一行\n第二行',
        id: undefined,
        retry: undefined,
      },
    ])
  })

  it('flush 返回没有空行结尾的最后一个事件', () => {
    const parser = new ChatSseParser()

    expect(parser.push('event: done\ndata: {}')).toEqual([])
    expect(parser.flush()).toEqual([
      {
        event: 'done',
        data: '{}',
        id: undefined,
        retry: undefined,
      },
    ])
    expect(parser.flush()).toEqual([])
  })
})
