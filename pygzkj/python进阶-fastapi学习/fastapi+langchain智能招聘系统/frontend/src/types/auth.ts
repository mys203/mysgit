export interface LoginPayload {
  username: string
  password: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export type LoginResult = TokenPair

export interface User {
  id: number
  username: string
  real_name: string
  email?: string | null
  phone?: string | null
  department_id?: number | null
  roles: string[]
  permissions: string[]
  status?: string
  last_login_at?: string | null
  created_at?: string
  updated_at?: string
}
