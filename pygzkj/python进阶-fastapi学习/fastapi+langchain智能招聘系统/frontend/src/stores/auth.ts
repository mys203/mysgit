import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  fetchCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from '@/api/auth'
import type { LoginPayload, User } from '@/types/auth'
import {
  clearAuthTokens,
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
} from '@/utils/token'
import { USER_KEY, readJson, removeStoredItem, writeJson } from '@/utils/storage'
import { isAdminRole } from '@/constants/permissions'
import { useTagsViewStore } from '@/stores/tagsView'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(readJson<User | null>(USER_KEY, null))
  const initialized = ref(false)

  const isAuthenticated = computed(() => Boolean(getAccessToken()))
  const displayName = computed(() => user.value?.real_name || user.value?.username || '用户')
  const isAdmin = computed(() => isAdminRole(user.value?.roles))

  function canAccess(permission?: string): boolean {
    if (!permission || isAdmin.value) {
      return true
    }

    return user.value?.permissions.includes(permission) === true
  }

  async function login(payload: LoginPayload): Promise<void> {
    useTagsViewStore().removeAllTabs()
    const result = await loginRequest(payload)
    setAccessToken(result.access_token)
    setRefreshToken(result.refresh_token)
    await fetchMe()
  }

  async function fetchMe(): Promise<User> {
    const currentUser = await fetchCurrentUser()
    user.value = currentUser
    writeJson(USER_KEY, currentUser)
    return currentUser
  }

  async function initialize(): Promise<void> {
    if (initialized.value) {
      return
    }

    if (getAccessToken() && !user.value) {
      await fetchMe()
    }

    initialized.value = true
  }

  async function logout(): Promise<void> {
    try {
      await logoutRequest(getRefreshToken())
    } finally {
      clearSession()
    }
  }

  function clearSession(): void {
    clearAuthTokens()
    removeStoredItem(USER_KEY)
    useTagsViewStore().removeAllTabs()
    user.value = null
    initialized.value = true
  }

  return {
    user,
    initialized,
    isAuthenticated,
    displayName,
    isAdmin,
    canAccess,
    login,
    fetchMe,
    initialize,
    logout,
    clearSession,
  }
})
