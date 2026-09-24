<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RefreshCw, Tags } from 'lucide-vue-next'
import { fetchJobCategories } from '@/api/jobs'
import DataState from '@/components/DataState.vue'
import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import type { JobCategory } from '@/types/job'
import { getErrorMessage } from '@/utils/error'

const categories = ref<JobCategory[]>([])
const loading = ref(false)
const errorMessage = ref('')

async function loadCategories(): Promise<void> {
  loading.value = true
  errorMessage.value = ''

  try {
    categories.value = (await fetchJobCategories()).items
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
    categories.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadCategories)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="岗位分类" description="查看岗位分类及岗位数量分布">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="loading" @click="loadCategories">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <section class="panel">
      <DataState
        :loading="loading"
        :error="errorMessage"
        :empty="!loading && !errorMessage && categories.length === 0"
        empty-text="暂无岗位分类"
        @retry="loadCategories"
      >
        <el-table :data="categories" stripe>
          <el-table-column label="分类名称" min-width="180">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <Tags :size="16" class="text-blue-500" />
                <span class="font-medium text-slate-700">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="code" label="分类编码" min-width="140" />
          <el-table-column prop="parent_id" label="父分类" width="110">
            <template #default="{ row }">{{ row.parent_id ?? '-' }}</template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="90" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
        </el-table>
      </DataState>
    </section>
  </div>
</template>
