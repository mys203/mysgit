<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshCw, ScanSearch } from 'lucide-vue-next'
import { fetchResumeParseRecords, fetchResumes, parseResume } from '@/api/resumes'
import { fetchAiTask } from '@/api/ai'
import AiTaskStatus from '@/components/AiTaskStatus.vue'
import PageHeader from '@/components/PageHeader.vue'
import ParseConfirmDialog from '@/components/ParseConfirmDialog.vue'
import ResumeParseViewer from '@/components/ResumeParseViewer.vue'
import ResumeUploader from '@/components/ResumeUploader.vue'
import StatusTag from '@/components/StatusTag.vue'
import type {
  ParseConfirmResponse,
  Resume,
  ResumeParseRecord,
  ResumeParseTaskOutput,
} from '@/types/resume'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime } from '@/utils/format'
import { useAiTaskPolling } from '@/utils/aiTaskPolling'

const resumes = ref<Resume[]>([])
const selectedResume = ref<Resume | null>(null)
const records = ref<ResumeParseRecord[]>([])
const selectedRecord = ref<ResumeParseRecord | null>(null)
const loading = ref(false)
const recordsLoading = ref(false)
const parsing = ref(false)
const errorMessage = ref('')
const confirmVisible = ref(false)
const { task: parseTask, start: startParsePolling } =
  useAiTaskPolling<ResumeParseTaskOutput>()

async function loadResumes(): Promise<void> {
  loading.value = true

  try {
    const result = await fetchResumes({
      page: 1,
      page_size: 100,
    })
    resumes.value = result.items
  } finally {
    loading.value = false
  }
}

async function loadRecords(resume: Resume): Promise<void> {
  selectedResume.value = resume
  selectedRecord.value = null
  recordsLoading.value = true
  errorMessage.value = ''

  try {
    const result = await fetchResumeParseRecords(resume.id, {
      page: 1,
      page_size: 50,
    })
    records.value = result.items
    selectedRecord.value = result.items[0] ?? null
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
    records.value = []
  } finally {
    recordsLoading.value = false
  }
}

async function startParse(): Promise<void> {
  if (!selectedResume.value) {
    ElMessage.warning('请先选择需要解析的简历')
    return
  }

  parsing.value = true
  errorMessage.value = ''

  try {
    const accepted = await parseResume(selectedResume.value.id)
    const task = await startParsePolling({
      taskNo: accepted.task_no,
      getTask: (taskNo) => fetchAiTask<ResumeParseTaskOutput>(taskNo),
    })
    await loadRecords(selectedResume.value)
    await loadResumes()
    ElMessage.success(task.degraded ? '简历解析完成，当前使用降级能力' : '简历解析完成')
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    parsing.value = false
  }
}

async function handleConfirmed(result: ParseConfirmResponse): Promise<void> {
  await loadResumes()
  if (selectedResume.value?.id === result.resume_id) {
    await loadRecords(selectedResume.value)
  }
}

function handleUploaded(resume: Resume): void {
  resumes.value = [resume, ...resumes.value.filter((item) => item.id !== resume.id)]
  void loadRecords(resume)
}

onMounted(loadResumes)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="简历深度解析" description="选择简历触发结构化解析，并核对字段">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="loading" @click="loadResumes">
          刷新简历
        </el-button>
        <el-button
          type="primary"
          :icon="ScanSearch"
          :loading="parsing"
          :disabled="!selectedResume"
          @click="startParse"
        >
          开始解析
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
    />

    <div v-if="parseTask" class="mb-4">
      <AiTaskStatus :task="parseTask" />
    </div>

    <div class="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <div class="space-y-4">
        <section class="panel">
          <div class="border-b border-slate-100 px-4 py-3">
            <h2 class="text-sm font-semibold text-slate-700">上传新简历</h2>
          </div>
          <div class="p-4">
            <ResumeUploader @uploaded="handleUploaded" />
          </div>
        </section>

        <section class="panel">
          <div class="border-b border-slate-100 px-4 py-3">
            <h2 class="text-sm font-semibold text-slate-700">简历列表</h2>
          </div>
          <div v-loading="loading" class="max-h-[560px] overflow-y-auto">
            <button
              v-for="resume in resumes"
              :key="resume.id"
              type="button"
              class="flex w-full items-start gap-3 border-b border-slate-100 px-4 py-3 text-left transition hover:bg-slate-50"
              :class="{ 'bg-blue-50/70': selectedResume?.id === resume.id }"
              @click="loadRecords(resume)"
            >
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-blue-50 text-blue-600">
                <ScanSearch :size="16" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium text-slate-700">
                  {{ resume.filename }}
                </span>
                <span class="mt-1 block text-xs text-slate-400">
                  {{ resume.candidate_id ? `候选人 #${resume.candidate_id}` : '未关联候选人' }}
                </span>
              </span>
              <StatusTag :status="resume.status" />
            </button>
            <el-empty v-if="!loading && resumes.length === 0" description="暂无简历" :image-size="72" />
          </div>
        </section>
      </div>

      <section class="panel min-h-[420px] p-5" v-loading="recordsLoading">
        <div v-if="selectedResume" class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-slate-700">{{ selectedResume.filename }}</h2>
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

        <template v-if="selectedResume">
          <el-radio-group
            v-if="records.length > 0"
            v-model="selectedRecord"
            class="mb-4 flex flex-wrap gap-2"
          >
            <el-radio-button
              v-for="record in records"
              :key="record.id"
              :value="record"
            >
              #{{ record.id }} · {{ formatDateTime(record.created_at) }}
            </el-radio-button>
          </el-radio-group>

          <ResumeParseViewer v-if="selectedRecord" :record="selectedRecord" />
          <el-empty
            v-else
            description="该简历暂无解析记录，请点击开始解析"
            :image-size="80"
          />
        </template>

        <el-empty v-else description="请从左侧选择一份简历" :image-size="90" />
      </section>
    </div>

    <ParseConfirmDialog
      v-model="confirmVisible"
      :record="selectedRecord"
      @confirmed="handleConfirmed"
    />
  </div>
</template>
