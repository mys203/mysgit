<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Pencil, RefreshCw, Sparkles } from 'lucide-vue-next'
import {
  createInterviewQuestions,
  fetchAiTask,
  fetchInterviewQuestions,
  updateInterviewQuestion,
} from '@/api/ai'
import { fetchCandidates } from '@/api/candidates'
import { fetchJobs } from '@/api/jobs'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusTag from '@/components/StatusTag.vue'
import AiTaskStatus from '@/components/AiTaskStatus.vue'
import { usePagedList } from '@/composables/usePagedList'
import type {
  InterviewQuestion,
  InterviewQuestionTaskOutput,
  InterviewQuestionPayload,
  InterviewQuestionUpdate,
  QuestionStatus,
} from '@/types/ai'
import type { Candidate } from '@/types/candidate'
import type { Job } from '@/types/job'
import { getErrorMessage } from '@/utils/error'
import { useAiTaskPolling } from '@/utils/aiTaskPolling'

interface QuestionFilters extends Record<string, unknown> {
  interview_id?: number
  category: string
  status: QuestionStatus | ''
}

const list = usePagedList<InterviewQuestion, QuestionFilters>(fetchInterviewQuestions, {
  category: '',
  status: '',
})

const jobs = ref<Job[]>([])
const candidates = ref<Candidate[]>([])
const generating = ref(false)
const editVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const errorMessage = ref('')
const { task: generationTask, start: startGenerationPolling } =
  useAiTaskPolling<InterviewQuestionTaskOutput>()

const form = reactive<InterviewQuestionPayload>({
  job_id: 0,
  candidate_id: null,
  interview_id: null,
  count: 5,
  categories: ['专业知识', '项目经历', '行为面试'],
})

const editForm = reactive<InterviewQuestionUpdate>({
  question: '',
  category: '',
  reference_answer: '',
  score_weight: 1,
  status: 'DRAFT',
})

async function loadOptions(): Promise<void> {
  const [jobResult, candidateResult] = await Promise.allSettled([
    fetchJobs({ status: 'PUBLISHED', page: 1, page_size: 100 }),
    fetchCandidates({ page: 1, page_size: 100 }),
  ])
  if (jobResult.status === 'fulfilled') {
    jobs.value = jobResult.value.items
  }
  if (candidateResult.status === 'fulfilled') {
    candidates.value = candidateResult.value.items
  }
}

async function generate(): Promise<void> {
  if (!form.job_id) {
    ElMessage.warning('请选择目标岗位')
    return
  }

  if (form.categories.length === 0) {
    ElMessage.warning('请至少选择一个题目分类')
    return
  }

  generating.value = true
  errorMessage.value = ''

  try {
    const accepted = await createInterviewQuestions({
      ...form,
      candidate_id: form.candidate_id || null,
      interview_id: form.interview_id || null,
    })
    const task = await startGenerationPolling({
      taskNo: accepted.task_no,
      getTask: (taskNo) => fetchAiTask<InterviewQuestionTaskOutput>(taskNo),
    })
    const output = task.output_payload
    if (!output) {
      throw new Error('面试题任务成功但未返回结果')
    }
    await list.load()
    ElMessage.success(output.degraded ? '面试题生成完成，当前使用降级能力' : '面试题生成完成')
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    generating.value = false
  }
}

function openEdit(question: InterviewQuestion): void {
  editingId.value = question.id
  Object.assign(editForm, {
    question: question.question,
    category: question.category,
    reference_answer: question.reference_answer ?? '',
    score_weight: question.score_weight,
    status: question.status,
  })
  editVisible.value = true
}

async function saveQuestion(): Promise<void> {
  if (!editingId.value) {
    return
  }

  saving.value = true

  try {
    const result = await updateInterviewQuestion(editingId.value, {
      ...editForm,
      reference_answer: editForm.reference_answer || undefined,
    })
    list.items.value = list.items.value.map((item) => (item.id === result.id ? result : item))
    ElMessage.success('面试题已更新')
    editVisible.value = false
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void list.load()
  void loadOptions()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="面试题生成" description="按岗位与候选人画像生成结构化面试题">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新题库
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

    <section class="panel p-5">
      <div class="grid items-end gap-4 xl:grid-cols-4">
        <el-form-item label="目标岗位" class="mb-0">
          <el-select v-model="form.job_id" class="w-full" filterable placeholder="请选择岗位">
            <el-option
              v-for="job in jobs"
              :key="job.id"
              :label="job.title"
              :value="job.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="候选人" class="mb-0">
          <el-select
            v-model="form.candidate_id"
            class="w-full"
            clearable
            filterable
            placeholder="可选"
          >
            <el-option
              v-for="candidate in candidates"
              :key="candidate.id"
              :label="candidate.name"
              :value="candidate.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="题目分类" class="mb-0">
          <el-select
            v-model="form.categories"
            class="w-full"
            multiple
            collapse-tags
            collapse-tags-tooltip
            allow-create
            filterable
          >
            <el-option label="专业知识" value="专业知识" />
            <el-option label="项目经历" value="项目经历" />
            <el-option label="行为面试" value="行为面试" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成数量" class="mb-0">
          <el-input-number v-model="form.count" class="w-full" :min="1" :max="20" />
        </el-form-item>
      </div>
      <div class="flex justify-end">
        <el-button
          type="primary"
          :icon="Sparkles"
          :loading="generating"
          @click="generate"
        >
          生成面试题
        </el-button>
      </div>
    </section>

    <div v-if="generationTask || generating" class="mt-4">
      <AiTaskStatus :task="generationTask" />
    </div>

    <section class="panel mt-4">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div class="filter-row">
          <el-input
            v-model="list.filters.category"
            class="w-40"
            clearable
            placeholder="题目分类"
          />
          <el-select
            v-model="list.filters.status"
            class="w-32"
            clearable
            placeholder="状态"
          >
            <el-option label="草稿" value="DRAFT" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已拒绝" value="REJECTED" />
          </el-select>
          <el-button type="primary" @click="list.search">查询</el-button>
          <el-button @click="list.reset">重置</el-button>
        </div>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无面试题"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column prop="question" label="面试题" min-width="340">
            <template #default="{ row }">
              <p class="line-clamp-2 leading-6 text-slate-700">{{ row.question }}</p>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="110" />
          <el-table-column prop="score_weight" label="评分权重" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="generated_by" label="生成方式" min-width="130" />
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :icon="Pencil" @click="openEdit(row)">
                编辑
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

    <el-dialog v-model="editVisible" title="编辑面试题" width="720px">
      <el-form :model="editForm" label-position="top">
        <el-form-item label="题目分类">
          <el-input v-model="editForm.category" />
        </el-form-item>
        <el-form-item label="题干">
          <el-input v-model="editForm.question" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="参考答案">
          <el-input v-model="editForm.reference_answer" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="评分权重">
          <el-input-number
            v-model="editForm.score_weight"
            class="w-full"
            :min="0.1"
            :max="10"
            :step="0.1"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" class="w-full">
            <el-option label="草稿" value="DRAFT" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已拒绝" value="REJECTED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveQuestion">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
</style>
