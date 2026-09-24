import { describe, expect, it } from 'vitest'
import type { ChatMessage } from '@/types/chat'
import {
  buildChatSessionTitle,
  createChatRequestId,
  getCitationTypeLabel,
  getChatQuickPrompts,
  mergeChatCitations,
  mergeChatContexts,
  normalizeChatMessage,
  normalizeChatMessagePage,
  normalizeChatMessageStatus,
  normalizeChatSession,
  normalizeChatSessionPage,
  normalizeCitation,
  resolveDoneMessageStatus,
  resolveHistoryBeforeSequence,
  upsertChatMessages,
} from '@/utils/chatSessions'

function createMessage(
  overrides: Partial<ChatMessage> = {},
): ChatMessage {
  return {
    id: 'local-assistant-request-1',
    session_id: 9,
    role: 'ASSISTANT',
    content: '',
    sequence: 2,
    status: 'PENDING',
    citations: [],
    created_at: '2026-09-20T10:00:00.000Z',
    request_id: 'request-1',
    client_id: 'request-1',
    ...overrides,
  }
}

describe('chatSessions', () => {
  it('按 request_id 幂等合并流式消息，不产生重复消息', () => {
    const local = createMessage()
    const merged = upsertChatMessages([local], [
      createMessage({
        id: 101,
        assistant_id: 'assistant-101',
        status: 'STREAMING',
        content: '候选人',
        citations: [
          {
            id: 8,
            source_type: 'RESUME',
            title: '候选人简历',
            resume_id: 12,
          },
        ],
      }),
      createMessage({
        id: 101,
        assistant_id: 'assistant-101',
        status: 'COMPLETED',
        content: '候选人匹配度较高',
        citations: [
          {
            id: 8,
            source_type: 'RESUME',
            title: '候选人简历',
            resume_id: 12,
          },
        ],
      }),
    ])

    expect(merged).toHaveLength(1)
    expect(merged[0]).toMatchObject({
      id: 101,
      assistant_id: 'assistant-101',
      status: 'COMPLETED',
      content: '候选人匹配度较高',
    })
    expect(merged[0].citations).toHaveLength(1)
  })

  it('生成稳定的客户端请求标识', () => {
    const first = createChatRequestId()
    const second = createChatRequestId()

    expect(first).toBeTruthy()
    expect(second).toBeTruthy()
    expect(first).not.toBe(second)
  })

  it('兼容会话顶层上下文、嵌套 context 和 resume_id', () => {
    const topLevelSession = normalizeChatSession({
      id: 3,
      title: '候选人沟通',
      job_id: 11,
      candidate_id: 22,
      resume_id: 33,
      context: {
        job_id: 99,
      },
      created_at: '2026-09-20T10:00:00.000Z',
      updated_at: '2026-09-20T10:10:00.000Z',
    })
    const nestedSession = normalizeChatSession({
      id: 4,
      title: '岗位沟通',
      context: {
        job_id: 12,
        candidate_id: 23,
        resume_id: 34,
      },
      created_at: '2026-09-20T10:00:00.000Z',
      updated_at: '2026-09-20T10:10:00.000Z',
    })

    expect(topLevelSession?.context).toEqual({
      job_id: 11,
      candidate_id: 22,
      resume_id: 33,
    })
    expect(nestedSession?.context).toEqual({
      job_id: 12,
      candidate_id: 23,
      resume_id: 34,
    })
    expect(
      mergeChatContexts(
        {},
        {
          job_id: 11,
          candidate_id: 22,
          resume_id: 33,
        },
      ),
    ).toEqual({
      job_id: 11,
      candidate_id: 22,
      resume_id: 33,
    })
  })

  it('规范化会话分页并保留上下文', () => {
    const page = normalizeChatSessionPage({
      items: [
        {
          id: 3,
          title: '候选人沟通',
          context: {
            job_id: 11,
            candidate_id: 22,
          },
          created_at: '2026-09-20T10:00:00.000Z',
          updated_at: '2026-09-20T10:10:00.000Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    })

    expect(page.items[0]).toMatchObject({
      id: 3,
      title: '候选人沟通',
      context: {
        job_id: 11,
        candidate_id: 22,
      },
    })
  })

  it('读取 sequence_no，并优先使用后端历史游标', () => {
    const message = normalizeChatMessage(
      {
        id: 31,
        role: 'assistant',
        content: '历史回答',
        sequence_no: 37,
        status: 'completed',
      },
      9,
    )
    const page = normalizeChatMessagePage(
      {
        items: [
          {
            id: 30,
            role: 'assistant',
            content: '更早回答',
            sequence_no: 35,
            status: 'completed',
          },
        ],
        has_more: true,
        next_before_sequence: 21,
      },
      9,
    )

    expect(message?.sequence).toBe(37)
    expect(page.next_before_sequence).toBe(21)
    expect(resolveHistoryBeforeSequence(page.next_before_sequence, 35)).toBe(21)
    expect(resolveHistoryBeforeSequence(undefined, 35)).toBe(35)
  })

  it('字段缺失时不把消息序号重排为 1..N', () => {
    const page = normalizeChatMessagePage(
      {
        items: [
          { id: 9, role: 'assistant', content: '第二条' },
          { id: 8, role: 'assistant', content: '第一条' },
        ],
      },
      9,
    )

    expect(page.items.map((item) => item.sequence)).toEqual([0, 0])
    expect(page.items.map((item) => item.id)).toEqual([9, 8])
  })

  it('兼容 source_id、excerpt，并生成引用标签与去重', () => {
    const first = normalizeCitation({
      source_type: 'resume_snapshot',
      source_id: 88,
      excerpt: '候选人有五年后端经验',
    })
    const duplicate = normalizeCitation({
      source_type: 'RESUME',
      source_id: 88,
      title: '候选人简历',
    })

    expect(first).toMatchObject({
      reference_id: 88,
      snippet: '候选人有五年后端经验',
    })
    expect(first && getCitationTypeLabel(first)).toBe('简历')
    expect(
      first && duplicate
        ? mergeChatCitations([first], [duplicate])
        : [],
    ).toHaveLength(1)
  })

  it('done 状态按服务端值解析，未知状态不默认为完成', () => {
    expect(resolveDoneMessageStatus({ status: 'stopped' })).toBe('STOPPED')
    expect(resolveDoneMessageStatus({ status: 'cancelled' })).toBe('CANCELLED')
    expect(resolveDoneMessageStatus({ status: 'unknown_state' })).toBe('UNKNOWN')
    expect(normalizeChatMessageStatus('mystery')).toBe('UNKNOWN')
  })

  it('根据上下文生成标题与快捷问题', () => {
    expect(buildChatSessionTitle('  如何评估候选人匹配度？  ', 8)).toBe(
      '如何评估候选人匹...',
    )
    expect(getChatQuickPrompts({ job_id: 1, candidate_id: 2 })).toContain(
      '评估这位候选人与岗位的匹配情况',
    )
  })
})
