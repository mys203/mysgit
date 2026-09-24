<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Eye, FileSearch, RefreshCw, ScanSearch, Upload } from 'lucide-vue-next'
import {
  fetchResume,
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
  ResumeDetail,
  ResumeParseRecord,
  ResumeParseTaskOutput,
} from '@/types/resume'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime, formatFileSize } from '@/utils/format'
import { useAiTaskPolling } from '@/utils/aiTaskPolling'

type ResumeFilters = Record<string, unknown>

const router = useRouter()
const list = usePagedList<Resume, ResumeFilters>(fetchResumes, {})
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailError = ref('')
const selectedResume = ref<ResumeDetail | null>(null)
const parseRecords = ref<ResumeParseRecord[]>([])
const selectedRecord = ref<ResumeParseRecord | null>(null)
const confirmVisible = ref(false)
const { task: parseTask, start: startParsePolling } =
  useAiTaskPolling<ResumeParseTaskOutput>()

async function loadRecords(resumeId: number): Promise<void> {
  const records = await fetchResumeParseRecords(resumeId, {
    page: 1,
    page_size: 50,
  })
  parseRecords.value = records.items
  selectedRecord.value = records.items[0] ?? null
}

async function showDetail(row: Resume): Promise<void> {
  detailVisible.value = true
  detailLoading.value = true
  detailError.value = ''
  selectedRecord.value = null

  try {
    const [resume, records] = await Promise.all([
      fetchResume(row.id),
      fetchResumeParseRecords(row.id, { page: 1, page_size: 50 }),
    ])
    selectedResume.value = resume
    parseRecords.value = records.items
    selectedRecord.value = records.items[0] ?? null
  } catch (error) {
    detailError.value = getErrorMessage(error)
    selectedResume.value = null
    parseRecords.value = []
  } finally {
    detailLoading.value = false
  }
}

async function handleParse(row: Resume): Promise<void> {
  const accepted = await parseResume(row.id)
  const task = await startParsePolling({
    taskNo: accepted.task_no,
    getTask: (taskNo) => fetchAiTask<ResumeParseTaskOutput>(taskNo),
  })
  await list.load()
  if (detailVisible.value && selectedResume.value?.id === row.id) {
    await loadRecords(row.id)
  }
  ElMessage.success(task.degraded ? '简历解析完成，当前使用降级能力' : '简历解析完成')
}

async function handleConfirmed(result: ParseConfirmResponse): Promise<void> {
  await list.load()
  await loadRecords(result.resume_id)
  if (selectedResume.value?.id === result.resume_id) {
    selectedResume.value = await fetchResume(result.resume_id)
  }
}

onMounted(list.load)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="简历库" description="管理已入库简历并跟踪解析状态">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
        <el-button type="primary" :icon="Upload" @click="router.push('/resumes/upload')">
          上传简历
        </el-button>
      </template>
    </PageHeader>

    <div v-if="parseTask" class="mb-4">
      <AiTaskStatus :task="parseTask" />
    </div>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div>
          <h2 class="text-sm font-semibold text-slate-700">简历文件</h2>
          <p class="mt-1 text-xs text-slate-400">接口按上传时间倒序分页返回</p>
        </div>
        <span class="text-xs text-slate-400">共 {{ list.total.value }} 份简历</span>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无简历数据"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column prop="filename" label="简历文件" min-width="240" fixed="left">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <FileSearch :size="17" class="shrink-0 text-blue-500" />
                <button
                  type="button"
                  class="truncate text-left font-medium text-slate-700 hover:text-blue-600"
                  @click="showDetail(row)"
                >
                  {{ row.filename }}
                </button>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="file_type" label="文件类型" width="100">
            <template #default="{ row }">{{ row.file_type.toUpperCase() }}</template>
          </el-table-column>
          <el-table-column label="关联候选人" width="120">
            <template #default="{ row }">
              {{ row.candidate_id ? `#${row.candidate_id}` : '未关联' }}
            </template>
          </el-table-column>
          <el-table-column label="文件大小" width="105">
            <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
          </el-table-column>
          <el-table-column prop="file_hash" label="文件指纹" min-width="180">
            <template #default="{ row }">
              <span class="font-mono text-xs text-slate-500">
                {{ row.file_hash.slice(0, 16) }}...
              </span>
            </template>
          </el-table-column>
          <el-table-column label="解析状态" width="110">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="入库时间" width="155">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :icon="Eye" @click="showDetail(row)">
                详情
              </el-button>
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

    <el-drawer v-model="detailVisible" title="简历详情" size="720px">
      <div v-loading="detailLoading">
        <el-alert
          v-if="detailError"
          :title="detailError"
          type="error"
          :closable="false"
          show-icon
        />

        <template v-else-if="selectedResume">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="文件名" :span="2">
              {{ selectedResume.filename }}
            </el-descriptions-item>
            <el-descriptions-item label="文件类型">
              {{ selectedResume.file_type.toUpperCase() }}
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ formatFileSize(selectedResume.file_size) }}
            </el-descriptions-item>
            <el-descriptions-item label="候选人">
              {{ selectedResume.candidate_id ? `#${selectedResume.candidate_id}` : '未关联' }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <StatusTag :status="selectedResume.status" />
            </el-descriptions-item>
          </el-descriptions>

          <div class="mt-5">
            <div class="mb-3 flex items-center justify-between gap-3">
              <h3 class="text-sm font-semibold text-slate-700">解析记录</h3>
              <el-button
                v-if="selectedRecord && selectedRecord.status !== 'CONFIRMED'"
                type="primary"
                size="small"
                @click="confirmVisible = true"
              >
                确认结果
              </el-button>
            </div>
            <el-radio-group
              v-if="parseRecords.length > 0"
              v-model="selectedRecord"
              class="mb-3 flex flex-wrap gap-2"
            >
              <el-radio-button
                v-for="record in parseRecords"
                :key="record.id"
                :value="record"
              >
                #{{ record.id }} · {{ formatDateTime(record.created_at) }}
              </el-radio-button>
            </el-radio-group>
            <ResumeParseViewer v-if="selectedRecord" :record="selectedRecord" />
            <el-empty v-else description="暂无解析记录" :image-size="72" />
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
