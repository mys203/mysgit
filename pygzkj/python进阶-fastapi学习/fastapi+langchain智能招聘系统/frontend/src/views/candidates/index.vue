<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Building2, Pencil, Plus, RefreshCw, Trash2, UserRoundSearch } from 'lucide-vue-next'
import {
  createCandidate,
  deleteCandidate,
  fetchCandidates,
  updateCandidate,
} from '@/api/candidates'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePagedList } from '@/composables/usePagedList'
import type {
  Candidate,
  CandidateGender,
  CandidatePayload,
  CandidateStatus,
} from '@/types/candidate'
import { formatDateTime } from '@/utils/format'

interface CandidateFilters extends Record<string, unknown> {
  search: string
  status: CandidateStatus | ''
}

const list = usePagedList<Candidate, CandidateFilters>(fetchCandidates, {
  search: '',
  status: '',
})

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)
const editingId = ref<number | null>(null)
const skillsText = ref('')

const form = reactive<CandidatePayload>({
  name: '',
  email: '',
  phone: '',
  gender: null,
  birth_date: null,
  education: '',
  work_years: 0,
  current_company: '',
  current_title: '',
  skills: [],
  summary: '',
  source: '',
  status: 'ACTIVE',
})

const rules: FormRules<CandidatePayload> = {
  name: [{ required: true, message: '请输入候选人姓名', trigger: 'blur' }],
  phone: [
    {
      pattern: /^1\d{10}$/,
      message: '请输入有效的手机号',
      trigger: 'blur',
    },
  ],
  email: [{ type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }],
}

const genderOptions: Array<{ label: string; value: CandidateGender }> = [
  { label: '男', value: 'MALE' },
  { label: '女', value: 'FEMALE' },
  { label: '其他', value: 'OTHER' },
  { label: '未知', value: 'UNKNOWN' },
]

const statusOptions: Array<{ label: string; value: CandidateStatus }> = [
  { label: '正常', value: 'ACTIVE' },
  { label: '停用', value: 'INACTIVE' },
  { label: '黑名单', value: 'BLACKLIST' },
]

function resetForm(): void {
  editingId.value = null
  skillsText.value = ''
  Object.assign(form, {
    name: '',
    email: '',
    phone: '',
    gender: null,
    birth_date: null,
    education: '',
    work_years: 0,
    current_company: '',
    current_title: '',
    skills: [],
    summary: '',
    source: '',
    status: 'ACTIVE',
  })
  formRef.value?.clearValidate()
}

function openCreate(): void {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Candidate): void {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    email: row.email ?? '',
    phone: row.phone ?? '',
    gender: row.gender,
    birth_date: row.birth_date,
    education: row.education ?? '',
    work_years: row.work_years ?? 0,
    current_company: row.current_company ?? '',
    current_title: row.current_title ?? '',
    skills: row.skills,
    summary: row.summary ?? '',
    source: row.source ?? '',
    status: row.status,
  })
  skillsText.value = row.skills.join('、')
  dialogVisible.value = true
}

async function submit(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  const payload: CandidatePayload = {
    ...form,
    email: form.email || null,
    phone: form.phone || null,
    education: form.education || null,
    current_company: form.current_company || null,
    current_title: form.current_title || null,
    summary: form.summary || null,
    source: form.source || null,
    skills: skillsText.value
      .split(/[、,，\s]+/)
      .map((item) => item.trim())
      .filter(Boolean),
  }

  submitting.value = true

  try {
    if (editingId.value) {
      await updateCandidate(editingId.value, payload)
      ElMessage.success('候选人信息已更新')
    } else {
      await createCandidate(payload)
      ElMessage.success('候选人已创建')
    }
    dialogVisible.value = false
    await list.load()
  } finally {
    submitting.value = false
  }
}

async function removeCandidate(row: Candidate): Promise<void> {
  await ElMessageBox.confirm(`确定删除候选人“${row.name}”吗？`, '删除候选人', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
  await deleteCandidate(row.id)
  ElMessage.success('候选人已删除')
  await list.load()
}

onMounted(list.load)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="候选人列表" description="维护候选人基础档案与技能画像">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增候选人</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div class="filter-row">
          <el-input
            v-model="list.filters.search"
            class="w-64"
            clearable
            placeholder="姓名、手机号或邮箱"
            @keyup.enter="list.search"
          />
          <el-select
            v-model="list.filters.status"
            class="w-32"
            clearable
            placeholder="候选人状态"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-button type="primary" @click="list.search">查询</el-button>
          <el-button @click="list.reset">重置</el-button>
        </div>
        <span class="text-xs text-slate-400">共 {{ list.total.value }} 位候选人</span>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无候选人"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column prop="name" label="姓名" min-width="120" fixed="left">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <span class="flex h-7 w-7 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                  <UserRoundSearch :size="15" />
                </span>
                <span class="font-medium text-slate-700">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" min-width="125">
            <template #default="{ row }">{{ row.phone || '-' }}</template>
          </el-table-column>
          <el-table-column prop="current_title" label="当前职位" min-width="145">
            <template #default="{ row }">{{ row.current_title || '-' }}</template>
          </el-table-column>
          <el-table-column label="当前公司" min-width="160">
            <template #default="{ row }">
              <div class="flex items-center gap-1.5">
                <Building2 :size="14" class="text-slate-400" />
                {{ row.current_company || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="工作年限" width="100">
            <template #default="{ row }">
              {{ row.work_years === null ? '-' : `${row.work_years} 年` }}
            </template>
          </el-table-column>
          <el-table-column label="技能" min-width="190">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag
                  v-for="skill in row.skills.slice(0, 4)"
                  :key="skill"
                  size="small"
                  effect="plain"
                >
                  {{ skill }}
                </el-tag>
                <span v-if="row.skills.length > 4" class="text-xs text-slate-400">
                  +{{ row.skills.length - 4 }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="155">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :icon="Pencil" @click="openEdit(row)">
                编辑
              </el-button>
              <el-button link type="danger" :icon="Trash2" @click="removeCandidate(row)">
                删除
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
      :title="editingId ? '编辑候选人' : '新增候选人'"
      width="680px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="grid gap-x-4 md:grid-cols-2">
          <el-form-item label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="性别">
            <el-select v-model="form.gender" class="w-full" clearable placeholder="请选择">
              <el-option
                v-for="option in genderOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="当前公司">
            <el-input v-model="form.current_company" placeholder="请输入当前公司" />
          </el-form-item>
          <el-form-item label="当前职位">
            <el-input v-model="form.current_title" placeholder="请输入当前职位" />
          </el-form-item>
          <el-form-item label="工作年限">
            <el-input-number
              v-model="form.work_years"
              class="w-full"
              :min="0"
              :max="80"
              :precision="1"
            />
          </el-form-item>
          <el-form-item label="学历">
            <el-input v-model="form.education" placeholder="请输入最高学历" />
          </el-form-item>
          <el-form-item label="候选人状态">
            <el-select v-model="form.status" class="w-full">
              <el-option
                v-for="option in statusOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="候选人来源">
            <el-input v-model="form.source" placeholder="例如：招聘网站、员工推荐" />
          </el-form-item>
        </div>
        <el-form-item label="技能标签">
          <el-input v-model="skillsText" placeholder="多个技能使用逗号或顿号分隔" />
        </el-form-item>
        <el-form-item label="个人摘要">
          <el-input v-model="form.summary" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
