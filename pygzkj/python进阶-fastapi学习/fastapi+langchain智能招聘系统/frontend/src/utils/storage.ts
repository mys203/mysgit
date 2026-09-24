export const ACCESS_TOKEN_KEY = 'smart_recruitment_access_token'
export const REFRESH_TOKEN_KEY = 'smart_recruitment_refresh_token'
export const USER_KEY = 'smart_recruitment_user'
export const TAGS_VIEW_KEY = 'smart_recruitment_tags_view'
export const SIDEBAR_COLLAPSED_KEY = 'smart_recruitment_sidebar_collapsed'

export function readJson<T>(key: string, fallback: T): T {
  const raw = localStorage.getItem(key)
  if (!raw) {
    return fallback
  }

  try {
    return JSON.parse(raw) as T
  } catch {
    localStorage.removeItem(key)
    return fallback
  }
}

export function writeJson<T>(key: string, value: T): void {
  localStorage.setItem(key, JSON.stringify(value))
}

export function removeStoredItem(key: string): void {
  localStorage.removeItem(key)
}
