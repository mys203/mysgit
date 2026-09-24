export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  request_id?: string | null
  timestamp?: string | null
}

export interface PageQuery {
  page: number
  page_size: number
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface SelectOption<TValue extends string | number = string> {
  label: string
  value: TValue
}

export type AiTaskStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED'

export interface AiTaskAccepted {
  task_no: string
  status: AiTaskStatus
}

export interface AiTask<TOutput extends object = Record<string, unknown>> {
  id: number
  task_no: string
  task_type: string
  status: AiTaskStatus
  provider: string
  model_name: string | null
  output_payload: TOutput | null
  error_message?: string | null
  error_code?: string | null
  error_detail?: unknown
  degraded: boolean
  started_at?: string | null
  finished_at?: string | null
  created_at: string
  updated_at: string
}
