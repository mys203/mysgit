export type JobStatus = 'DRAFT' | 'PUBLISHED' | 'CLOSED'
export type EmploymentType = 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'INTERN'

export interface Job {
  id: number
  title: string
  code: string
  category_id: number | null
  department_id: number | null
  recruiter_id: number | null
  description: string
  requirements: string
  skills: string[]
  location: string | null
  employment_type: EmploymentType
  salary_min: number | null
  salary_max: number | null
  headcount: number
  status: JobStatus
  published_at: string | null
  closed_at: string | null
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface JobCreatePayload {
  title: string
  code: string
  category_id?: number | null
  department_id?: number | null
  recruiter_id?: number | null
  description: string
  requirements: string
  skills: string[]
  location?: string | null
  employment_type: EmploymentType
  salary_min?: number | null
  salary_max?: number | null
  headcount: number
}

export type JobUpdatePayload = Partial<Omit<JobCreatePayload, 'code'>>

export interface JobQuery {
  search?: string
  status?: JobStatus | ''
  category_id?: number | null
  department_id?: number | null
  page: number
  page_size: number
}

export interface JobCategory {
  id: number
  name: string
  code: string
  parent_id: number | null
  sort_order: number
  status: 'ACTIVE' | 'INACTIVE'
  created_at: string
  updated_at: string
}

export interface Department {
  id: number
  name: string
  code: string
  parent_id: number | null
  description: string | null
  status: 'ACTIVE' | 'INACTIVE'
  created_at: string
  updated_at: string
}

export interface DepartmentOption {
  id: number
  name: string
  code: string
  parent_id: number | null
}

export interface PaginationQuery {
  page: number
  page_size: number
}
