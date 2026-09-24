<script setup lang="ts">
import type { ResumeParseRecord } from '@/types/resume'
import StatusTag from '@/components/StatusTag.vue'

defineProps<{
  record: ResumeParseRecord
}>()
</script>

<template>
  <div class="space-y-5">
    <div class="grid gap-3 rounded bg-slate-50 p-4 text-sm md:grid-cols-3">
      <div>
        <span class="text-slate-400">解析状态</span>
        <div class="mt-1"><StatusTag :status="record.status" /></div>
      </div>
      <div>
        <span class="text-slate-400">解析任务</span>
        <p class="mt-1 text-slate-700">
          {{ record.task_id === null ? '-' : `#${record.task_id}` }}
        </p>
      </div>
      <div>
        <span class="text-slate-400">置信度</span>
        <p class="mt-1 text-slate-700">
          {{ record.confidence === null || record.confidence === undefined ? '-' : `${Math.round(record.confidence * 100)}%` }}
        </p>
      </div>
    </div>

    <el-descriptions
      :column="2"
      border
      size="small"
    >
      <el-descriptions-item label="姓名">
        {{ record.parsed_data.name || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="手机号">
        {{ record.parsed_data.phone || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="邮箱">
        {{ record.parsed_data.email || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="当前职位">
        {{ record.parsed_data.current_title || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="工作年限">
        {{ record.parsed_data.work_years ?? '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="当前公司">
        {{ record.parsed_data.current_company || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="技能" :span="2">
        <div class="flex flex-wrap gap-1.5">
          <el-tag
            v-for="skill in record.parsed_data.skills || []"
            :key="skill"
            size="small"
            effect="light"
          >
            {{ skill }}
          </el-tag>
          <span v-if="!record.parsed_data.skills?.length">-</span>
        </div>
      </el-descriptions-item>
      <el-descriptions-item label="个人摘要" :span="2">
        {{ record.parsed_data.summary || '-' }}
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>
