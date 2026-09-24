<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
    <div>
      <h1 class="text-xl font-semibold tracking-normal text-slate-800">{{ title }}</h1>
      <p v-if="description" class="mt-1 text-sm text-slate-500">{{ description }}</p>
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <slot name="actions"></slot>
    </div>
  </div>
</template>
