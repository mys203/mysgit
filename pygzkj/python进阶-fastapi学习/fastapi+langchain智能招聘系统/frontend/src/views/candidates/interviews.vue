<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CalendarPlus, Pencil, RefreshCw, UserPlus, XCircle } from 'lucide-vue-next'
import {
  addInterviewParticipant,
  cancelInterview,
  createInterview,
  fetchInterviews,
  submitInterviewFeedback,
  updateInterview,
} from '@/api/ai'
import { fetchCandidates } from '@/api/candidates'
import { fetchJobs } from '@/api/jobs'
import { fetchUserOptions } from '@/api/system'
import { PERMISSIONS } from '@/constants/permissions'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePagedList } from '@/composables/usePagedList'
import type {
  Interview,
  InterviewFeedbackPayload,
  InterviewPayload,
  InterviewStatus,
} from '@/types/ai'
import type { Candidate } from '@/types/candidate'
import type { Job } from '@/types/job'
import type { UserOption } from '@/types/system'
import { formatDateTime } from '@/utils/format'
import { buildInterviewUpdatePayload } from '@/utils/contracts'
import { useAuthStore } from '@/stores/auth'

interface InterviewFilters extends Record<string, unknown> {
  status: InterviewStatus | ''
}

const list = usePagedList<Interview, InterviewFilters>(fetchInterviews, {
  status: '',
})

const authStore = useAuthStore()
const candidates = ref<Candidate[]>([])
const jobs = ref<Job[]>([])
const users = ref<UserOption[]>([])
const dialogVisible = ref(false)
const feedbackVisible = ref(false)
const participantVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const feedbackFormRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const currentInterview = ref<Interview | null>(null)
const participantForm = reactive<{
  user_id: number
  participant_role: 'INTERVIEWER' | 'OBSERVER' | 'COORDINATOR'
}>({
  user_id: 0,
  participant_role: 'INTERVIEWER',
})

const form = reactive<InterviewPayload>({
  job_id: 0,
  candidate_id: 0,
  application_id: null,
  interviewer_id: null,
  title: '',
  round_no: 1,
  mode: 'VIDEO',
  scheduled_at: '',
  duration_minutes: 60,
  location: '',
  meeting_url: '',
})

const feedbackForm = reactive<InterviewFeedbackPayload>({
  feedback: '',
  score: 80,
  status: 'COMPLETED',
})

const rules: FormRules<InterviewPayload> = {
  candidate_id: [{ required: true, message: '请选择候选人', trigger: 'change' }],
  job_id: [{ required: true, message: '请选择应聘岗位', trigger: 'change' }],
  title: [{ required: true, message: '请输入面试标题', trigger: 'blur' }],
  mode: [{ required: true, message: '请选择面试方式', trigger: 'change' }],
  scheduled_at: [{ required: true, message: '请选择面试时间', trigger: 'change' }],
}

const feedbackRules: FormRules<InterviewFeedbackPayload> = {
  feedback: [{ required: true, message: '请输入面试反馈', trigger: 'blur' }],
  status: [{ required: true, message: '请选择反馈状态', trigger: 'change' }],
}

const canManageInterviews = computed(() =>
  authStore.canAccess(PERMISSIONS.INTERVIEWS_MANAGE),
)
const canScheduleInterviews = computed(() =>
  authStore.canAccess(PERMISSIONS.INTERVIEWS_SCHEDULE),
)
const canWriteInterviews = computed(() =>
  authStore.canAccess(PERMISSIONS.INTERVIEWS_WRITE),
)

const jobMap = computed(() => new Map(jobs.value.map((item) => [item.id, item.title])))
const candidateMap = computed(
  () => new Map(candidates.value.map((item) => [item.id, item.name])),
)
const userMap = computed(
  () => new Map(users.value.map((item) => [item.id, item.real_name || item.username])),
)

async function loadOptions(): Promise<void> {
  const [candidateResult, jobResult, userResult] = await Promise.allSettled([
    fetchCandidates({ page: 1, page_size: 100 }),
    fetchJobs({ page: 1, page_size: 100 }),
    fetchUserOptions({ role_code: 'INTERVIEWER', limit: 200 }),
  ])

  if (candidateResult.status === 'fulfilled') {
    candidates.value = candidateResult.value.items
  }
  if (jobResult.status === 'fulfilled') {
    jobs.value = jobResult.value.items
  }
  if (userResult.status === 'fulfilled') {
    users.value = userResult.value
  }
}

