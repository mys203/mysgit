<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CircleOff,
  CirclePlay,
  Pencil,
  Plus,
  RefreshCw,
  ShieldCheck,
  Trash2,
  UserRound,
} from 'lucide-vue-next'
import {
  createUser,
  deleteUser,
  fetchRoles,
  fetchUser,
  fetchUsers,
  updateUser,
} from '@/api/system'
import { fetchDepartmentOptions } from '@/api/jobs'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusTag from '@/components/StatusTag.vue'
import { usePagedList } from '@/composables/usePagedList'
import { useAuthStore } from '@/stores/auth'
import type { DepartmentOption } from '@/types/job'
import type {
  Role,
  SystemUser,
  UserStatus,
} from '@/types/system'
import { formatDateTime } from '@/utils/format'
import {
  buildUserCreatePayload,
  buildUserUpdatePayload,
  canManageUsers,
  createEmptyUserForm,
  getRoleDisplayName,
  toUserForm,
  type UserFormModel,
} from '@/utils/users'

interface UserFilters extends Record<string, unknown> {
  search: string
  status: UserStatus | ''
}

type UserAction = 'edit' | 'toggle' | 'delete'

interface ActiveAction {
  id: number
  type: UserAction
}

const authStore = useAuthStore()
const list = usePagedList<SystemUser, UserFilters>(fetchUsers, {
  search: '',
  status: '',
})

const departments = ref<DepartmentOption[]>([])
const roles = ref<Role[]>([])
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const submitting = ref(false)
const editingUser = ref<SystemUser | null>(null)
const activeAction = ref<ActiveAction | null>(null)

const form = reactive<UserFormModel>(createEmptyUserForm())

const canManage = computed(() =>
  canManageUsers(authStore.user?.roles, authStore.user?.permissions),
)
const isEditing = computed(() => editingUser.value !== null)
const dialogTitle = computed(() => (isEditing.value ? '编辑用户' : '新建用户'))
const departmentMap = computed(
  () => new Map(departments.value.map((item) => [item.id, item.name])),
)
const roleNameMap = computed(
  () => new Map(roles.value.map((item) => [item.code, item.name])),
)
const selectableRoles = computed(() =>
  roles.value.filter((role) => role.status === 'ACTIVE'),
)

