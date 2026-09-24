import { ref } from 'vue'
import { defineStore } from 'pinia'
import { SIDEBAR_COLLAPSED_KEY } from '@/utils/storage'

export const useAppStore = defineStore('app', () => {
  const storedCollapsed = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
  const sidebarCollapsed = ref(
    storedCollapsed === 'true' || (storedCollapsed === null && window.innerWidth <= 900),
  )

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(sidebarCollapsed.value))
  }

  function setSidebarCollapsed(collapsed: boolean): void {
    sidebarCollapsed.value = collapsed
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed))
  }

  return {
    sidebarCollapsed,
    toggleSidebar,
    setSidebarCollapsed,
  }
})
