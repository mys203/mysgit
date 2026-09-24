<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter, type RouteLocationRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import { WifiOff } from 'lucide-vue-next'
import { fetchCandidate, fetchCandidates } from '@/api/candidates'
import { fetchJob, fetchJobs } from '@/api/jobs'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import ChatContextBar from '@/components/chat/ChatContextBar.vue'
import ChatContextPanel from '@/components/chat/ChatContextPanel.vue'
import ChatMessageList from '@/components/chat/ChatMessageList.vue'
import ChatSessionList from '@/components/chat/ChatSessionList.vue'
import { useChatStore } from '@/stores/chat'
import type { Candidate } from '@/types/candidate'
import type { ChatContext, ChatMessageId } from '@/types/chat'
import type { Job } from '@/types/job'
import { getChatQuickPrompts } from '@/utils/chatSessions'

const router = useRouter()
const chatStore = useChatStore()
const {
  sessions,
  sessionsLoading,
  sessionsLoadingMore,
  sessionsError,
  sessionTotal,
  activeSessionId,
  activeSession,
  sessionDetailLoading,
  sessionDetailError,
  activeMessages,
  activeMessageLoading,
  activeMessageError,
  activeHasMore,
  activeProgress,
  activeSending,
} = storeToRefs(chatStore)

const draftContext = ref<ChatContext>({
  job_id: null,
  candidate_id: null,
})
const jobOptions = ref<Job[]>([])
const candidateOptions = ref<Candidate[]>([])
const resolvedJob = ref<Job | null>(null)
const resolvedCandidate = ref<Candidate | null>(null)
const jobLoading = ref(false)
const candidateLoading = ref(false)
const mobileSessionsOpen = ref(false)
const mobileContextOpen = ref(false)
const contextPanelOpen = ref(true)
const isOnline = ref(navigator.onLine)

let jobSearchTimer: ReturnType<typeof setTimeout> | null = null
let candidateSearchTimer: ReturnType<typeof setTimeout> | null = null

const currentContext = computed<ChatContext>(
  () => activeSession.value?.context ?? draftContext.value,
)
const selectedJob = computed(
  () =>
    jobOptions.value.find((job) => job.id === currentContext.value.job_id) ??
    (resolvedJob.value?.id === currentContext.value.job_id
      ? resolvedJob.value
      : null),
)
const selectedCandidate = computed(
  () =>
    candidateOptions.value.find(
      (candidate) => candidate.id === currentContext.value.candidate_id,
    ) ??
    (resolvedCandidate.value?.id === currentContext.value.candidate_id
      ? resolvedCandidate.value
      : null),
)
const pageTitle = computed(
  () => activeSession.value?.title || 'AI 招聘问答',
)
const quickPrompts = computed(() => getChatQuickPrompts(currentContext.value))
const sessionHasMore = computed(
  () => sessions.value.length < sessionTotal.value,
)

function mergeJobOption(job: Job): void {
  jobOptions.value = [job, ...jobOptions.value.filter((item) => item.id !== job.id)]
}

function mergeCandidateOption(candidate: Candidate): void {
  candidateOptions.value = [
    candidate,
    ...candidateOptions.value.filter((item) => item.id !== candidate.id),
  ]
}

async function hydrateJob(jobId: number | null | undefined): Promise<void> {
  if (!jobId || jobOptions.value.some((job) => job.id === jobId)) {
    return
  }

  try {
    const job = await fetchJob(jobId)
    resolvedJob.value = job
    mergeJobOption(job)
  } catch {
    resolvedJob.value = null
  }
}

async function hydrateCandidate(
  candidateId: number | null | undefined,
): Promise<void> {
  if (
    !candidateId ||
    candidateOptions.value.some((candidate) => candidate.id === candidateId)
  ) {
    return
  }

  try {
    const candidate = await fetchCandidate(candidateId)
    resolvedCandidate.value = candidate
    mergeCandidateOption(candidate)
  } catch {
    resolvedCandidate.value = null
  }
}

async function searchJobs(keyword = ''): Promise<void> {
  jobLoading.value = true

  try {
    const result = await fetchJobs({
      search: keyword || undefined,
      page: 1,
      page_size: 20,
    })
    const selected = resolvedJob.value
    const items = result.items
    jobOptions.value =
      selected && !items.some((job) => job.id === selected.id)
        ? [selected, ...items]
        : items
  } catch {
    jobOptions.value = resolvedJob.value ? [resolvedJob.value] : []
  } finally {
    jobLoading.value = false
  }
}