function resetForm(): void {
  editingId.value = null
  Object.assign(form, {
    job_id: 0,
    candidate_id: 0,
    application_id: null,
    interviewer_id: null,
    title: '',
    round_no: 1,
    mode: 'VIDEO',
    scheduled_at: '',
    duration_minutes: 60,
    location: '',
    meeting_url: '',
  })
  formRef.value?.clearValidate()
}

function openCreate(): void {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Interview): void {
  editingId.value = row.id
  Object.assign(form, {
    job_id: row.job_id,
    candidate_id: row.candidate_id,
    application_id: row.application_id,
    interviewer_id: row.interviewer_id,
    title: row.title,
    round_no: row.round_no,
    mode: row.mode,
    scheduled_at: row.scheduled_at,
    duration_minutes: row.duration_minutes,
    location: row.location ?? '',
    meeting_url: row.meeting_url ?? '',
  })
  dialogVisible.value = true
}

async function submit(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  const payload: InterviewPayload = {
    ...form,
    location: form.location || null,
    meeting_url: form.meeting_url || null,
  }
  submitting.value = true

  try {
    if (editingId.value) {
      await updateInterview(editingId.value, buildInterviewUpdatePayload(payload))
      ElMessage.success('面试安排已更新')
    } else {
      await createInterview(payload)
      ElMessage.success('面试已安排')
    }
    dialogVisible.value = false
    await list.load()
  } finally {
    submitting.value = false
  }
}

async function handleCancel(row: Interview): Promise<void> {
  const reason = await ElMessageBox.prompt('请输入取消原因', '取消面试', {
    confirmButtonText: '确认取消',
    cancelButtonText: '返回',
    inputValidator: (value) => Boolean(value.trim()) || '请输入取消原因',
  })
  await cancelInterview(row.id, reason.value.trim())
  ElMessage.success('面试已取消')
  await list.load()
}

function openFeedback(row: Interview): void {
  currentInterview.value = row
  Object.assign(feedbackForm, {
    feedback: '',
    score: 80,
    status: 'COMPLETED',
  })
  feedbackVisible.value = true
}

async function submitFeedback(): Promise<void> {
  if (!currentInterview.value) {
    return
  }

  const valid = await feedbackFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  submitting.value = true

  try {
    await submitInterviewFeedback(currentInterview.value.id, feedbackForm)
    ElMessage.success('面试反馈已提交')
    feedbackVisible.value = false
    await list.load()
  } finally {
    submitting.value = false
  }
}

function openParticipant(row: Interview): void {
  currentInterview.value = row
  participantForm.user_id = 0
  participantForm.participant_role = 'INTERVIEWER'
  participantVisible.value = true
}

