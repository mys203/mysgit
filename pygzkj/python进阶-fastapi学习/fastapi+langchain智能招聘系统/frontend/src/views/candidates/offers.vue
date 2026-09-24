<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { BriefcaseBusiness, RefreshCw } from 'lucide-vue-next'
import { fetchApplications, updateApplicationStage } from '@/api/candidates'
import { fetchCandidates } from '@/api/candidates'
import { fetchJobs } from '@/api/jobs'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { usePagedList } from '@/composables/usePagedList'
import type { Application, ApplicationStage, Candidate } from '@/types/candidate'
import type { Job } from '@/types/job'
import { formatDateTime } from '@/utils/format'

interface OfferFilters extends Record<string, unknown> {
  stage: ApplicationStage | ''
}

const list = usePagedList<Application, OfferFilters>(fetchApplications, {
  stage: 'OFFER',
})
const jobs = ref<Job[]>([])
const candidates = ref<Candidate[]>([])

const jobMap = computed(() => new Map(jobs.value.map((item) => [item.id, item.title])))
const candidateMap = computed(
  () => new Map(candidates.value.map((item) => [item.id, item.name])),
)

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

async function updateOffer(row: Application, stage: ApplicationStage): Promise<void> {
  await updateApplicationStage(row.id, { stage })
  row.stage = stage
  ElMessage.success(stage === 'HIRED' ? '已确认录用' : '已更新录用状态')
  await list.load()
}

onMounted(() => {
  void list.load()
  void loadOptions()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="录用管理" description="跟进待录用与已录用候选人">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <el-select v-model="list.filters.stage" class="w-36" clearable placeholder="录用阶段">
          <el-option label="待录用" value="OFFER" />
          <el-option label="已录用" value="HIRED" />
        </el-select>
        <el-button type="primary" @click="list.search">查询</el-button>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无录用流程"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column label="候选人" min-width="130">
            <template #default="{ row }">
              {{ candidateMap.get(row.candidate_id) || `候选人 #${row.candidate_id}` }}
            </template>
          </el-table-column>
          <el-table-column label="岗位" min-width="210">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <BriefcaseBusiness :size="16" class="text-blue-500" />
                {{ jobMap.get(row.job_id) || `岗位 #${row.job_id}` }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="招聘阶段" width="110">
            <template #default="{ row }">
              {{ row.stage === 'HIRED' ? '已录用' : '待录用' }}
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.stage !== 'HIRED'"
                link
                type="success"
                @click="updateOffer(row, 'HIRED')"
              >
                确认录用
              </el-button>
              <el-button
                v-else
                link
                type="warning"
                @click="updateOffer(row, 'OFFER')"
              >
                撤回录用
              </el-button>
            </template>
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