async function searchCandidates(keyword = ''): Promise<void> {
  candidateLoading.value = true

  try {
    const result = await fetchCandidates({
      search: keyword || undefined,
      page: 1,
      page_size: 20,
    })
    const selected = resolvedCandidate.value
    const items = result.items
    candidateOptions.value =
      selected && !items.some((candidate) => candidate.id === selected.id)
        ? [selected, ...items]
        : items
  } catch {
    candidateOptions.value = resolvedCandidate.value
      ? [resolvedCandidate.value]
      : []
  } finally {
    candidateLoading.value = false
  }
}

function debounceJobs(keyword: string): void {
  if (jobSearchTimer) {
    clearTimeout(jobSearchTimer)
  }
  jobSearchTimer = setTimeout(() => {
    void searchJobs(keyword)
  }, 280)
}

function debounceCandidates(keyword: string): void {
  if (candidateSearchTimer) {
    clearTimeout(candidateSearchTimer)
  }
  candidateSearchTimer = setTimeout(() => {
    void searchCandidates(keyword)
  }, 280)
}

async function applyJob(jobId: number | null): Promise<void> {
  const nextContext: ChatContext = {
    ...currentContext.value,
    job_id: jobId,
  }

  if (activeSessionId.value) {
    await chatStore.updateContext(activeSessionId.value, nextContext)
  } else {
    draftContext.value = nextContext
  }

  await hydrateJob(jobId)
}

async function applyCandidate(candidateId: number | null): Promise<void> {
  const nextContext: ChatContext = {
    ...currentContext.value,
    candidate_id: candidateId,
  }

  if (activeSessionId.value) {
    await chatStore.updateContext(activeSessionId.value, nextContext)
  } else {
    draftContext.value = nextContext
  }

  await hydrateCandidate(candidateId)
}

async function selectSession(sessionId: number): Promise<void> {
  mobileSessionsOpen.value = false
  await chatStore.selectSession(sessionId)
  await Promise.all([
    hydrateJob(activeSession.value?.context.job_id),
    hydrateCandidate(activeSession.value?.context.candidate_id),
  ])
}

function createSession(): void {
  chatStore.startNewSession()
  draftContext.value = {
    job_id: null,
    candidate_id: null,
  }
  mobileSessionsOpen.value = false
}

async function renameSession(sessionId: number, title: string): Promise<void> {
  const success = await chatStore.renameSession(sessionId, title)
  if (success) {
    ElMessage.success('会话已重命名')
  }
}

async function removeSession(sessionId: number): Promise<void> {
  try {
    await chatStore.removeSession(sessionId)
    ElMessage.success('会话已删除')
  } catch {
    // 请求层已提示错误，保留当前会话。
  }
}

async function searchSessions(keyword: string): Promise<void> {
  await chatStore.loadSessions({
    reset: true,
    keyword,
  })

  const first = sessions.value[0]
  if (first) {
    await selectSession(first.id)
  } else {
    createSession()
  }
}

async function sendMessage(content: string): Promise<void> {
  mobileSessionsOpen.value = false
  await chatStore.sendMessage(content, currentContext.value)
}

async function stopMessage(): Promise<void> {
  if (!activeSessionId.value) {
    return
  }

  await chatStore.stopSession(activeSessionId.value)
}

async function retryMessage(messageId: ChatMessageId): Promise<void> {
  if (!activeSessionId.value) {
    return
  }

  await chatStore.retryMessage(activeSessionId.value, messageId)
}

async function loadOlderMessages(): Promise<void> {
  if (!activeSessionId.value) {
    return
  }

  await chatStore.loadMessages(activeSessionId.value, { older: true })
}

async function reloadMessages(): Promise<void> {
  if (activeSessionId.value) {
    await chatStore.loadMessages(activeSessionId.value)
  }
}

function navigate(route: RouteLocationRaw): void {
  mobileContextOpen.value = false
  void router.push(route)
}

function updateOnlineState(): void {
  isOnline.value = navigator.onLine
}

watch(
  () => currentContext.value,
  (context) => {
    if (context.job_id && !jobOptions.value.some((job) => job.id === context.job_id)) {
      void hydrateJob(context.job_id)
    }
    if (
      context.candidate_id &&
      !candidateOptions.value.some(
        (candidate) => candidate.id === context.candidate_id,
      )
    ) {
      void hydrateCandidate(context.candidate_id)
    }
  },
  { immediate: true, deep: true },
)

onMounted(async () => {
  window.addEventListener('online', updateOnlineState)
  window.addEventListener('offline', updateOnlineState)

  await chatStore.loadSessions({ reset: true })
  const firstSession = sessions.value[0]
  if (firstSession) {
    await selectSession(firstSession.id)
  }

  await Promise.allSettled([searchJobs(), searchCandidates()])
})

