<script setup lang="ts">
import { computed } from 'vue'
import {
  Bot,
  CheckCircle2,
  CircleAlert,
  ExternalLink,
  LoaderCircle,
  RotateCcw,
  UserRound,
} from 'lucide-vue-next'
import type { RouteLocationRaw } from 'vue-router'
import type { ChatCitation, ChatMessage, ChatMessageId } from '@/types/chat'
import {
  buildCitationRoute,
  getCitationTypeLabel,
} from '@/utils/chatSessions'
import { formatDateTime } from '@/utils/format'

const props = defineProps<{
  message: ChatMessage
}>()

const emit = defineEmits<{
  retry: [messageId: ChatMessageId]
  navigate: [route: RouteLocationRaw]
}>()

const isUser = computed(() => props.message.role === 'USER')
const isStreaming = computed(
  () =>
    props.message.role === 'ASSISTANT' &&
    (props.message.status === 'PENDING' ||
      props.message.status === 'STREAMING'),
)
const canRetry = computed(
  () => props.message.role === 'ASSISTANT' && props.message.status === 'FAILED',
)
const showTerminalStatus = computed(
  () =>
    props.message.status === 'STOPPED' ||
    props.message.status === 'CANCELLED' ||
    props.message.status === 'UNKNOWN',
)

function terminalStatusText(): string {
  if (props.message.status === 'CANCELLED') {
    return '回答已取消'
  }
  if (props.message.status === 'UNKNOWN') {
    return '回答状态未知'
  }
  return '回答已停止'
}

function navigateCitation(citation: ChatCitation): void {
  const route = buildCitationRoute(citation)
  if (route) {
    emit('navigate', route)
  }
}

function citationHasRoute(citation: ChatCitation): boolean {
  return buildCitationRoute(citation) !== null
}

function progressMessage(): string {
  const progress = props.message.progress
  if (!progress) {
    return '正在生成回答'
  }

  return progress.message || progress.stage || '正在生成回答'
}
</script>

<template>
  <article
    class="flex gap-3 px-4 py-3"
    :class="isUser ? 'justify-end' : 'justify-start'"
  >
    <div
      v-if="!isUser"
      class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600"
    >
      <Bot :size="17" />
    </div>

    <div class="min-w-0 max-w-[860px]" :class="isUser ? 'order-1' : ''">
      <div
        class="mb-1 flex items-center gap-2 text-xs"
        :class="isUser ? 'justify-end text-slate-400' : 'text-slate-400'"
      >
        <span>{{ isUser ? '我' : 'AI 招聘助手' }}</span>
        <span>{{ formatDateTime(props.message.created_at) }}</span>
      </div>

      <div
        class="rounded-md px-4 py-3 text-sm leading-6 shadow-sm"
        :class="
          isUser
            ? 'bg-[#409eff] text-white'
            : 'border border-slate-200 bg-white text-slate-700'
        "
      >
        <p
          v-if="props.message.content"
          class="whitespace-pre-wrap break-words"
        >
          {{ props.message.content }}
        </p>
        <div
          v-else-if="isStreaming"
          class="flex items-center gap-2 text-slate-400"
        >
          <LoaderCircle :size="15" class="animate-spin" />
          <span>{{ progressMessage() }}</span>
        </div>
        <p v-else class="text-slate-400">暂无回答内容</p>

        <span
          v-if="isStreaming && props.message.content"
          class="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-blue-500 align-middle"
        />
      </div>

      <div
        v-if="!isUser && (props.message.degraded || showTerminalStatus)"
        class="mt-2 flex flex-wrap items-center gap-2"
      >
        <el-tag
          v-if="props.message.degraded"
          size="small"
          type="warning"
          effect="light"
        >
          降级回答
        </el-tag>
        <span
          v-if="showTerminalStatus"
          class="text-xs text-slate-400"
        >
          {{ terminalStatusText() }}
        </span>
      </div>

      <div
        v-if="!isUser && props.message.status === 'COMPLETED'"
        class="mt-2 flex items-center gap-1 text-xs text-emerald-600"
      >
        <CheckCircle2 :size="13" />
        回答完成
      </div>

      <div
        v-if="!isUser && props.message.status === 'FAILED'"
        class="mt-2 rounded border border-red-200 bg-red-50 px-3 py-2"
      >
        <div class="flex items-start gap-2 text-xs text-red-700">
          <CircleAlert :size="15" class="mt-0.5 shrink-0" />
          <span>{{ props.message.error_message || '回答生成失败，请重试' }}</span>
        </div>
        <button
          v-if="canRetry"
          type="button"
          class="mt-2 inline-flex items-center gap-1 text-xs font-medium text-red-700 hover:text-red-800"
          @click="emit('retry', props.message.id)"
        >
          <RotateCcw :size="13" />
          重试
        </button>
      </div>

      <details
        v-if="!isUser && props.message.citations.length"
        class="mt-2 rounded border border-slate-200 bg-white"
      >
        <summary
          class="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-xs text-slate-500"
        >
          <span>引用依据</span>
          <span class="rounded-full bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">
            {{ props.message.citations.length }}
          </span>
        </summary>
        <div class="border-t border-slate-100 px-3 py-2">
          <button
            v-for="(citation, index) in props.message.citations"
            :key="citation.id ?? `${citation.title}-${index}`"
            type="button"
            class="flex w-full items-start justify-between gap-3 border-b border-slate-100 py-2 text-left last:border-0 disabled:cursor-default"
            :disabled="!citationHasRoute(citation)"
            @click="navigateCitation(citation)"
          >
            <span class="min-w-0">
              <span class="flex items-center gap-1.5">
                <el-tag size="small" effect="plain">
                  {{ getCitationTypeLabel(citation) }}
                </el-tag>
                <span class="truncate text-xs font-medium text-slate-700">
                  {{ citation.title }}
                </span>
              </span>
              <span
                v-if="citation.snippet"
                class="mt-1 line-clamp-2 block text-xs leading-5 text-slate-400"
              >
                {{ citation.snippet }}
              </span>
            </span>
            <ExternalLink
              v-if="citationHasRoute(citation)"
              :size="14"
              class="mt-1 shrink-0 text-blue-500"
            />
          </button>
        </div>
      </details>
    </div>

    <div
      v-if="isUser"
      class="order-2 mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600"
    >
      <UserRound :size="17" />
    </div>
  </article>
</template>
