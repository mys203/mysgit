import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const useLoadingStore = defineStore('loading', () => {
  const pendingCount = ref(0)
  const active = computed(() => pendingCount.value > 0)

  function start(): void {
    pendingCount.value += 1
  }

  function finish(): void {
    pendingCount.value = Math.max(0, pendingCount.value - 1)
  }

  function reset(): void {
    pendingCount.value = 0
  }

  return {
    pendingCount,
    active,
    start,
    finish,
    reset,
  }
})
