<script setup lang="ts">
import {
  BriefcaseBusiness,
  Menu,
  PanelRight,
  UserRoundSearch,
} from 'lucide-vue-next'
import type { Candidate } from '@/types/candidate'
import type { ChatContext } from '@/types/chat'
import type { Job } from '@/types/job'

const props = defineProps<{
  title: string
  context: ChatContext
  job: Job | null
  candidate: Candidate | null
  jobs: Job[]
  candidates: Candidate[]
  jobLoading: boolean
  candidateLoading: boolean
  disabled?: boolean
  contextPanelOpen?: boolean
}>()

const emit = defineEmits<{
  'update:jobId': [jobId: number | null]
  'update:candidateId': [candidateId: number | null]
  searchJobs: [keyword: string]
  searchCandidates: [keyword: string]
  openSessions: []
  openContext: []
  toggleContext: []
}>()

function toPositiveId(value: unknown): number | null {
  if (typeof value === 'number' && Number.isInteger(value) && value > 0) {
    return value
  }

  if (typeof value === 'string' && /^\d+$/.test(value)) {
    const parsed = Number(value)
    return parsed > 0 ? parsed : null
  }

  return null
}
</script>

<template>
  <header class="shrink-0 border-b border-slate-200 bg-white px-3 py-2.5">
    <div class="flex items-center gap-2">
      <button
        type="button"
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-slate-200 text-slate-500 md:hidden"
        title="打开会话列表"
        @click="emit('openSessions')"
      >
        <Menu :size="17" />
      </button>

      <div class="min-w-0 flex-1">
        <h1 class="truncate text-sm font-semibold text-slate-800">
          {{ props.title }}
        </h1>
        <p class="mt-0.5 hidden text-xs text-slate-400 sm:block">
          基于岗位与候选人资料进行连续问答
        </p>
      </div>

      <button
        type="button"
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded border text-slate-500 transition xl:hidden"
        :class="
          props.contextPanelOpen
            ? 'border-blue-300 bg-blue-50 text-blue-600'
            : 'border-slate-200 hover:border-blue-300 hover:text-blue-600'
        "
        title="查看上下文详情"
        @click="emit('openContext')"
      >
        <PanelRight :size="17" />
      </button>

      <button
        type="button"
        class="hidden h-8 w-8 shrink-0 items-center justify-center rounded border text-slate-500 transition xl:flex"
        :class="
          props.contextPanelOpen
            ? 'border-blue-300 bg-blue-50 text-blue-600'
            : 'border-slate-200 hover:border-blue-300 hover:text-blue-600'
        "
        :title="props.contextPanelOpen ? '收起上下文详情' : '展开上下文详情'"
        @click="emit('toggleContext')"
      >
        <PanelRight :size="17" />
      </button>
    </div>

    <div class="mt-2 flex flex-wrap items-center gap-2">
      <div class="grid min-w-0 flex-1 grid-cols-2 gap-2 lg:max-w-[520px]">
        <el-select
          :model-value="props.context.job_id ?? null"
          clearable
          filterable
          remote
          reserve-keyword
          :remote-method="(keyword: string) => emit('searchJobs', keyword)"
          :loading="props.jobLoading"
          :disabled="props.disabled"
          placeholder="选择岗位"
          @update:model-value="(value: unknown) => emit('update:jobId', toPositiveId(value))"
        >
          <template #prefix>
            <BriefcaseBusiness :size="14" class="text-slate-400" />
          </template>
          <el-option
            v-for="option in props.jobs"
            :key="option.id"
            :label="`${option.title} · ${option.code}`"
            :value="option.id"
          />
        </el-select>

        <el-select
          :model-value="props.context.candidate_id ?? null"
          clearable
          filterable
          remote
          reserve-keyword
          :remote-method="(keyword: string) => emit('searchCandidates', keyword)"
          :loading="props.candidateLoading"
          :disabled="props.disabled"
          placeholder="选择候选人"
          @update:model-value="
            (value: unknown) => emit('update:candidateId', toPositiveId(value))
          "
        >
          <template #prefix>
            <UserRoundSearch :size="14" class="text-slate-400" />
          </template>
          <el-option
            v-for="option in props.candidates"
            :key="option.id"
            :label="`${option.name} · ${option.current_title || '暂无职位'}`"
            :value="option.id"
          />
        </el-select>
      </div>

      <div
        v-if="props.context.job_id || props.context.candidate_id"
        class="flex min-w-0 flex-wrap items-center gap-1.5"
      >
        <el-tag
          v-if="props.context.job_id"
          closable
          effect="light"
          :disable-transitions="true"
          @close="emit('update:jobId', null)"
        >
          岗位：{{ props.job?.title || `#${props.context.job_id}` }}
        </el-tag>
        <el-tag
          v-if="props.context.candidate_id"
          closable
          effect="light"
          type="success"
          :disable-transitions="true"
          @close="emit('update:candidateId', null)"
        >
          候选人：{{ props.candidate?.name || `#${props.context.candidate_id}` }}
        </el-tag>
      </div>
    </div>
  </header>
</template>
