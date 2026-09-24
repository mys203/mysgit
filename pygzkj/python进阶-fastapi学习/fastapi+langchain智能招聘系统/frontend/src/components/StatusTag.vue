<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status?: string
  text?: string
}>()

const statusMap: Record<string, { label: string; type: 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
  DRAFT: { label: '草稿', type: 'info' },
  PUBLISHED: { label: '招聘中', type: 'success' },
  CLOSED: { label: '已关闭', type: 'info' },
  ACTIVE: { label: '启用', type: 'success' },
  INACTIVE: { label: '停用', type: 'info' },
  BLACKLIST: { label: '黑名单', type: 'danger' },
  UPLOADED: { label: '已上传', type: 'info' },
  PARSING: { label: '解析中', type: 'primary' },
  PARSED: { label: '已解析', type: 'success' },
  CONFIRMED: { label: '已确认', type: 'success' },
  FAILED: { label: '失败', type: 'danger' },
  PENDING: { label: '等待处理', type: 'warning' },
  RUNNING: { label: '执行中', type: 'primary' },
  SUCCEEDED: { label: '成功', type: 'success' },
  APPLIED: { label: '已申请', type: 'info' },
  SCREENING: { label: '筛选中', type: 'warning' },
  INTERVIEW: { label: '面试中', type: 'primary' },
  OFFER: { label: '待录用', type: 'warning' },
  HIRED: { label: '已录用', type: 'success' },
  REJECTED: { label: '已淘汰', type: 'danger' },
  WITHDRAWN: { label: '已撤回', type: 'info' },
  SCHEDULED: { label: '已安排', type: 'primary' },
  IN_PROGRESS: { label: '进行中', type: 'primary' },
  COMPLETED: { label: '已完成', type: 'success' },
  CANCELLED: { label: '已取消', type: 'danger' },
  APPROVED: { label: '已通过', type: 'success' },
  INVITED: { label: '已邀请', type: 'warning' },
  DECLINED: { label: '已拒绝', type: 'danger' },
}

const current = computed(() => statusMap[props.status ?? ''])
</script>

<template>
  <el-tag :type="current?.type ?? 'info'" size="small" effect="light">
    {{ text || current?.label || status || '-' }}
  </el-tag>
</template>
