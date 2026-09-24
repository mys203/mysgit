import { request } from '@/api/http'
import type { PaginatedData, AiTask, AiTaskAccepted } from '@/types/common'
import type {
  Interview,
  InterviewFeedbackPayload,
  InterviewParticipant,
  InterviewPayload,
  InterviewQuestion,
  InterviewQuestionPayload,
  InterviewQuestionQuery,
  InterviewQuestionUpdate,
  InterviewUpdatePayload,
  MatchQuery,
  MatchResult,
} from '@/types/ai'
import { compactParams } from '@/utils/contracts'

export function createMatchTask(payload: MatchQuery): Promise<AiTaskAccepted> {
  return request<AiTaskAccepted>({
    url: '/ai/matches',
    method: 'POST',
    data: payload,
  })
}

export function fetchAiTask<TOutput extends object>(
  taskNo: string,
): Promise<AiTask<TOutput>> {
  return request<AiTask<TOutput>>({
    url: `/ai/tasks/${taskNo}`,
    method: 'GET',
  })
}

export function fetchMatchResult(id: number): Promise<MatchResult> {
  return request<MatchResult>({
    url: `/match-results/${id}`,
    method: 'GET',
  })
}

export function createInterviewQuestions(
  payload: InterviewQuestionPayload,
): Promise<AiTaskAccepted> {
  return request<AiTaskAccepted>({
    url: '/ai/interview-questions',
    method: 'POST',
    data: payload,
  })
}

export function fetchInterviewQuestions(
  query: InterviewQuestionQuery,
): Promise<PaginatedData<InterviewQuestion>> {
  if (query.interview_id) {
    return request<{ items: InterviewQuestion[] }>({
      url: `/interviews/${query.interview_id}/questions`,
      method: 'GET',
    }).then((result) => ({
      items: result.items,
      total: result.items.length,
      page: 1,
      page_size: result.items.length || query.page_size,
    }))
  }

  return request<PaginatedData<InterviewQuestion>>({
    url: '/interview-questions',
    method: 'GET',
    params: compactParams(query),
  })
}

export function updateInterviewQuestion(
  id: number,
  payload: InterviewQuestionUpdate,
): Promise<InterviewQuestion> {
  return request<InterviewQuestion>({
    url: `/interview-questions/${id}`,
    method: 'PATCH',
    data: payload,
  })
}

export function fetchInterviews(params: {
  status?: string
  page: number
  page_size: number
}): Promise<PaginatedData<Interview>> {
  return request<PaginatedData<Interview>>({
    url: '/interviews',
    method: 'GET',
    params: compactParams(params),
  })
}

export function createInterview(payload: InterviewPayload): Promise<Interview> {
  return request<Interview>({
    url: '/interviews',
    method: 'POST',
    data: payload,
  })
}

export function updateInterview(
  id: number,
  payload: InterviewUpdatePayload,
): Promise<Interview> {
  return request<Interview>({
    url: `/interviews/${id}`,
    method: 'PATCH',
    data: payload,
  })
}

export function cancelInterview(id: number, reason: string): Promise<Interview> {
  return request<Interview>({
    url: `/interviews/${id}/cancel`,
    method: 'POST',
    data: { reason },
  })
}

export function addInterviewParticipant(
  id: number,
  userId: number,
  participantRole: 'INTERVIEWER' | 'OBSERVER' | 'COORDINATOR' = 'INTERVIEWER',
): Promise<InterviewParticipant> {
  return request<InterviewParticipant>({
    url: `/interviews/${id}/participants`,
    method: 'POST',
    data: {
      user_id: userId,
      participant_role: participantRole,
    },
  })
}

export function submitInterviewFeedback(
  id: number,
  payload: InterviewFeedbackPayload,
): Promise<InterviewParticipant> {
  return request<InterviewParticipant>({
    url: `/interviews/${id}/feedback`,
    method: 'POST',
    data: payload,
  })
}
