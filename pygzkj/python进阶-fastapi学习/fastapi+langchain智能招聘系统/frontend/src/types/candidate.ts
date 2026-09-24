export type CandidateGender = 'MALE' | 'FEMALE' | 'OTHER' | 'UNKNOWN'
export type CandidateStatus = 'ACTIVE' | 'INACTIVE' | 'BLACKLIST'
export type ApplicationStage =
  | 'APPLIED'
  | 'SCREENING'
  | 'INTERVIEW'
  | 'OFFER'
  | 'HIRED'
  | 'REJECTED'
  | 'WITHDRAWN'

export interface Candidate {
  id: number
  name: string
  email: string | null
  phone: string | null
  gender: CandidateGender | null
  birth_date: string | null
  education: string | null
  work_years: number | null
  current_company: string | null
  current_title: string | null
  skills: string[]
  summary: string | null
  source: string | null
  status: CandidateStatus
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface CandidatePayload {
  name: string
  email?: string | null
  phone?: string | null
  gender?: CandidateGender | null
  birth_date?: string | null
  education?: string | null
  work_years?: number | null
  current_company?: string | null
  current_title?: string | null
  skills: string[]
  summary?: string | null
  source?: string | null
  status: CandidateStatus
}

export interface CandidateQuery {
  search?: string
  status?: CandidateStatus | ''
  page: number
  page_size: number
}

export interface Application {
  id: number
  job_id: number
  candidate_id: number
  resume_id: number | null
  stage: ApplicationStage
  status: string
  source: string | null
  applied_at: string
  updated_by: number | null
  created_at: string
  updated_at: string
}

export interface ApplicationQuery {
  job_id?: number | null
  candidate_id?: number | null
  stage?: ApplicationStage | ''
  page: number
  page_size: number
}

export interface ApplicationStagePayload {
  stage: ApplicationStage
  reason?: string
}
