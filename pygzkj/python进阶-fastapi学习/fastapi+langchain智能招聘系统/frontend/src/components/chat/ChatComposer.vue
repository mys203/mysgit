<script setup lang="ts">
import { ref } from 'vue'
import { LoaderCircle, Send, Square } from 'lucide-vue-next'
import type { ChatProgress } from '@/types/chat'

const props = defineProps<{
  sending: boolean
  disabled?: boolean
  progress: ChatProgress | null
}>()

const emit = defineEmits<{
  send: [content: string]
  stop: []
}>()

const draft = ref('')

function send(): void {
  const content = draft.value.trim()
  if (!content || props.sending || props.disabled) {
    return
  }

  emit('send', content)
  draft.value = ''
}

function handleKeydown(event: KeyboardEvent): void {
  if (
    event.key === 'Enter' &&
    !event.shiftKey &&
    !event.isComposing
  ) {
    event.preventDefault()
    send()
  }
}

function progressText(): string {
  return props.progress?.message || props.progress?.stage || '正在生成回答'
}
</script>

<template>
  <footer class="shrink-0 border-t border-slate-200 bg-white px-3 py-3">
    <div
      v-if="props.sending"
      class="mb-2 flex items-center justify-between gap-3 rounded bg-blue-50 px-3 py-2"
    >
      <span class="flex min-w-0 items-center gap-2 text-xs text-blue-700">
        <LoaderCircle :size="14" class="shrink-0 animate-spin" />
        <span class="truncate">{{ progressText() }}</span>
      </span>
      <el-button size="small" type="danger" plain :icon="Square" @click="emit('stop')">
        停止
      </el-button>
    </div>

    <div class="rounded-md border border-slate-200 bg-white p-2 shadow-sm">
      <el-input
        v-model="draft"
        type="textarea"
        :rows="3"
        resize="none"
        maxlength="4000"
        show-word-limit
        :disabled="props.disabled"
        placeholder="输入你的招聘问题"
        @keydown="handleKeydown"
      />
      <div class="mt-2 flex items-center justify-between gap-3">
        <span class="truncate text-xs text-slate-400">
          {{ props.disabled ? '网络连接已断开' : '上下文已同步' }}
        </span>
        <el-button
          v-if="!props.sending"
          type="primary"
          :icon="Send"
          :disabled="props.disabled || !draft.trim()"
          @click="send"
        >
          发送
        </el-button>
      </div>
    </div>
  </footer>
</template>
