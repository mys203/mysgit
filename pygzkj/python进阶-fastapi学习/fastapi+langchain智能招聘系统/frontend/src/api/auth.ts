import { request } from '@/api/http'
import type { LoginPayload, LoginResult, User } from '@/types/auth'

export function login(payload: LoginPayload): Promise<LoginResult> {
  return request<LoginResult>({
    url: '/auth/login',
    method: 'POST',
    data: payload,
  })
}

export function fetchCurrentUser(): Promise<User> {
  return request<User>({
    url: '/auth/me',
    method: 'GET',
  })
}

export function logout(refreshToken: string): Promise<void> {
  return request<void>({
    url: '/auth/logout',
    method: 'POST',
    data: {
      refresh_token: refreshToken,
    },
  })
}
