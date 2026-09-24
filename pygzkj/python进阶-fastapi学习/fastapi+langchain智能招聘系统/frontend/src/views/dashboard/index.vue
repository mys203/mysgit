<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  BriefcaseBusiness,
  Bot,
  CalendarClock,
  CircleUserRound,
  RefreshCw,
} from 'lucide-vue-next'
import { fetchDashboardSummary } from '@/api/dashboard'
import PageHeader from '@/components/PageHeader.vue'
import type { DashboardSummary } from '@/types/system'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime } from '@/utils/format'

const summary = ref<DashboardSummary | null>(null)
const loading = ref(false)
const errorMessage = ref('')

function sumCounts(source?: Record<string, number>): number {
  return Object.values(source ?? {}).reduce((total, value) => total + value, 0)
}

const metrics = computed(() => {
  if (!summary.value) {
    return []
  }

  return [
    {
      label: '岗位总数',
      value: sumCounts(summary.value.jobs),
      hint: `${summary.value.jobs.PUBLISHED ?? 0} 个招聘中`,
      icon: BriefcaseBusiness,
      color: 'bg-blue-50 text-blue-600',
    },
    {
      label: '候选人总量',
      value: sumCounts(summary.value.candidates),
      hint: `${summary.value.candidates.ACTIVE ?? 0} 位正常候选人`,
      icon: CircleUserRound,
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      label: '面试安排',
      value: sumCounts(summary.value.interviews),
      hint: `${summary.value.interviews.SCHEDULED ?? 0} 场待进行`,
      icon: CalendarClock,
      color: 'bg-amber-50 text-amber-600',
    },
    {
      label: 'AI 任务',
      value: sumCounts(summary.value.ai_tasks),
      hint: `${summary.value.ai_tasks.FAILED ?? 0} 个失败任务`,
      icon: Bot,
      color: 'bg-violet-50 text-violet-600',
    },
  ]
})

const distributionSections = computed(() => {
  if (!summary.value) {
    return []
  }

  return [
    { title: '岗位状态分布', data: summary.value.jobs },
    { title: '候选人状态分布', data: summary.value.candidates },
    { title: '应聘阶段分布', data: summary.value.applications },
    { title: '面试状态分布', data: summary.value.interviews },
    { title: 'AI 任务状态分布', data: summary.value.ai_tasks },
  ]
})

async function loadSummary(): Promise<void> {
  loading.value = true
  errorMessage.value = ''

  try {
    summary.value = await fetchDashboardSummary()
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
    summary.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadSummary)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="工作台" description="招聘业务与 AI 处理的实时概览">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="loading" @click="loadSummary">
          刷新数据
        </el-button>
      </template>
    </PageHeader>

    <el-alert
      v-if="errorMessage"
      class="mb-4"
      :title="errorMessage"
      type="error"
      :closable="false"
      show-icon
    >
      <button
        type="button"
        class="mt-3 rounded border border-red-200 bg-white px-3 py-1 text-sm text-red-600"
        @click="loadSummary"
      >
        重新加载
      </button>
    </el-alert>

    <div v-if="loading && !summary" class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="index in 4" :key="index" class="panel p-5">
        <el-skeleton :rows="2" animated />
      </div>
    </div>

    <template v-else-if="summary">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="metric in metrics" :key="metric.label" class="panel p-5">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm text-slate-500">{{ metric.label }}</p>
              <p class="mt-2 text-3xl font-semibold text-slate-800">{{ metric.value }}</p>
              <p class="mt-2 text-xs text-slate-400">{{ metric.hint }}</p>
            </div>
            <span class="flex h-10 w-10 items-center justify-center rounded" :class="metric.color">
              <component :is="metric.icon" :size="20" />
            </span>
          </div>
        </div>
      </div>

      <div class="mt-4 grid gap-4 xl:grid-cols-2">
        <section
          v-for="section in distributionSections"
          :key="section.title"
          class="panel"
        >
          <div class="border-b border-slate-100 px-4 py-3">
            <h2 class="text-sm font-semibold text-slate-700">{{ section.title }}</h2>
          </div>
          <div class="divide-y divide-slate-100">
            <div
              v-for="[key, value] in Object.entries(section.data)"
              :key="key"
              class="flex items-center justify-between px-4 py-3 text-sm"
            >
              <span class="text-slate-600">{{ key }}</span>
              <span class="font-semibold text-slate-800">{{ value }}</span>
            </div>
            <el-empty
              v-if="Object.keys(section.data).length === 0"
              description="暂无分布数据"
              :image-size="64"
            />
          </div>
        </section>
      </div>

      <p class="mt-4 text-right text-xs text-slate-400">
        数据生成时间：{{ formatDateTime(summary.generated_at) }}
      </p>
    </template>

    <el-empty v-else-if="!loading" description="暂无工作台数据" :image-size="90" />
  </div>
</template>
