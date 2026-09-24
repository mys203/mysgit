<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchJobs } from '@/api/jobs'
import { confirmParseRecord } from '@/api/resumes'
import type { Job } from '@/types/job'
import type {
  ParseConfirmPayload,
  ParseConfirmResponse,
  ResumeParseRecord,
} from '@/types/resume'

const props = defineProps<{
  modelValue: boolean
  record: ResumeParseRecord | null
}>()

const emits = defineEmits<{
  'update:modelValue': [value: boolean]
  confirmed: [result: ParseConfirmResponse]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emits('update:modelValue', value),
})

const jobs = ref<Job[]>([])
const loadingJobs = ref(false)
const submitting = ref(false)
const useOverride = ref(false)
const skillsText = ref('')

const form = reactive<ParseConfirmPayload>({
  candidate_id: null,
  job_position_id: null,
  candidate_override: null,
})

const override = reactive({
  name: '',
  email: '',
  phone: '',
  education: '',
  work_years: 0,
  current_company: '',
  current_title: '',
  summary: '',
})

function resetFromRecord(): void {
  const data = props.record?.parsed_data
  useOverride.value = false
  skillsText.value = data?.skills?.join('、') ?? ''
  Object.assign(override, {
    name: data?.name ?? '',
    email: data?.email ?? '',
    phone: data?.phone ?? '',
    education: data?.education ?? '',
    work_years: data?.work_years ?? 0,
    current_company: data?.current_company ?? '',
    current_title: data?.current_title ?? '',
    summary: data?.summary ?? '',
  })
  Object.assign(form, {
    candidate_id: null,
    job_position_id: null,
    candidate_override: null,
  })
}

async function loadJobs(): Promise<void> {
  if (jobs.value.length > 0) {
    return
  }

  loadingJobs.value = true

  try {
    const result = await fetchJobs({
      status: 'PUBLISHED',
      page: 1,
      page_size: 100,
    })
    jobs.value = result.items
  } finally {
    loadingJobs.value = false
  }
}

async function submit(): Promise<void> {
  if (!props.record) {
    return
  }

  submitting.value = true

  try {
    const result = await confirmParseRecord(props.record.id, {
      candidate_id: form.candidate_id || null,
      job_position_id: form.job_position_id || null,
      candidate_override: useOverride.value
        ? {
            name: override.name || null,
            email: override.email || null,
            phone: override.phone || null,
            education: override.education || null,
            work_years: override.work_years,
            current_company: override.current_company || null,
            current_title: override.current_title || null,
            skills: skillsText.value
              .split(/[、,，\s]+/)
              .map((item) => item.trim())
              .filter(Boolean),
            summary: override.summary || null,
          }
        : null,
    })
    ElMessage.success('解析结果已确认')
    emits('confirmed', result)
    visible.value = false
  } finally {
    submitting.value = false
  }
}

watch(
  () => [props.modelValue, props.record?.id],
  ([isVisible]) => {
    if (isVisible) {
      resetFromRecord()
      void loadJobs()
    }
  },
)
</script>

<template>
  <el-dialog v-model="visible" title="确认解析结果" width="760px" destroy-on-close>
    <el-form label-position="top">
      <div class="grid gap-x-4 md:grid-cols-2">
        <el-form-item label="关联岗位">
          <el-select
            v-model="form.job_position_id"
            class="w-full"
            clearable
            filterable
            :loading="loadingJobs"
            placeholder="可选，确认后自动创建应聘记录"
          >
            <el-option
              v-for="job in jobs"
              :key="job.id"
              :label="`${job.title} · ${job.code}`"
              :value="job.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="已有候选人 ID">
          <el-input-number
            v-model="form.candidate_id"
            class="w-full"
            :min="1"
            :controls="false"
            placeholder="可选，留空则自动匹配或创建"
          />
        </el-form-item>
      </div>

      <el-divider content-position="left">
        <el-checkbox v-model="useOverride">人工修正候选人字段</el-checkbox>
      </el-divider>

      <div v-if="useOverride" class="grid gap-x-4 md:grid-cols-2">
        <el-form-item label="姓名">
          <el-input v-model="override.name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="override.email" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="override.phone" />
        </el-form-item>
        <el-form-item label="学历">
          <el-input v-model="override.education" />
        </el-form-item>
        <el-form-item label="工作年限">
          <el-input-number v-model="override.work_years" class="w-full" :min="0" :max="80" />
        </el-form-item>
        <el-form-item label="当前公司">
          <el-input v-model="override.current_company" />
        </el-form-item>
        <el-form-item label="当前职位">
          <el-input v-model="override.current_title" />
        </el-form-item>
        <el-form-item label="技能">
          <el-input v-model="skillsText" placeholder="使用逗号或顿号分隔" />
        </el-form-item>
        <el-form-item label="个人摘要" class="md:col-span-2">
          <el-input v-model="override.summary" type="textarea" :rows="3" />
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">
        确认并保存
      </el-button>
    </template>
  </el-dialog>
</template>
