export interface MatchQuery {
  job_id: number
  candidate_ids?: number[]
  top_k: number
  force_refresh?: boolean
}

export interface MatchResult {
  id: number
  job_id: number
  candidate_id: number
  application_id: number | null
  score: number
  rule_score: number
  vector_score: number | null
  llm_score: number | null
  level: string
  reasons: string[]
  detail: Record<string, unknown>
  algorithm_version: string
  prompt_version: string
  degraded: boolean
  created_at: string
}

export interface MatchResponse {
  task_no: string
  algorithm_version: string
  prompt_version: string
  degraded: boolean
  items: MatchResult[]
}

export interface GeneratedInterviewQuestion {
  question: string
  category: string
  reference_answer: string | null
  score_weight: number
}

export interface InterviewQuestionTaskOutput extends Record<string, unknown> {
  task_no: string
  degraded: boolean
  prompt_safety?: unknown
  questions: GeneratedInterviewQuestion[]
}

export type QuestionStatus = 'DRAFT' | 'APPROVED' | 'REJECTED'

export interface InterviewQuestionPayload {
  job_id: number
  candidate_id?: number | null
  interview_id?: number | null
  count: number
  categories: string[]
}

export interface InterviewQuestion {
  id: number
  interview_id: number | null
  job_id: number
  candidate_id: number | null
  question: string
  category: string
  reference_answer: string | null
  score_weight: number
  status: QuestionStatus
  generated_by: string
  approved_by: number | null
  approved_at: string | null
  created_at: string
  updated_at: string
}

export interface InterviewQuestionQuery {
  interview_id?: number
  category?: string
  status?: QuestionStatus | ''
  page: number
  page_size: number
}

export interface InterviewQuestionUpdate {
  question?: string
  category?: string
  reference_answer?: string
  score_weight?: number
  status?: QuestionStatus
}

export type InterviewStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
export type InterviewMode = 'OFFLINE' | 'VIDEO' | 'PHONE'

export interface Interview {
  id: number
  job_id: number
  candidate_id: number
  application_id: number | null
  interviewer_id: number | null
  title: string
  round_no: number
  mode: InterviewMode
  scheduled_at: string
  duration_minutes: number
  location: string | null
  meeting_url: string | null
  status: InterviewStatus
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface InterviewPayload {
  job_id: number
  candidate_id: number
  application_id?: number | null
  interviewer_id?: number | null
  title: string
  round_no: number
  mode: InterviewMode
  scheduled_at: string
  duration_minutes: number
  location?: string | null
  meeting_url?: string | null
}

export interface InterviewUpdatePayload {
  interviewer_id?: number | null
  title?: string
  round_no?: number
  mode?: InterviewMode
  scheduled_at?: string
  duration_minutes?: number
  location?: string | null
  meeting_url?: string | null
  status?: InterviewStatus
}

export interface InterviewParticipant {
  id: number
  interview_id: number
  user_id: number
  participant_role: string
  feedback: string | null
  score?: number
  status: string
  created_at: string
  updated_at: string
}

export interface InterviewFeedbackPayload {
  feedback: string
  score?: number
  status: 'INVITED' | 'CONFIRMED' | 'COMPLETED' | 'DECLINED'
}
