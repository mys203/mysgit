<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FileClock, RefreshCw, ScanSearch } from 'lucide-vue-next'
import {
  fetchResumeParseRecords,
  fetchResumes,
  parseResume,
} from '@/api/resumes'
import { fetchAiTask } from '@/api/ai'
import AiTaskStatus from '@/components/AiTaskStatus.vue'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import ParseConfirmDialog from '@/components/ParseConfirmDialog.vue'
import ResumeParseViewer from '@/components/ResumeParseViewer.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePagedList } from '@/composables/usePagedList'
import type {
  ParseConfirmResponse,
  Resume,
  ResumeParseRecord,
  ResumeParseTaskOutput,
} from '@/types/resume'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime } from '@/utils/format'
import { useAiTaskPolling } from '@/utils/aiTaskPolling'

type ResumeFilters = Record<string, unknown>

const list = usePagedList<Resume, ResumeFilters>(fetchResumes, {})
const drawerVisible = ref(false)
const recordsLoading = ref(false)
const recordsError = ref('')
const selectedResume = ref<Resume | null>(null)
const records = ref<ResumeParseRecord[]>([])
const selectedRecord = ref<ResumeParseRecord | null>(null)
const confirmVisible = ref(false)
const { task: parseTask, start: startParsePolling } =
  useAiTaskPolling<ResumeParseTaskOutput>()

async function loadRecords(resume: Resume): Promise<void> {
  drawerVisible.value = true
  selectedResume.value = resume
  selectedRecord.value = null
  recordsLoading.value = true
  recordsError.value = ''

  try {
    const result = await fetchResumeParseRecords(resume.id, {
      page: 1,
      page_size: 50,
    })
    records.value = result.items
    selectedRecord.value = result.items[0] ?? null
  } catch (error) {
    recordsError.value = getErrorMessage(error)
    records.value = []
  } finally {
    recordsLoading.value = false
  }
}

async function handleParse(resume: Resume): Promise<void> {
  const accepted = await parseResume(resume.id)
  const task = await startParsePolling({
    taskNo: accepted.task_no,
    getTask: (taskNo) => fetchAiTask<ResumeParseTaskOutput>(taskNo),
  })
  await list.load()
  if (selectedResume.value?.id === resume.id) {
    await loadRecords(resume)
  }
  ElMessage.success(task.degraded ? '简历解析完成，当前使用降级能力' : '简历解析完成')
}

async function handleConfirmed(result: ParseConfirmResponse): Promise<void> {
  await list.load()
  if (selectedResume.value?.id === result.resume_id) {
    await loadRecords(selectedResume.value)
  }
}

function selectRecord(record: ResumeParseRecord | null): void {
  selectedRecord.value = record
}

onMounted(list.load)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="解析记录" description="按简历查看解析批次、结构化结果与确认状态">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <div v-if="parseTask" class="mb-4">
      <AiTaskStatus :task="parseTask" />
    </div>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div>
          <h2 class="text-sm font-semibold text-slate-700">简历解析批次</h2>
          <p class="mt-1 text-xs text-slate-400">进入简历详情查看该文件的历次解析记录</p>
        </div>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无简历解析记录"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column prop="filename" label="简历文件" min-width="240">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <FileClock :size="17" class="text-blue-500" />
                <span class="font-medium text-slate-700">{{ row.filename }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="关联候选人" min-width="120">
            <template #default="{ row }">
              {{ row.candidate_id ? `#${row.candidate_id}` : '未关联' }}
            </template>
          </el-table-column>
          <el-table-column label="解析状态" width="110">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="210" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="loadRecords(row)">查看记录</el-button>
              <el-button
                v-if="row.status === 'UPLOADED' || row.status === 'FAILED'"
                link
                type="primary"
                :icon="ScanSearch"
                @click="handleParse(row)"
              >
                解析
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

    <el-drawer v-model="drawerVisible" title="解析批次详情" size="760px">
      <div v-loading="recordsLoading">
        <el-alert
          v-if="recordsError"
          :title="recordsError"
          type="error"
          :closable="false"
          show-icon
        />
        <template v-else>
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="font-medium text-slate-700">{{ selectedResume?.filename }}</p>
              <p class="mt-1 text-xs text-slate-400">共 {{ records.length }} 条解析记录</p>
            </div>
            <el-button
              v-if="selectedRecord && selectedRecord.status !== 'CONFIRMED'"
              type="primary"
              @click="confirmVisible = true"
            >
              确认结果
            </el-button>
          </div>

          <el-table
            v-if="records.length > 0"
            :data="records"
            size="small"
            highlight-current-row
            @current-change="selectRecord"
          >
            <el-table-column prop="id" label="记录 ID" width="90" />
            <el-table-column label="AI 任务" width="110">
              <template #default="{ row }">
                {{ row.task_id === null ? '-' : `#${row.task_id}` }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <StatusTag :status="row.status" />
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="100">
              <template #default="{ row }">
                {{ Math.round(row.confidence * 100) }}%
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="160">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无解析记录" :image-size="72" />

          <div v-if="selectedRecord" class="mt-5 border-t border-slate-100 pt-5">
            <ResumeParseViewer :record="selectedRecord" />
          </div>
        </template>
      </div>
    </el-drawer>

    <ParseConfirmDialog
      v-model="confirmVisible"
      :record="selectedRecord"
      @confirmed="handleConfirmed"
    />
  </div>
</template>
