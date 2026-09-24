export type ResumeStatus = 'UPLOADED' | 'PARSING' | 'PARSED' | 'CONFIRMED' | 'FAILED'
export type ParseRecordStatus = 'PENDING' | 'PARSED' | 'CONFIRMED' | 'FAILED'

export interface Resume {
  id: number
  candidate_id: number | null
  filename: string
  file_hash: string
  file_type: string
  file_size: number
  status: ResumeStatus
  uploaded_by: number | null
  created_at: string
  updated_at: string
  duplicated?: boolean
}

export interface ResumeDetail extends Resume {
  raw_text: string | null
}

export interface ResumeQuery {
  page: number
  page_size: number
}

export interface ResumeParsedData {
  name: string | null
  email: string | null
  phone: string | null
  gender: string | null
  education: string | null
  work_years: number | null
  current_company: string | null
  current_title: string | null
  skills: string[]
  summary: string | null
  confidence: number
}

export interface ResumeParseRecord {
  id: number
  resume_id: number
  task_id: number | null
  status: ParseRecordStatus
  parsed_data: Partial<ResumeParsedData>
  confidence: number
  confirmed_by: number | null
  confirmed_at: string | null
  created_at: string
  updated_at: string
}

export interface ParseRecordQuery {
  page: number
  page_size: number
}

export interface ParseResultResponse {
  parse_record: ResumeParseRecord
  task_no: string
  degraded: boolean
  status: 'PENDING'
}

export interface ResumeParseTaskOutput extends Record<string, unknown> {
  parsed_data: Partial<ResumeParsedData>
  prompt_safety?: unknown
}

export interface CandidateOverride {
  name?: string | null
  email?: string | null
  phone?: string | null
  education?: string | null
  work_years?: number | null
  current_company?: string | null
  current_title?: string | null
  skills?: string[] | null
  summary?: string | null
}

export interface ParseConfirmPayload {
  candidate_id?: number | null
  job_position_id?: number | null
  candidate_override?: CandidateOverride | null
}

export interface ParseConfirmResponse {
  resume_id: number
  parse_record_id: number
  candidate_id: number
  application_id: number | null
  status: string
}