async function submitParticipant(): Promise<void> {
  if (!currentInterview.value || !participantForm.user_id) {
    ElMessage.warning('请选择面试参与人')
    return
  }

  submitting.value = true

  try {
    await addInterviewParticipant(
      currentInterview.value.id,
      participantForm.user_id,
      participantForm.participant_role,
    )
    ElMessage.success('面试参与人已添加')
    participantVisible.value = false
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  void list.load()
  void loadOptions()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="面试安排" description="安排面试、维护面试官并记录反馈">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
        <el-button
          v-if="canScheduleInterviews"
          type="primary"
          :icon="CalendarPlus"
          @click="openCreate"
        >
          安排面试
        </el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <el-select
          v-model="list.filters.status"
          class="w-36"
          clearable
          placeholder="面试状态"
        >
          <el-option label="已安排" value="SCHEDULED" />
          <el-option label="进行中" value="IN_PROGRESS" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="已取消" value="CANCELLED" />
        </el-select>
        <el-button type="primary" @click="list.search">查询</el-button>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无面试安排"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column prop="title" label="面试标题" min-width="180" />
          <el-table-column label="候选人" min-width="120">
            <template #default="{ row }">
              {{ candidateMap.get(row.candidate_id) || `候选人 #${row.candidate_id}` }}
            </template>
          </el-table-column>
          <el-table-column label="应聘岗位" min-width="190">
            <template #default="{ row }">
              {{ jobMap.get(row.job_id) || `岗位 #${row.job_id}` }}
            </template>
          </el-table-column>
          <el-table-column prop="round_no" label="轮次" width="80" />
          <el-table-column label="方式" width="100">
            <template #default="{ row }">
              {{ row.mode === 'VIDEO' ? '视频面试' : row.mode === 'PHONE' ? '电话面试' : '现场面试' }}
            </template>
          </el-table-column>
          <el-table-column label="面试时间" width="165">
            <template #default="{ row }">{{ formatDateTime(row.scheduled_at) }}</template>
          </el-table-column>
          <el-table-column label="面试官" min-width="130">
            <template #default="{ row }">
              {{ row.interviewer_id ? userMap.get(row.interviewer_id) || `用户 #${row.interviewer_id}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="210" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="canManageInterviews && (row.status === 'SCHEDULED' || row.status === 'IN_PROGRESS')"
                link
                type="primary"
                :icon="Pencil"
                @click="openEdit(row)"
              >
                改期
              </el-button>
              <el-button
                v-if="canWriteInterviews && (row.status === 'SCHEDULED' || row.status === 'IN_PROGRESS')"
                link
                type="success"
                @click="openFeedback(row)"
              >
                反馈
              </el-button>
              <el-button
                v-if="canManageInterviews && row.status === 'SCHEDULED'"
                link
                type="danger"
                :icon="XCircle"
                @click="handleCancel(row)"
              >
                取消
              </el-button>
              <el-button
                v-if="canScheduleInterviews && row.status !== 'CANCELLED'"
                link
                type="primary"
                :icon="UserPlus"
                @click="openParticipant(row)"
              >
                参与人
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

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '调整面试安排' : '安排面试'"
      width="700px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="grid gap-x-4 md:grid-cols-2">
          <el-form-item label="候选人" prop="candidate_id">
            <el-select v-model="form.candidate_id" class="w-full" filterable placeholder="请选择候选人">
              <el-option
                v-for="candidate in candidates"
                :key="candidate.id"
                :label="`${candidate.name} · ${candidate.phone || '无手机号'}`"
                :value="candidate.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="应聘岗位" prop="job_id">
            <el-select v-model="form.job_id" class="w-full" filterable placeholder="请选择岗位">
              <el-option
                v-for="job in jobs"
                :key="job.id"
                :label="job.title"
                :value="job.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="面试标题" prop="title">
            <el-input v-model="form.title" placeholder="例如：后端工程师一面" />
          </el-form-item>
          <el-form-item label="面试轮次">
            <el-input-number v-model="form.round_no" class="w-full" :min="1" :max="20" />
          </el-form-item>
          <el-form-item label="面试方式" prop="mode">
            <el-select v-model="form.mode" class="w-full">
              <el-option label="视频面试" value="VIDEO" />
              <el-option label="现场面试" value="OFFLINE" />
              <el-option label="电话面试" value="PHONE" />
            </el-select>
          </el-form-item>
          <el-form-item label="面试时间" prop="scheduled_at">
            <el-date-picker
              v-model="form.scheduled_at"
              class="w-full"
              type="datetime"
              value-format="YYYY-MM-DDTHH:mm:ss"
              placeholder="请选择面试时间"
            />
          </el-form-item>
          <el-form-item label="预计时长">
            <el-input-number
              v-model="form.duration_minutes"
              class="w-full"
              :min="15"
              :max="720"
              :step="15"
            />
          </el-form-item>
          <el-form-item label="面试官">
            <el-select
              v-model="form.interviewer_id"
              class="w-full"
              clearable
              filterable
              placeholder="请选择面试官"
            >
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="user.real_name || user.username"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="面试地点">
          <el-input v-model="form.location" placeholder="现场面试时填写" />
        </el-form-item>
        <el-form-item label="会议链接">
          <el-input v-model="form.meeting_url" placeholder="视频面试时填写" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="feedbackVisible" title="面试反馈" width="560px">
      <el-form
        ref="feedbackFormRef"
        :model="feedbackForm"
        :rules="feedbackRules"
        label-position="top"
      >
        <el-form-item label="反馈状态" prop="status">
          <el-select v-model="feedbackForm.status" class="w-full">
            <el-option label="已完成" value="COMPLETED" />
            <el-option label="已确认" value="CONFIRMED" />
            <el-option label="已拒绝" value="DECLINED" />
          </el-select>
        </el-form-item>
        <el-form-item label="面试评分">
          <el-slider v-model="feedbackForm.score" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="反馈意见" prop="feedback">
          <el-input
            v-model="feedbackForm.feedback"
            type="textarea"
            :rows="5"
            placeholder="请输入能力表现、风险点与后续建议"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitFeedback">
          提交反馈
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="participantVisible" title="添加面试参与人" width="480px">
      <el-form label-position="top">
        <el-form-item label="系统用户">
          <el-select
            v-model="participantForm.user_id"
            class="w-full"
            filterable
            placeholder="请选择参与人"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.real_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="参与角色">
          <el-select v-model="participantForm.participant_role" class="w-full">
            <el-option label="面试官" value="INTERVIEWER" />
            <el-option label="观察者" value="OBSERVER" />
            <el-option label="协调人" value="COORDINATOR" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="participantVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitParticipant">
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
