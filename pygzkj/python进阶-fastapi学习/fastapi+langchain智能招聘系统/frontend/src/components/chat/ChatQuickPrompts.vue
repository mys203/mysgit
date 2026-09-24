<script setup lang="ts">
import { Sparkles } from 'lucide-vue-next'

const props = defineProps<{
  prompts: string[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  select: [prompt: string]
}>()
</script>

<template>
  <div v-if="props.prompts.length" class="flex flex-wrap justify-center gap-2">
    <button
      v-for="prompt in props.prompts"
      :key="prompt"
      type="button"
      class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="props.disabled"
      @click="emit('select', prompt)"
    >
      <Sparkles :size="13" />
      {{ prompt }}
    </button>
  </div>
</template>
