export interface ChatContext {
  job_id?: number | null
  candidate_id?: number | null
  resume_id?: number | null
}

export interface ChatSession {
  id: number
  title: string
  context: ChatContext
  created_at: string
  updated_at: string
  last_message_at?: string | null
  message_count?: number
}

export interface ChatSessionCreatePayload {
  title?: string
  context: ChatContext
}

export interface ChatSessionRenamePayload {
  title: string
}

export interface ChatSessionQuery {
  page: number
  page_size: number
  keyword?: string
}

export interface ChatSessionPage {
  items: ChatSession[]
  total: number
  page: number
  page_size: number
}

export type ChatMessageRole = 'USER' | 'ASSISTANT' | 'SYSTEM'
export type ChatMessageStatus =
  | 'PENDING'
  | 'STREAMING'
  | 'COMPLETED'
  | 'STOPPED'
  | 'CANCELLED'
  | 'FAILED'
  | 'UNKNOWN'

export type ChatMessageId = number | string

export interface ChatCitation {
  id?: ChatMessageId
  source_type?: string
  title: string
  snippet?: string | null
  reference_id?: number | null
  job_id?: number | null
  candidate_id?: number | null
  resume_id?: number | null
  match_result_id?: number | null
  interview_question_id?: number | null
  route?: string | null
}

export interface ChatProgress {
  stage?: string
  message?: string
  percent?: number | null
}

export interface ChatMessage {
  id: ChatMessageId
  session_id: number
  role: ChatMessageRole
  content: string
  sequence: number
  status: ChatMessageStatus
  citations: ChatCitation[]
  created_at: string
  updated_at?: string | null
  assistant_id?: string | null
  client_id?: string | null
  request_id?: string | null
  error_message?: string | null
  progress?: ChatProgress | null
  degraded?: boolean
}

export interface ChatMessagePage {
  items: ChatMessage[]
  total?: number
  page?: number
  page_size: number
  has_more?: boolean
  next_before_sequence?: number | null
}

export interface ChatMessagePayload {
  content: string
  stream: true
  context?: ChatContext
}

export interface ChatRetryPayload {
  stream: true
}

export interface ChatStreamEvent {
  event: string
  data: string
  id?: string
  retry?: number
}

export interface ChatSseMeta {
  assistant_id: string
  message_id?: ChatMessageId
  user_message_id?: ChatMessageId
  sequence?: number
}

export interface ChatSseDone {
  message_id?: ChatMessageId
  assistant_id?: string
  content?: string
  sequence?: number
  citations?: ChatCitation[]
  degraded?: boolean
  status?: ChatMessageStatus
}

export interface ChatStreamResult {
  completed: boolean
}
