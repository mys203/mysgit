<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { KeyRound, RefreshCw, ShieldCheck } from 'lucide-vue-next'
import { fetchRoles } from '@/api/system'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import type { Role } from '@/types/system'
import { getErrorMessage } from '@/utils/error'
import { formatDateTime } from '@/utils/format'

const roles = ref<Role[]>([])
const loading = ref(false)
const errorMessage = ref('')

async function loadRoles(): Promise<void> {
  loading.value = true
  errorMessage.value = ''

  try {
    roles.value = (await fetchRoles()).items
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
    roles.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadRoles)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="角色权限" description="查看系统角色与权限点配置">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="loading" @click="loadRoles">刷新</el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <DataState
        :loading="loading"
        :error="errorMessage"
        :empty="!loading && !errorMessage && roles.length === 0"
        empty-text="暂无角色数据"
        @retry="loadRoles"
      >
        <el-table :data="roles" stripe>
          <el-table-column label="角色" min-width="180">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <span class="flex h-8 w-8 items-center justify-center rounded bg-blue-50 text-blue-600">
                  <ShieldCheck :size="16" />
                </span>
                <div>
                  <p class="font-medium text-slate-700">{{ row.name }}</p>
                  <p class="text-xs text-slate-400">{{ row.code }}</p>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="角色说明" min-width="240">
            <template #default="{ row }">{{ row.description || '-' }}</template>
          </el-table-column>
          <el-table-column prop="code" label="角色编码" min-width="150">
            <template #default="{ row }">
              <div class="flex items-center gap-1.5">
                <KeyRound :size="14" class="text-blue-500" />
                {{ row.code }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </DataState>
    </section>
  </div>
</template>