const formRules: FormRules<UserFormModel> = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 64, message: '账号长度应为 3-64 个字符', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_.-]+$/,
      message: '账号仅支持字母、数字、下划线、点和短横线',
      trigger: 'blur',
    },
  ],
  password: [
    {
      validator: (_rule, value, callback) => {
        const password = typeof value === 'string' ? value : ''
        if (!isEditing.value && !password) {
          callback(new Error('请输入密码'))
          return
        }
        if (password && password.length < 8) {
          callback(new Error('密码至少 8 位'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  real_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { max: 100, message: '姓名不能超过 100 个字符', trigger: 'blur' },
  ],
  email: [
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
      trigger: ['blur', 'change'],
    },
    { max: 255, message: '邮箱不能超过 255 个字符', trigger: 'blur' },
  ],
  phone: [
    { max: 32, message: '手机号不能超过 32 个字符', trigger: 'blur' },
  ],
  role_codes: [
    {
      type: 'array',
      required: true,
      min: 1,
      max: 5,
      message: '请选择 1-5 个角色',
      trigger: 'change',
    },
  ],
  status: [{ required: true, message: '请选择账号状态', trigger: 'change' }],
}

async function loadOptions(): Promise<void> {
  const [roleResult, departmentResult] = await Promise.allSettled([
    fetchRoles(),
    fetchDepartmentOptions(),
  ])

  if (roleResult.status === 'fulfilled') {
    roles.value = roleResult.value.items
  }

  if (departmentResult.status === 'fulfilled') {
    departments.value = departmentResult.value
  }
}

function openCreateDialog(): void {
  if (activeAction.value) {
    return
  }

  editingUser.value = null
  Object.assign(form, createEmptyUserForm())
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

async function openEditDialog(row: SystemUser): Promise<void> {
  if (activeAction.value) {
    return
  }

  activeAction.value = { id: row.id, type: 'edit' }

  try {
    const detail = await fetchUser(row.id)
    editingUser.value = detail
    Object.assign(form, toUserForm(detail))
    dialogVisible.value = true
    formRef.value?.clearValidate()
  } finally {
    activeAction.value = null
  }
}

async function submitUser(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid || submitting.value) {
    return
  }

  submitting.value = true

  try {
    if (editingUser.value) {
      await updateUser(editingUser.value.id, buildUserUpdatePayload(form))
      ElMessage.success('用户已更新')
    } else {
      await createUser(buildUserCreatePayload(form))
      ElMessage.success('用户已创建')
    }

    dialogVisible.value = false
    await list.load()
  } finally {
    submitting.value = false
  }
}

async function toggleUserStatus(row: SystemUser): Promise<void> {
  if (activeAction.value) {
    return
  }

  const nextStatus: UserStatus = row.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
  const actionText = nextStatus === 'ACTIVE' ? '启用' : '停用'

  if (nextStatus === 'INACTIVE') {
    try {
      await ElMessageBox.confirm(
        `确定停用用户“${row.real_name || row.username}”吗？`,
        '停用用户',
        {
          confirmButtonText: '停用',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    } catch {
      return
    }
  }

  activeAction.value = { id: row.id, type: 'toggle' }

  try {
    await updateUser(row.id, { status: nextStatus })
    ElMessage.success(`用户已${actionText}`)
    await list.load()
  } finally {
    activeAction.value = null
  }
}

async function removeUser(row: SystemUser): Promise<void> {
  if (activeAction.value) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定删除用户“${row.real_name || row.username}”吗？删除后无法恢复。`,
      '删除用户',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'error',
      },
    )
  } catch {
    return
  }

  activeAction.value = { id: row.id, type: 'delete' }

  try {
    await deleteUser(row.id)
    ElMessage.success('用户已删除')
    await list.load()
  } finally {
    activeAction.value = null
  }
}

function isActionLoading(userId: number, type: UserAction): boolean {
  return activeAction.value?.id === userId && activeAction.value.type === type
}

function roleName(code: SystemUser['roles'][number]): string {
  return getRoleDisplayName(code, roleNameMap.value)
}

onMounted(() => {
  void list.load()
  void loadOptions()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="用户管理" description="查看系统账号、所属部门与角色授权">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
        <el-button
          v-if="canManage"
          type="primary"
          :icon="Plus"
          :disabled="activeAction !== null"
          @click="openCreateDialog"
        >
          新建用户
        </el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div class="filter-row">
          <el-input
            v-model="list.filters.search"
            class="w-64"
            clearable
            placeholder="账号、姓名或邮箱"
            @keyup.enter="list.search"
          />
          <el-select
            v-model="list.filters.status"
            class="w-32"
            clearable
            placeholder="账号状态"
          >
            <el-option label="正常" value="ACTIVE" />
            <el-option label="停用" value="INACTIVE" />
          </el-select>
          <el-button type="primary" @click="list.search">查询</el-button>
          <el-button @click="list.reset">重置</el-button>
        </div>
        <span class="text-xs text-slate-400">共 {{ list.total.value }} 个账号</span>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无用户数据"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column label="用户" min-width="180" fixed="left">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <span class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                  <UserRound :size="16" />
                </span>
                <div>
                  <p class="font-medium text-slate-700">{{ row.real_name || row.username }}</p>
                  <p class="text-xs text-slate-400">@{{ row.username }}</p>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="部门" min-width="130">
            <template #default="{ row }">
              {{ row.department_id ? departmentMap.get(row.department_id) || `#${row.department_id}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" min-width="190">
            <template #default="{ row }">{{ row.email || '-' }}</template>
          </el-table-column>
          <el-table-column label="角色" min-width="210">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tooltip
                  v-for="role in row.roles"
                  :key="role"
                  :content="role"
                  placement="top"
                >
                  <el-tag type="primary" effect="plain" size="small">
                    <ShieldCheck :size="12" class="mr-1 inline" />
                    {{ roleName(role) }}
                  </el-tag>
                </el-tooltip>
                <span v-if="row.roles.length === 0" class="text-slate-400">-</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="最近登录" width="160">
            <template #default="{ row }">{{ formatDateTime(row.last_login_at) }}</template>
          </el-table-column>
          <el-table-column v-if="canManage" label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                :icon="Pencil"
                :loading="isActionLoading(row.id, 'edit')"
                :disabled="activeAction !== null"
                @click="openEditDialog(row)"
              >
                编辑
              </el-button>
              <el-button
                link
                :type="row.status === 'ACTIVE' ? 'warning' : 'success'"
                :icon="row.status === 'ACTIVE' ? CircleOff : CirclePlay"
                :loading="isActionLoading(row.id, 'toggle')"
                :disabled="activeAction !== null"
                @click="toggleUserStatus(row)"
              >
                {{ row.status === 'ACTIVE' ? '停用' : '启用' }}
              </el-button>
              <el-button
                link
                type="danger"
                :icon="Trash2"
                :loading="isActionLoading(row.id, 'delete')"
                :disabled="activeAction !== null"
                @click="removeUser(row)"
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

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="min(720px, calc(100vw - 32px))"
      destroy-on-close
      :close-on-click-modal="!submitting"
      :close-on-press-escape="!submitting"
      :show-close="!submitting"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-position="top"
        :disabled="submitting"
      >
        <div class="grid gap-x-5 md:grid-cols-2">
          <el-form-item label="账号" prop="username">
            <el-input
              v-model="form.username"
              :disabled="isEditing"
              autocomplete="username"
              placeholder="3-64 位字母、数字、下划线、点或短横线"
            />
          </el-form-item>
          <el-form-item label="姓名" prop="real_name">
            <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              show-password
              :placeholder="isEditing ? '留空表示不修改，至少 8 位' : '请输入至少 8 位密码'"
            />
          </el-form-item>
          <el-form-item label="账号状态" prop="status">
            <el-select v-model="form.status" class="w-full">
              <el-option label="正常" value="ACTIVE" />
              <el-option label="停用" value="INACTIVE" />
            </el-select>
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱地址" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="所属部门" prop="department_id">
            <el-select
              v-model="form.department_id"
              class="w-full"
              clearable
              filterable
              placeholder="请选择所属部门"
            >
              <el-option
                v-for="department in departments"
                :key="department.id"
                :label="department.name"
                :value="department.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="角色" prop="role_codes">
            <el-select
              v-model="form.role_codes"
              class="w-full"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              placeholder="请选择 1-5 个角色"
            >
              <el-option
                v-for="role in selectableRoles"
                :key="role.code"
                :label="`${role.name}（${role.code}）`"
                :value="role.code"
              />
            </el-select>
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="flex flex-wrap justify-end gap-2">
          <el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitUser">
            {{ isEditing ? '保存修改' : '创建用户' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
