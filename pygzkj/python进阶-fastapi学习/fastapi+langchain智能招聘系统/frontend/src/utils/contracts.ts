import type { AiTaskStatus } from '@/types/common'
import type { CandidateGender } from '@/types/candidate'
import type { InterviewPayload, InterviewUpdatePayload } from '@/types/ai'

export function compactParams<T extends object>(params: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => {
      if (value === undefined || value === null || value === '') {
        return false
      }

      return !(Array.isArray(value) && value.length === 0)
    }),
  ) as Partial<T>
}

export function isTerminalTaskStatus(status: AiTaskStatus): boolean {
  return status === 'SUCCEEDED' || status === 'FAILED'
}

export function buildInterviewUpdatePayload(
  payload: Partial<InterviewPayload>,
): InterviewUpdatePayload {
  return {
    interviewer_id: payload.interviewer_id,
    title: payload.title,
    round_no: payload.round_no,
    mode: payload.mode,
    scheduled_at: payload.scheduled_at,
    duration_minutes: payload.duration_minutes,
    location: payload.location,
    meeting_url: payload.meeting_url,
  }
}

export function normalizeCandidateGender(
  value?: string | null,
): CandidateGender | undefined {
  if (!value) {
    return undefined
  }

  const normalized = value.toUpperCase()
  if (
    normalized === 'MALE' ||
    normalized === 'FEMALE' ||
    normalized === 'OTHER' ||
    normalized === 'UNKNOWN'
  ) {
    return normalized
  }

  return 'UNKNOWN'
}

export function parsePositiveId(value: unknown): number | null {
  if (typeof value === 'number' && Number.isInteger(value) && value > 0) {
    return value
  }

  if (typeof value === 'string' && /^\d+$/.test(value)) {
    const parsed = Number(value)
    return parsed > 0 ? parsed : null
  }

  return null
}
