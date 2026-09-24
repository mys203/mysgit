<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Eye, RefreshCw } from 'lucide-vue-next'
import { fetchOperationLogs } from '@/api/system'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { usePagedList } from '@/composables/usePagedList'
import type { OperationLog } from '@/types/system'
import { formatDateTime } from '@/utils/format'

interface LogFilters extends Record<string, unknown> {
  action: string
  resource_type: string
}

const list = usePagedList<OperationLog, LogFilters>(fetchOperationLogs, {
  action: '',
  resource_type: '',
})

const drawerVisible = ref(false)
const selectedLog = ref<OperationLog | null>(null)

function showDetail(log: OperationLog): void {
  selectedLog.value = log
  drawerVisible.value = true
}

function statusType(statusCode: number): 'success' | 'danger' {
  return statusCode >= 200 && statusCode < 400 ? 'success' : 'danger'
}

onMounted(list.load)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="操作日志" description="查询后台操作记录、响应状态与耗时">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="list.loading.value" @click="list.load">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <div class="table-toolbar border-b border-slate-100 p-4">
        <div class="filter-row">
          <el-input
            v-model="list.filters.action"
            class="w-48"
            clearable
            placeholder="操作动作"
            @keyup.enter="list.search"
          />
          <el-input
            v-model="list.filters.resource_type"
            class="w-48"
            clearable
            placeholder="资源类型"
            @keyup.enter="list.search"
          />
          <el-button type="primary" @click="list.search">查询</el-button>
          <el-button @click="list.reset">重置</el-button>
        </div>
        <span class="text-xs text-slate-400">共 {{ list.total.value }} 条日志</span>
      </div>

      <DataState
        :loading="list.loading.value"
        :error="list.errorMessage.value"
        :empty="!list.loading.value && !list.errorMessage.value && list.items.value.length === 0"
        empty-text="暂无操作日志"
        @retry="list.load"
      >
        <el-table :data="list.items.value" stripe>
          <el-table-column label="操作人" min-width="120">
            <template #default="{ row }">
              {{ row.username || (row.user_id ? `用户 #${row.user_id}` : '系统') }}
            </template>
          </el-table-column>
          <el-table-column prop="action" label="操作" min-width="120" />
          <el-table-column prop="resource_type" label="资源类型" min-width="120">
            <template #default="{ row }">{{ row.resource_type || '-' }}</template>
          </el-table-column>
          <el-table-column prop="method" label="方法" width="90" />
          <el-table-column prop="path" label="请求路径" min-width="250" show-overflow-tooltip />
          <el-table-column prop="ip" label="IP 地址" min-width="130">
            <template #default="{ row }">{{ row.ip || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态码" width="90">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status_code)" size="small">
                {{ row.status_code }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="耗时" width="90">
            <template #default="{ row }">
              {{ row.duration_ms === null ? '-' : `${row.duration_ms.toFixed(1)} ms` }}
            </template>
          </el-table-column>
          <el-table-column label="操作时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :icon="Eye" @click="showDetail(row)">
                详情
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

    <el-drawer v-model="drawerVisible" title="日志详情" size="560px">
      <el-descriptions v-if="selectedLog" :column="1" border>
        <el-descriptions-item label="日志 ID">{{ selectedLog.id }}</el-descriptions-item>
        <el-descriptions-item label="操作人">
          {{ selectedLog.username || selectedLog.user_id || '系统' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作">{{ selectedLog.action }}</el-descriptions-item>
        <el-descriptions-item label="资源类型">
          {{ selectedLog.resource_type || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="资源 ID">
          {{ selectedLog.resource_id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="请求方法">{{ selectedLog.method }}</el-descriptions-item>
        <el-descriptions-item label="请求路径">
          <span class="break-all">{{ selectedLog.path }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="IP 地址">{{ selectedLog.ip || '-' }}</el-descriptions-item>
        <el-descriptions-item label="User Agent">
          <span class="break-all">{{ selectedLog.user_agent || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="请求 ID">
          {{ selectedLog.request_id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态码">
          <el-tag :type="statusType(selectedLog.status_code)" size="small">
            {{ selectedLog.status_code }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="响应耗时">
          {{ selectedLog.duration_ms === null ? '-' : `${selectedLog.duration_ms.toFixed(1)} ms` }}
        </el-descriptions-item>
        <el-descriptions-item label="操作时间">
          {{ formatDateTime(selectedLog.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="详情">
          <pre class="whitespace-pre-wrap break-all text-xs">{{ JSON.stringify(selectedLog.detail, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>
