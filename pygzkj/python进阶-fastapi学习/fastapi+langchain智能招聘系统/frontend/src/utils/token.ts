import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  removeStoredItem,
} from '@/utils/storage'

export function getAccessToken(): string {
  return localStorage.getItem(ACCESS_TOKEN_KEY) ?? ''
}

export function getRefreshToken(): string {
  return localStorage.getItem(REFRESH_TOKEN_KEY) ?? ''
}

export function setAccessToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function setRefreshToken(token: string): void {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export function clearAuthTokens(): void {
  removeStoredItem(ACCESS_TOKEN_KEY)
  removeStoredItem(REFRESH_TOKEN_KEY)
}
