import axios, {
  AxiosHeaders,
  type AxiosError,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { useLoadingStore } from '@/stores/loading'
import type { ApiResponse } from '@/types/common'
import type { TokenPair } from '@/types/auth'
import { getAccessToken, getRefreshToken, setAccessToken, setRefreshToken, clearAuthTokens } from '@/utils/token'
import { TAGS_VIEW_KEY, USER_KEY } from '@/utils/storage'
import { notifyError } from '@/utils/notify'

interface RetryRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
  silentError?: boolean
}

export interface AppRequestConfig extends AxiosRequestConfig {
  silentError?: boolean
}

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const successCodes = new Set([0, 200])

export class ApiBusinessError extends Error {
  readonly code: number
  readonly requestId?: string | null

  constructor(message: string, code: number, requestId?: string | null) {
    super(message)
    this.name = 'ApiBusinessError'
    this.code = code
    this.requestId = requestId
  }
}

export class AuthenticationExpiredError extends Error {
  constructor(message = '登录状态已失效') {
    super(message)
    this.name = 'AuthenticationExpiredError'
  }
}

const service = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const refreshClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

let refreshPromise: Promise<string> | null = null

function createRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function redirectToLogin(): void {
  if (window.location.pathname === '/login') {
    return
  }

  const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`)
  window.location.replace(`/login?redirect=${redirect}`)
}

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new AuthenticationExpiredError()
  }

  let response: AxiosResponse<ApiResponse<TokenPair>>
  try {
    response = await refreshClient.post<ApiResponse<TokenPair>>('/auth/refresh', {
      refresh_token: refreshToken,
    })
  } catch (error) {
    const status = axios.isAxiosError(error) ? error.response?.status : undefined
    if (status === 400 || status === 401 || status === 403) {
      throw new AuthenticationExpiredError()
    }
    throw error
  }
  const payload = response.data

  if (!successCodes.has(payload.code) || !payload.data?.access_token) {
    throw new AuthenticationExpiredError(payload.message || '登录状态已失效')
  }

  setAccessToken(payload.data.access_token)
  if (payload.data.refresh_token) {
    setRefreshToken(payload.data.refresh_token)
  }

  return payload.data.access_token
}

function getRefreshedToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

export function getApiBaseUrl(): string {
  return baseURL
}

export function resolveApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path
  }

  const normalizedBase = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${normalizedBase}${normalizedPath}`
}

export function refreshAccessTokenWithQueue(): Promise<string> {
  return getRefreshedToken()
}

export function shouldExpireSessionAfterRefreshError(error: unknown): boolean {
  return (
    error instanceof AuthenticationExpiredError ||
    (axios.isAxiosError(error) && error.response?.status === 401)
  )
}

export function expireSession(): void {
  clearAuthTokens()
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(TAGS_VIEW_KEY)
  redirectToLogin()
}

service.interceptors.request.use((config) => {
  const loadingStore = useLoadingStore()
  loadingStore.start()

  const headers = AxiosHeaders.from(config.headers)
  headers.set('X-Request-ID', createRequestId())

  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  config.headers = headers
  return config
})

service.interceptors.response.use(
  (response) => {
    const loadingStore = useLoadingStore()
    loadingStore.finish()
    return response
  },
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const loadingStore = useLoadingStore()
    loadingStore.finish()

    const originalConfig = error.config as RetryRequestConfig | undefined
    const status = error.response?.status
    const requestUrl = originalConfig?.url ?? ''
    const isAuthRequest =
      requestUrl.includes('/auth/login') ||
      requestUrl.includes('/auth/refresh') ||
      requestUrl.includes('/auth/logout')

    if (status === 401 && originalConfig && !originalConfig._retry && !isAuthRequest) {
      originalConfig._retry = true

      try {
        const token = await getRefreshedToken()
        const headers = AxiosHeaders.from(originalConfig.headers)
        headers.set('Authorization', `Bearer ${token}`)
        originalConfig.headers = headers
        return await service.request(originalConfig)
      } catch (refreshError) {
        if (shouldExpireSessionAfterRefreshError(refreshError)) {
          expireSession()
        }
        return Promise.reject(error)
      }
    }

    if (!axios.isCancel(error) && !originalConfig?.silentError) {
      const message = error.response?.data?.message || error.message || '网络请求失败'
      notifyError(message)
    }

    return Promise.reject(error)
  },
)

export async function request<T>(config: AppRequestConfig): Promise<T> {
  const response = await service.request<ApiResponse<T>>(config)
  const payload = response.data

  if (!successCodes.has(payload.code)) {
    const message = payload.message || '请求处理失败'
    notifyError(message)
    throw new ApiBusinessError(message, payload.code, payload.request_id)
  }

  return payload.data
}
