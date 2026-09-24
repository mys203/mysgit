import { describe, expect, it } from 'vitest'
import {
  buildInterviewUpdatePayload,
  compactParams,
  isTerminalTaskStatus,
  normalizeCandidateGender,
  parsePositiveId,
} from '@/utils/contracts'

describe('前端契约工具', () => {
  it('去除查询参数中的空值', () => {
    expect(
      compactParams({
        search: '',
        status: 'PUBLISHED',
        department_id: null,
        page: 1,
      }),
    ).toEqual({
      status: 'PUBLISHED',
      page: 1,
    })
  })

  it('只接受后端 AI 终态', () => {
    expect(isTerminalTaskStatus('SUCCEEDED')).toBe(true)
    expect(isTerminalTaskStatus('FAILED')).toBe(true)
    expect(isTerminalTaskStatus('RUNNING')).toBe(false)
  })

  it('候选人性别统一映射为后端枚举', () => {
    expect(normalizeCandidateGender('male')).toBe('MALE')
    expect(normalizeCandidateGender('未知')).toBe('UNKNOWN')
    expect(normalizeCandidateGender()).toBeUndefined()
  })

  it('路由查询 ID 只解析正整数', () => {
    expect(parsePositiveId('12')).toBe(12)
    expect(parsePositiveId('0')).toBeNull()
    expect(parsePositiveId('abc')).toBeNull()
  })

  it('面试更新只保留 InterviewUpdate 允许字段', () => {
    const payload = buildInterviewUpdatePayload({
      job_id: 1,
      candidate_id: 2,
      application_id: 3,
      interviewer_id: 4,
      title: '后端二面',
      round_no: 2,
      mode: 'VIDEO',
      scheduled_at: '2026-10-01T02:00:00Z',
      duration_minutes: 60,
      location: null,
      meeting_url: 'https://example.com/interview',
    })

    expect(payload).toEqual({
      interviewer_id: 4,
      title: '后端二面',
      round_no: 2,
      mode: 'VIDEO',
      scheduled_at: '2026-10-01T02:00:00Z',
      duration_minutes: 60,
      location: null,
      meeting_url: 'https://example.com/interview',
    })
    expect(payload).not.toHaveProperty('job_id')
    expect(payload).not.toHaveProperty('candidate_id')
    expect(payload).not.toHaveProperty('application_id')
  })
})
