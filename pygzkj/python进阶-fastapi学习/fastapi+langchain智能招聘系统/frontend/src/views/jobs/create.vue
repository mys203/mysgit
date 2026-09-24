<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Save } from 'lucide-vue-next'
import {
  createJob,
  fetchDepartmentOptions,
  fetchJob,
  fetchJobCategories,
  updateJob,
} from '@/api/jobs'
import PageHeader from '@/components/PageHeader.vue'
import type {
  DepartmentOption,
  EmploymentType,
  JobCategory,
  JobCreatePayload,
} from '@/types/job'
import { parsePositiveId } from '@/utils/contracts'
import { getErrorMessage } from '@/utils/error'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const categories = ref<JobCategory[]>([])
const departments = ref<DepartmentOption[]>([])
const skillsText = ref('')

const jobId = computed(() => parsePositiveId(route.query.id))
const isEdit = computed(() => jobId.value !== null)

const form = reactive<JobCreatePayload>({
  title: '',
  code: '',
  category_id: null,
  department_id: null,
  recruiter_id: null,
  description: '',
  requirements: '',
  skills: [],
  location: '',
  employment_type: 'FULL_TIME',
  salary_min: null,
  salary_max: null,
  headcount: 1,
})

const rules: FormRules<JobCreatePayload> = {
  title: [{ required: true, message: '请输入岗位名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入岗位编码', trigger: 'blur' },
    { min: 2, max: 64, message: '岗位编码长度应为 2-64 个字符', trigger: 'blur' },
  ],
  description: [{ required: true, message: '请输入岗位描述', trigger: 'blur' }],
  requirements: [{ required: true, message: '请输入任职要求', trigger: 'blur' }],
  headcount: [{ required: true, message: '请输入招聘人数', trigger: 'change' }],
}

const employmentOptions: Array<{ label: string; value: EmploymentType }> = [
  { label: '全职', value: 'FULL_TIME' },
  { label: '兼职', value: 'PART_TIME' },
  { label: '合同制', value: 'CONTRACT' },
  { label: '实习', value: 'INTERN' },
]

async function loadOptions(): Promise<void> {
  const [categoryResult, departmentResult] = await Promise.allSettled([
    fetchJobCategories(),
    fetchDepartmentOptions(),
  ])

  if (categoryResult.status === 'fulfilled') {
    categories.value = categoryResult.value.items
  }
  if (departmentResult.status === 'fulfilled') {
    departments.value = departmentResult.value
  }
}

async function loadDetail(): Promise<void> {
  if (!jobId.value) {
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const detail = await fetchJob(jobId.value)
    Object.assign(form, {
      title: detail.title,
      code: detail.code,
      category_id: detail.category_id,
      department_id: detail.department_id,
      recruiter_id: detail.recruiter_id,
      description: detail.description,
      requirements: detail.requirements,
      skills: detail.skills,
      location: detail.location,
      employment_type: detail.employment_type,
      salary_min: detail.salary_min,
      salary_max: detail.salary_max,
      headcount: detail.headcount,
    })
    skillsText.value = detail.skills.join('、')
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    loading.value = false
  }
}

async function submit(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  if (
    typeof form.salary_min === 'number' &&
    typeof form.salary_max === 'number' &&
    form.salary_max < form.salary_min
  ) {
    ElMessage.warning('最高薪资不能低于最低薪资')
    return
  }

  const payload: JobCreatePayload = {
    ...form,
    location: form.location || null,
    category_id: form.category_id || null,
    department_id: form.department_id || null,
    recruiter_id: form.recruiter_id || null,
    salary_min: form.salary_min ?? null,
    salary_max: form.salary_max ?? null,
    skills: skillsText.value
      .split(/[、,，\s]+/)
      .map((item) => item.trim())
      .filter(Boolean),
  }

  submitting.value = true

  try {
    if (jobId.value) {
      const { code: _code, ...updatePayload } = payload
      await updateJob(jobId.value, updatePayload)
      ElMessage.success('岗位已更新')
    } else {
      await createJob(payload)
      ElMessage.success('岗位已创建')
    }
    await router.replace('/jobs')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  void loadOptions()
  void loadDetail()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader
      :title="isEdit ? '编辑岗位' : '岗位发布'"
      description="字段与岗位管理契约保持一致"
    >
      <template #actions>
        <el-button :icon="ArrowLeft" @click="router.push('/jobs')">返回列表</el-button>
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

    <section class="panel p-5" v-loading="loading">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="grid gap-x-5 md:grid-cols-2 xl:grid-cols-3">
          <el-form-item label="岗位名称" prop="title">
            <el-input v-model="form.title" placeholder="例如：Python 后端工程师" />
          </el-form-item>
          <el-form-item label="岗位编码" prop="code">
            <el-input
              v-model="form.code"
              :disabled="isEdit"
              placeholder="例如：JOB-PY-001"
            />
          </el-form-item>
          <el-form-item label="岗位分类">
            <el-select v-model="form.category_id" class="w-full" clearable filterable>
              <el-option
                v-for="category in categories"
                :key="category.id"
                :label="`${category.name} · ${category.code}`"
                :value="category.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="所属部门">
            <el-select v-model="form.department_id" class="w-full" clearable filterable>
              <el-option
                v-for="department in departments"
                :key="department.id"
                :label="department.name"
                :value="department.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="工作地点">
            <el-input v-model="form.location" placeholder="例如：上海" />
          </el-form-item>
          <el-form-item label="用工类型">
            <el-select v-model="form.employment_type" class="w-full">
              <el-option
                v-for="option in employmentOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="最低月薪（K）">
            <el-input-number
              v-model="form.salary_min"
              class="w-full"
              :min="0"
              :controls="false"
            />
          </el-form-item>
          <el-form-item label="最高月薪（K）">
            <el-input-number
              v-model="form.salary_max"
              class="w-full"
              :min="0"
              :controls="false"
            />
          </el-form-item>
          <el-form-item label="招聘人数" prop="headcount">
            <el-input-number v-model="form.headcount" class="w-full" :min="1" :max="10000" />
          </el-form-item>
        </div>

        <el-form-item label="技能标签">
          <el-input
            v-model="skillsText"
            placeholder="多个技能使用逗号或顿号分隔，例如：Python、FastAPI、Redis"
          />
        </el-form-item>
        <el-form-item label="岗位描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="7"
            placeholder="请输入岗位职责、工作内容与协作关系"
          />
        </el-form-item>
        <el-form-item label="任职要求" prop="requirements">
          <el-input
            v-model="form.requirements"
            type="textarea"
            :rows="7"
            placeholder="请输入学历、经验、技能和综合素质要求"
          />
        </el-form-item>

        <div class="flex justify-end gap-2 border-t border-slate-100 pt-4">
          <el-button @click="router.push('/jobs')">取消</el-button>
          <el-button type="primary" :icon="Save" :loading="submitting" @click="submit">
            {{ isEdit ? '保存修改' : '创建岗位' }}
          </el-button>
        </div>
      </el-form>
    </section>
  </div>
</template>
