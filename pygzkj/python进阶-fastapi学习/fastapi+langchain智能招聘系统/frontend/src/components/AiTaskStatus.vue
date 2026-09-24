<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheckBig, CircleX, LoaderCircle } from 'lucide-vue-next'
import type { AiTask } from '@/types/common'

const props = defineProps<{
  task: AiTask<object> | null
}>()

const statusMeta = computed(() => {
  if (!props.task) {
    return {
      label: '尚未提交任务',
      type: 'info' as const,
      icon: LoaderCircle,
    }
  }

  const mapping = {
    PENDING: { label: '等待执行', type: 'warning' as const, icon: LoaderCircle },
    RUNNING: { label: '正在执行', type: 'primary' as const, icon: LoaderCircle },
    SUCCEEDED: { label: '执行成功', type: 'success' as const, icon: CircleCheckBig },
    FAILED: { label: '执行失败', type: 'danger' as const, icon: CircleX },
  }

  return mapping[props.task.status]
})
</script>

<template>
  <div class="flex items-center gap-3 rounded border border-slate-200 bg-white px-4 py-3">
    <el-tag :type="statusMeta.type" effect="light">{{ statusMeta.label }}</el-tag>
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2 text-sm text-slate-600">
        <component
          :is="statusMeta.icon"
          :size="16"
          :class="{ 'animate-spin': task?.status === 'PENDING' || task?.status === 'RUNNING' }"
        />
        <span v-if="task">
          任务号：{{ task.task_no }}
          <span v-if="task.provider"> · {{ task.provider }}</span>
          <span v-if="task.model_name"> / {{ task.model_name }}</span>
        </span>
        <span v-else>提交后显示任务进度</span>
      </div>
      <p v-if="task?.degraded" class="mt-1 text-xs text-amber-600">
        当前使用降级能力完成处理
      </p>
      <p v-if="task?.error_code || task?.error_message" class="mt-1 text-xs text-red-500">
        <span v-if="task.error_code">[{{ task.error_code }}] </span>
        {{ task.error_message || '任务执行失败' }}
      </p>
    </div>
  </div>
</template>
