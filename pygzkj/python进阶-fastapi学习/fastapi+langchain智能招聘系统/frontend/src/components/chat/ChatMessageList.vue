<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { ArrowUp, LoaderCircle, MessageSquareText, RefreshCw } from 'lucide-vue-next'
import type { RouteLocationRaw } from 'vue-router'
import type { ChatMessage, ChatMessageId } from '@/types/chat'
import ChatMessageItem from '@/components/chat/ChatMessageItem.vue'
import ChatQuickPrompts from '@/components/chat/ChatQuickPrompts.vue'

const props = defineProps<{
  sessionId: number | null
  messages: ChatMessage[]
  loading: boolean
  loadingOlder: boolean
  hasMore: boolean
  error: string
  sending: boolean
  quickPrompts: string[]
}>()

const emit = defineEmits<{
  retryLoad: []
  loadOlder: []
  retry: [messageId: ChatMessageId]
  navigate: [route: RouteLocationRaw]
  quickSelect: [prompt: string]
}>()

const scrollContainer = ref<HTMLElement | null>(null)
const nearBottom = ref(true)

function handleScroll(): void {
  const element = scrollContainer.value
  if (!element) {
    return
  }

  nearBottom.value =
    element.scrollHeight - element.scrollTop - element.clientHeight < 120
}

async function scrollToBottom(smooth = false): Promise<void> {
  await nextTick()
  const element = scrollContainer.value
  if (!element) {
    return
  }

  element.scrollTo({
    top: element.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto',
  })
}

watch(
  () => props.sessionId,
  () => {
    nearBottom.value = true
    void scrollToBottom()
  },
)

watch(
  () => [
    props.messages.length,
    props.messages[props.messages.length - 1]?.content ?? '',
    props.messages[props.messages.length - 1]?.status ?? '',
  ],
  () => {
    if (nearBottom.value) {
      void scrollToBottom()
    }
  },
)
</script>

<template>
  <div
    ref="scrollContainer"
    class="relative min-h-0 flex-1 overflow-y-auto overscroll-contain bg-slate-50"
    @scroll.passive="handleScroll"
  >
    <div
      v-if="props.hasMore && !props.loading"
      class="sticky top-0 z-10 flex justify-center bg-gradient-to-b from-slate-50 to-transparent px-4 py-2"
    >
      <button
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500 shadow-sm transition hover:border-blue-300 hover:text-blue-600 disabled:opacity-50"
        :disabled="props.loadingOlder"
        @click="emit('loadOlder')"
      >
        <LoaderCircle v-if="props.loadingOlder" :size="13" class="animate-spin" />
        <ArrowUp v-else :size="13" />
        {{ props.loadingOlder ? '加载中' : '加载更早消息' }}
      </button>
    </div>

    <div v-if="props.loading" class="space-y-4 px-4 py-6">
      <div class="ml-auto h-20 w-2/3 animate-pulse rounded bg-slate-200/70" />
      <div class="h-28 w-4/5 animate-pulse rounded bg-white" />
      <div class="ml-auto h-16 w-1/2 animate-pulse rounded bg-slate-200/70" />
    </div>

    <div v-else-if="props.error" class="flex min-h-full items-center justify-center p-6">
      <el-alert
        :title="props.error"
        type="error"
        :closable="false"
        show-icon
      >
        <button
          type="button"
          class="mt-2 inline-flex items-center gap-1 text-xs text-red-600"
          @click="emit('retryLoad')"
        >
          <RefreshCw :size="13" />
          重新加载
        </button>
      </el-alert>
    </div>

    <div
      v-else-if="props.messages.length === 0"
      class="flex min-h-full flex-col items-center justify-center px-4 py-10 text-center"
    >
      <span class="flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600">
        <MessageSquareText :size="23" />
      </span>
      <h2 class="mt-3 text-base font-semibold text-slate-700">开始新的招聘对话</h2>
      <p class="mt-1 text-xs text-slate-400">
        可直接提问，也可选择岗位或候选人补充上下文
      </p>
      <div class="mt-5 max-w-2xl">
        <ChatQuickPrompts
          :prompts="props.quickPrompts"
          :disabled="props.sending"
          @select="emit('quickSelect', $event)"
        />
      </div>
    </div>

    <div v-else class="pb-4">
      <ChatMessageItem
        v-for="message in props.messages"
        :key="message.id"
        :message="message"
        @retry="emit('retry', $event)"
        @navigate="emit('navigate', $event)"
      />
    </div>
  </div>
</template>
