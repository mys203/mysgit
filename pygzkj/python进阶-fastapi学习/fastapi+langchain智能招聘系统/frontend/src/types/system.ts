import type { RoleCode } from '@/constants/permissions'

export type UserStatus = 'ACTIVE' | 'INACTIVE'

export interface Role {
  id: number
  name: string
  code: RoleCode
  description: string | null
  status: UserStatus
  created_at: string
  updated_at: string
}

export interface OperationLog {
  id: number
  user_id: number | null
  username: string | null
  method: string
  path: string
  action: string
  resource_type: string | null
  resource_id: string | null
  status_code: number
  ip: string | null
  user_agent: string | null
  request_id: string | null
  detail: Record<string, unknown>
  duration_ms: number | null
  created_at: string
}

export interface OperationLogQuery {
  user_id?: number
  action?: string
  resource_type?: string
  start_time?: string
  end_time?: string
  page: number
  page_size: number
}

export interface UserQuery {
  search?: string
  status?: UserStatus | ''
  page: number
  page_size: number
}

export interface UserOption {
  id: number
  username: string
  real_name: string
  department_id: number | null
  roles: RoleCode[]
}

export interface SystemUser {
  id: number
  username: string
  real_name: string
  email: string | null
  phone: string | null
  department_id: number | null
  status: UserStatus
  roles: RoleCode[]
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface UserCreatePayload {
  username: string
  password: string
  real_name: string
  email: string | null
  phone: string | null
  department_id: number | null
  role_codes: RoleCode[]
  status: UserStatus
}

export interface UserUpdatePayload {
  real_name?: string
  email?: string | null
  phone?: string | null
  department_id?: number | null
  role_codes?: RoleCode[]
  status?: UserStatus
  password?: string
}

export interface UserDeleteResult {
  id: number
  deleted: boolean
}

export interface DashboardSummary {
  jobs: Record<string, number>
  candidates: Record<string, number>
  applications: Record<string, number>
  interviews: Record<string, number>
  ai_tasks: Record<string, number>
  generated_at: string
}
