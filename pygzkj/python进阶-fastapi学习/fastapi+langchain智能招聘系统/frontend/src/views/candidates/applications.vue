<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshCw } from 'lucide-vue-next'
import { fetchApplications, updateApplicationStage } from '@/api/candidates'
import { fetchCandidates } from '@/api/candidates'
import { fetchJobs } from '@/api/jobs'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePagedList } from '@/composables/usePagedList'
import type { Application, ApplicationStage } from '@/types/candidate'
import type { Candidate } from '@/types/candidate'
import type { Job } from '@/types/job'
import { formatDateTime } from '@/utils/format'

interface ApplicationFilters extends Record<string, unknown> {
  job_id: number | null
  stage: ApplicationStage | ''
}

const list = usePagedList<Application, ApplicationFilters>(fetchApplications, {
  job_id: null,
  stage: '',
})

const jobs = ref<Job[]>([])
const candidates = ref<Candidate[]>([])

const stageOptions: Array<{ label: string; value: ApplicationStage }> = [
  { label: '已申请', value: 'APPLIED' },
  { label: '筛选中', value: 'SCREENING' },
  { label: '面试中', value: 'INTERVIEW' },
  { label: '待录用', value: 'OFFER' },
  { label: '已录用', value: 'HIRED' },
  { label: '已淘汰', value: 'REJECTED' },
  { label: '已撤回', value: 'WITHDRAWN' },
]

const jobMap = computed(() => new Map(jobs.value.map((item) => [item.id, item.title])))
const candidateMap = computed(
  () => new Map(candidates.value.map((item) => [item.id, item.name])),
)

function getStageLabel(stage: ApplicationStage): string {
  return stageOptions.find((item) => item.value === stage)?.label || stage
}

async function loadOptions(): Promise<void> {
  const [jobResult, candidateResult] = await Promise.allSettled([
    fetchJobs({ page: 1, page_size: 100 }),
    fetchCandidates({ page: 1, page_size: 100 }),
  ])

  if (jobResult.status === 'fulfilled') {
    jobs.value = jobResult.value.items
  }
  if (candidateResult.status === 'fulfilled') {
    candidates.value = candidateResult.value.items
  }
}

async function changeStage(row: Application, stage: ApplicationStage): Promise<void> {
  if (row.stage === stage) {
    return
  }

  await updateApplicationStage(row.id, { stage })
  row.stage = stage
  ElMessage.success('应聘阶段已更新')
}

onMounted(() => {
  void list.load()
  void loadOptions()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="应聘流程" description="跟踪候选人的申请进度与招聘阶段">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div class="filter-row">
          <el-select
            v-model="list.filters.job_id"
            class="w-64"
            clearable
            filterable
            placeholder="应聘岗位"
          >
            <el-option
              v-for="job in jobs"
              :key="job.id"
              :label="job.title"
              :value="job.id"
            />
          </el-select>
          <el-select
            v-model="list.filters.stage"
            class="w-36"
            clearable
            placeholder="招聘阶段"
          >
            <el-option
              v-for="option in stageOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-button type="primary" @click="list.search">查询</el-button>
          <el-button @click="list.reset">重置</el-button>
        </div>
        <span class="text-xs text-slate-400">共 {{ list.total.value }} 条应聘记录</span>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无应聘记录"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column label="候选人" min-width="130">
            <template #default="{ row }">
              {{ candidateMap.get(row.candidate_id) || `候选人 #${row.candidate_id}` }}
            </template>
          </el-table-column>
          <el-table-column label="应聘岗位" min-width="210">
            <template #default="{ row }">
              {{ jobMap.get(row.job_id) || `岗位 #${row.job_id}` }}
            </template>
          </el-table-column>
          <el-table-column label="简历 ID" width="100">
            <template #default="{ row }">{{ row.resume_id || '-' }}</template>
          </el-table-column>
          <el-table-column label="当前阶段" width="130">
            <template #default="{ row }">
              <el-dropdown trigger="click">
                <el-button size="small">{{ getStageLabel(row.stage) }}</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="option in stageOptions"
                      :key="option.value"
                      @click="changeStage(row, option.value)"
                    >
                      {{ option.label }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" min-width="100">
            <template #default="{ row }">{{ row.source || '-' }}</template>
          </el-table-column>
          <el-table-column label="申请时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.applied_at) }}</template>
          </el-table-column>
          <el-table-column label="更新时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
          </el-table-column>
        </el-table>
      </DataState>

      <PaginationBar
        :page="list.page.value"
        :page-size="list.pageSize.value"
        :total="list.total.value"
        @update:page="list.changePage"
        @update:page-size="list.changePageSize"
      />
    </section>
  </div>
</template>
