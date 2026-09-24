<script setup lang="ts">
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import { useLoadingStore } from '@/stores/loading'

const loadingStore = useLoadingStore()
const loadingStyle = computed(() => ({
  width: loadingStore.active ? '82%' : '0',
}))
</script>

<template>
  <RouterView />
  <div class="global-loading-track" aria-hidden="true">
    <div class="global-loading-bar" :style="loadingStyle"></div>
  </div>
</template>
