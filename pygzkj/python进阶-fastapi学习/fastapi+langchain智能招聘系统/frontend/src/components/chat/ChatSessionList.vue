<script setup lang="ts">
import { ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import {
  LoaderCircle,
  MessageSquareText,
  MoreHorizontal,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from 'lucide-vue-next'
import type { ChatSession } from '@/types/chat'
import { formatDateTime } from '@/utils/format'

const props = defineProps<{
  sessions: ChatSession[]
  activeId: number | null
  loading: boolean
  loadingMore: boolean
  hasMore: boolean
  error: string
  total: number
}>()

const emit = defineEmits<{
  create: []
  select: [sessionId: number]
  rename: [sessionId: number, title: string]
  remove: [sessionId: number]
  search: [keyword: string]
  loadMore: []
  retry: []
}>()

const keyword = ref('')

function submitSearch(): void {
  emit('search', keyword.value.trim())
}

function clearSearch(): void {
  keyword.value = ''
  emit('search', '')
}

async function renameSession(session: ChatSession): Promise<void> {
  try {
    const result = await ElMessageBox.prompt('请输入新的会话名称', '重命名会话', {
      inputValue: session.title,
      inputPattern: /\S+/,
      inputErrorMessage: '会话名称不能为空',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    })
    const title = result.value.trim()
    if (title && title !== session.title) {
      emit('rename', session.id, title)
    }
  } catch {
    // 用户取消时无需处理。
  }
}

async function removeSession(session: ChatSession): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确定删除会话“${session.title}”吗？删除后无法恢复。`,
      '删除会话',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    emit('remove', session.id)
  } catch {
    // 用户取消时无需处理。
  }
}

function handleCommand(command: string, session: ChatSession): void {
  if (command === 'rename') {
    void renameSession(session)
  }
  if (command === 'remove') {
    void removeSession(session)
  }
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-white">
    <div class="border-b border-slate-200 px-3 py-3">
      <div class="mb-3 flex items-center justify-between">
        <div>
          <h2 class="text-sm font-semibold text-slate-800">会话记录</h2>
          <p class="mt-0.5 text-xs text-slate-400">共 {{ props.total }} 个会话</p>
        </div>
        <el-button
          type="primary"
          size="small"
          :icon="Plus"
          @click="emit('create')"
        >
          新建
        </el-button>
      </div>

      <el-input
        v-model="keyword"
        clearable
        :prefix-icon="Search"
        placeholder="搜索会话"
        @keyup.enter="submitSearch"
        @clear="clearSearch"
      />
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-2 py-2">
      <div v-if="props.loading" class="space-y-2 px-1 py-2">
        <div
          v-for="index in 5"
          :key="index"
          class="h-16 animate-pulse rounded bg-slate-100"
        />
      </div>

      <el-alert
        v-else-if="props.error"
        :title="props.error"
        type="error"
        :closable="false"
        show-icon
      >
        <button
          type="button"
          class="mt-2 flex items-center gap-1 text-xs text-red-600"
          @click="emit('retry')"
        >
          <RefreshCw :size="13" />
          重新加载
        </button>
      </el-alert>

      <div
        v-else-if="props.sessions.length === 0"
        class="flex h-full min-h-40 flex-col items-center justify-center text-center"
      >
        <MessageSquareText :size="26" class="text-slate-300" />
        <p class="mt-2 text-sm text-slate-500">暂无会话</p>
        <button
          type="button"
          class="mt-3 text-xs text-blue-600 hover:text-blue-700"
          @click="emit('create')"
        >
          创建第一个会话
        </button>
      </div>

      <div v-else class="space-y-1">
        <div
          v-for="session in props.sessions"
          :key="session.id"
          class="group flex cursor-pointer items-start gap-2 rounded px-2 py-2.5 transition"
          :class="
            session.id === props.activeId
              ? 'bg-blue-50'
              : 'hover:bg-slate-50'
          "
          @click="emit('select', session.id)"
        >
          <span
            class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded"
            :class="
              session.id === props.activeId
                ? 'bg-blue-100 text-blue-600'
                : 'bg-slate-100 text-slate-500'
            "
          >
            <MessageSquareText :size="15" />
          </span>

          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-slate-700">
              {{ session.title }}
            </p>
            <p class="mt-1 truncate text-xs text-slate-400">
              {{ formatDateTime(session.last_message_at || session.updated_at) }}
            </p>
          </div>

          <el-dropdown
            trigger="click"
            @command="(command: string) => handleCommand(command, session)"
          >
            <button
              type="button"
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded text-slate-400 opacity-100 transition hover:bg-white hover:text-slate-700 md:opacity-0 md:group-focus-within:opacity-100 md:group-hover:opacity-100"
              title="会话操作"
              @click.stop
            >
              <MoreHorizontal :size="15" />
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">
                  <Pencil :size="14" class="mr-2" />
                  重命名
                </el-dropdown-item>
                <el-dropdown-item command="remove" divided>
                  <Trash2 :size="14" class="mr-2 text-red-500" />
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <div
      v-if="props.hasMore && !props.loading && !props.error"
      class="border-t border-slate-100 p-2"
    >
      <button
        type="button"
        class="flex w-full items-center justify-center gap-1.5 rounded py-2 text-xs text-slate-500 transition hover:bg-slate-50 hover:text-blue-600"
        :disabled="props.loadingMore"
        @click="emit('loadMore')"
      >
        <LoaderCircle v-if="props.loadingMore" :size="14" class="animate-spin" />
        <span>{{ props.loadingMore ? '加载中' : '加载更多' }}</span>
      </button>
    </div>
  </div>
</template>
