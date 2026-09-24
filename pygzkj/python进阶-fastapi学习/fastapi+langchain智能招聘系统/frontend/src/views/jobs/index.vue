<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleOff, Eye, Pencil, Plus, RefreshCw, Rocket } from 'lucide-vue-next'
import {
  closeJob,
  deleteJob,
  fetchDepartmentOptions,
  fetchJobCategories,
  fetchJobs,
  publishJob,
} from '@/api/jobs'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePagedList } from '@/composables/usePagedList'
import type { DepartmentOption, Job, JobCategory, JobStatus } from '@/types/job'
import { formatDateTime } from '@/utils/format'

interface JobFilters extends Record<string, unknown> {
  search: string
  status: JobStatus | ''
  category_id: number | null
  department_id: number | null
}

const router = useRouter()
const categories = ref<JobCategory[]>([])
const departments = ref<DepartmentOption[]>([])

const list = usePagedList<Job, JobFilters>(fetchJobs, {
  search: '',
  status: '',
  category_id: null,
  department_id: null,
})

const statusOptions: Array<{ label: string; value: JobStatus }> = [
  { label: '草稿', value: 'DRAFT' },
  { label: '招聘中', value: 'PUBLISHED' },
  { label: '已关闭', value: 'CLOSED' },
]

const categoryMap = computed(
  () => new Map(categories.value.map((item) => [item.id, item.name])),
)
const departmentMap = computed(
  () => new Map(departments.value.map((item) => [item.id, item.name])),
)

function formatSalary(job: Job): string {
  if (job.salary_min === null && job.salary_max === null) {
    return '面议'
  }

  if (job.salary_min !== null && job.salary_max !== null) {
    return `${job.salary_min}-${job.salary_max}K`
  }

  return `${job.salary_min ?? job.salary_max}K`
}

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

async function handlePublish(row: Job): Promise<void> {
  await publishJob(row.id)
  ElMessage.success('岗位已发布')
  await list.load()
}

async function handleClose(row: Job): Promise<void> {
  await ElMessageBox.confirm(`确定关闭岗位“${row.title}”吗？`, '关闭岗位', {
    confirmButtonText: '关闭岗位',
    cancelButtonText: '取消',
    type: 'warning',
  })
  await closeJob(row.id)
  ElMessage.success('岗位已关闭')
  await list.load()
}

async function handleDelete(row: Job): Promise<void> {
  await ElMessageBox.confirm(`确定删除岗位“${row.title}”吗？`, '删除岗位', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'error',
  })
  await deleteJob(row.id)
  ElMessage.success('岗位已删除')
  await list.load()
}

onMounted(() => {
  void list.load()
  void loadOptions()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="岗位列表" description="维护岗位信息并控制招聘状态">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
        <el-button type="primary" :icon="Plus" @click="router.push('/jobs/create')">
          发布岗位
        </el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div class="filter-row">
          <el-input
            v-model="list.filters.search"
            class="w-56"
            clearable
            placeholder="岗位名称、编码或地点"
            @keyup.enter="list.search"
          />
          <el-select
            v-model="list.filters.status"
            class="w-32"
            clearable
            placeholder="岗位状态"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-select
            v-model="list.filters.category_id"
            class="w-40"
            clearable
            filterable
            placeholder="岗位分类"
          >
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
          <el-select
            v-model="list.filters.department_id"
            class="w-40"
            clearable
            filterable
            placeholder="所属部门"
          >
            <el-option
              v-for="department in departments"
              :key="department.id"
              :label="department.name"
              :value="department.id"
            />
          </el-select>
          <el-button type="primary" @click="list.search">查询</el-button>
          <el-button @click="list.reset">重置</el-button>
        </div>
        <span class="text-xs text-slate-400">共 {{ list.total.value }} 个岗位</span>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无符合条件的岗位"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column label="岗位" min-width="210" fixed="left">
            <template #default="{ row }">
              <button
                type="button"
                class="text-left font-medium text-blue-600 hover:text-blue-700"
                @click="router.push({ path: '/jobs/create', query: { id: row.id } })"
              >
                {{ row.title }}
              </button>
              <p class="mt-1 font-mono text-xs text-slate-400">{{ row.code }}</p>
            </template>
          </el-table-column>
          <el-table-column label="部门" min-width="120">
            <template #default="{ row }">
              {{ row.department_id ? departmentMap.get(row.department_id) || `#${row.department_id}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="分类" min-width="120">
            <template #default="{ row }">
              {{ row.category_id ? categoryMap.get(row.category_id) || `#${row.category_id}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="地点" min-width="100">
            <template #default="{ row }">{{ row.location || '-' }}</template>
          </el-table-column>
          <el-table-column label="薪资" min-width="110">
            <template #default="{ row }">{{ formatSalary(row) }}</template>
          </el-table-column>
          <el-table-column prop="headcount" label="招聘人数" width="100" />
          <el-table-column label="技能" min-width="180">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag
                  v-for="skill in row.skills.slice(0, 3)"
                  :key="skill"
                  size="small"
                  effect="plain"
                >
                  {{ skill }}
                </el-tag>
                <span v-if="row.skills.length > 3" class="text-xs text-slate-400">
                  +{{ row.skills.length - 3 }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="155">
            <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="272" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                :icon="Eye"
                @click="router.push({ path: '/ai/matches', query: { job_id: row.id } })"
              >
                匹配
              </el-button>
              <el-button
                link
                type="primary"
                :icon="Pencil"
                @click="router.push({ path: '/jobs/create', query: { id: row.id } })"
              >
                编辑
              </el-button>
              <el-button
                v-if="row.status === 'DRAFT'"
                link
                type="success"
                :icon="Rocket"
                @click="handlePublish(row)"
              >
                发布
              </el-button>
              <el-button
                v-if="row.status === 'PUBLISHED'"
                link
                type="warning"
                :icon="CircleOff"
                @click="handleClose(row)"
              >
                关闭
              </el-button>
              <el-button
                v-if="row.status === 'DRAFT'"
                link
                type="danger"
                @click="handleDelete(row)"
              >
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
  </div>
</template>
