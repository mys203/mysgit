import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import { TAGS_VIEW_KEY, readJson, writeJson } from '@/utils/storage'

export interface ViewTab {
  path: string
  title: string
  name: string
}

function isViewTab(value: unknown): value is ViewTab {
  if (!value || typeof value !== 'object') {
    return false
  }

  const item = value as Record<string, unknown>
  return (
    typeof item.path === 'string' &&
    typeof item.title === 'string' &&
    typeof item.name === 'string'
  )
}

const restoredTabs = readJson<unknown>(TAGS_VIEW_KEY, [] as ViewTab[])
const initialTabs = Array.isArray(restoredTabs) ? restoredTabs.filter(isViewTab) : []

export const useTagsViewStore = defineStore('tagsView', () => {
  const tabs = ref<ViewTab[]>(initialTabs)

  function persist(): void {
    writeJson(TAGS_VIEW_KEY, tabs.value)
  }

  function addTab(route: RouteLocationNormalizedLoaded): void {
    if (!route.name || route.meta.hidden === true) {
      return
    }

    const title = typeof route.meta.title === 'string' ? route.meta.title : String(route.name)
    const existing = tabs.value.find((tab) => tab.path === route.path)

    if (existing) {
      existing.title = title
      existing.name = String(route.name)
    } else {
      tabs.value.push({
        path: route.path,
        title,
        name: String(route.name),
      })
    }

    persist()
  }

  function removeTab(path: string): string | null {
    const index = tabs.value.findIndex((tab) => tab.path === path)
    if (index === -1) {
      return null
    }

    if (tabs.value.length === 1) {
      return tabs.value[0].path
    }

    tabs.value.splice(index, 1)
    persist()
    const nextTab = tabs.value[index] ?? tabs.value[index - 1] ?? null
    return nextTab?.path ?? null
  }

  function removeOtherTabs(path: string): void {
    const current = tabs.value.find((tab) => tab.path === path)
    tabs.value = current ? [current] : []
    persist()
  }

  function removeAllTabs(): void {
    tabs.value = []
    persist()
  }

  return {
    tabs,
    addTab,
    removeTab,
    removeOtherTabs,
    removeAllTabs,
  }
})