onBeforeUnmount(() => {
  window.removeEventListener('online', updateOnlineState)
  window.removeEventListener('offline', updateOnlineState)

  if (jobSearchTimer) {
    clearTimeout(jobSearchTimer)
  }
  if (candidateSearchTimer) {
    clearTimeout(candidateSearchTimer)
  }
})
</script>

<template>
  <div class="flex h-full min-h-0 overflow-hidden bg-slate-50">
    <aside class="hidden w-[272px] shrink-0 border-r border-slate-200 md:flex">
      <ChatSessionList
        class="w-full"
        :sessions="sessions"
        :active-id="activeSessionId"
        :loading="sessionsLoading"
        :loading-more="sessionsLoadingMore"
        :has-more="sessionHasMore"
        :error="sessionsError"
        :total="sessionTotal"
        @create="createSession"
        @select="selectSession"
        @rename="renameSession"
        @remove="removeSession"
        @search="searchSessions"
        @load-more="chatStore.loadMoreSessions"
        @retry="chatStore.loadSessions({ reset: true })"
      />
    </aside>

    <section class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <ChatContextBar
        :title="pageTitle"
        :context="currentContext"
        :job="selectedJob"
        :candidate="selectedCandidate"
        :jobs="jobOptions"
        :candidates="candidateOptions"
        :job-loading="jobLoading"
        :candidate-loading="candidateLoading"
        :disabled="
          activeSending || activeMessageLoading || sessionDetailLoading
        "
        :context-panel-open="contextPanelOpen"
        @update:job-id="applyJob"
        @update:candidate-id="applyCandidate"
        @search-jobs="debounceJobs"
        @search-candidates="debounceCandidates"
        @open-sessions="mobileSessionsOpen = true"
        @open-context="mobileContextOpen = true"
        @toggle-context="contextPanelOpen = !contextPanelOpen"
      />

      <div
        v-if="!isOnline"
        class="flex shrink-0 items-center gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-700"
      >
        <WifiOff :size="14" />
        网络连接已断开，恢复后可重试失败的回答
      </div>

      <div
        v-if="sessionDetailError"
        class="shrink-0 border-b border-red-100 bg-red-50 px-4 py-2 text-xs text-red-600"
      >
        {{ sessionDetailError }}
      </div>

      <ChatMessageList
        :session-id="activeSessionId"
        :messages="activeMessages"
        :loading="activeMessageLoading || sessionDetailLoading"
        :loading-older="activeMessageLoading && activeMessages.length > 0"
        :has-more="activeHasMore"
        :error="activeMessageError"
        :sending="activeSending"
        :quick-prompts="quickPrompts"
        @retry-load="reloadMessages"
        @load-older="loadOlderMessages"
        @retry="retryMessage"
        @navigate="navigate"
        @quick-select="sendMessage"
      />

      <ChatComposer
        :sending="activeSending"
        :disabled="
          !isOnline || activeMessageLoading || sessionDetailLoading
        "
        :progress="activeProgress"
        @send="sendMessage"
        @stop="stopMessage"
      />
    </section>

    <aside
      v-if="contextPanelOpen"
      class="hidden w-[300px] shrink-0 border-l border-slate-200 xl:flex"
    >
      <ChatContextPanel
        class="w-full"
        :job="selectedJob"
        :candidate="selectedCandidate"
        :loading="jobLoading || candidateLoading"
      />
    </aside>

    <el-drawer
      v-model="mobileSessionsOpen"
      direction="ltr"
      size="88%"
      :with-header="false"
      class="chat-drawer"
    >
      <ChatSessionList
        :sessions="sessions"
        :active-id="activeSessionId"
        :loading="sessionsLoading"
        :loading-more="sessionsLoadingMore"
        :has-more="sessionHasMore"
        :error="sessionsError"
        :total="sessionTotal"
        @create="createSession"
        @select="selectSession"
        @rename="renameSession"
        @remove="removeSession"
        @search="searchSessions"
        @load-more="chatStore.loadMoreSessions"
        @retry="chatStore.loadSessions({ reset: true })"
      />
    </el-drawer>

    <el-drawer
      v-model="mobileContextOpen"
      direction="rtl"
      size="88%"
      :with-header="false"
      class="chat-drawer"
    >
      <ChatContextPanel
        :job="selectedJob"
        :candidate="selectedCandidate"
        :loading="jobLoading || candidateLoading"
      />
    </el-drawer>
  </div>
</template>

<style scoped>
.chat-drawer :deep(.el-drawer__body) {
  padding: 0;
}
</style>
