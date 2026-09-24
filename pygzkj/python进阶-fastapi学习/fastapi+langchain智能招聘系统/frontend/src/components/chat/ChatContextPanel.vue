<script setup lang="ts">
import { Building2, BriefcaseBusiness, ChevronRight, UserRoundSearch } from 'lucide-vue-next'
import type { Candidate } from '@/types/candidate'
import type { Job } from '@/types/job'

const props = defineProps<{
  job: Job | null
  candidate: Candidate | null
  loading?: boolean
}>()
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-white">
    <div class="border-b border-slate-200 px-4 py-3">
      <h2 class="text-sm font-semibold text-slate-800">上下文详情</h2>
      <p class="mt-1 text-xs text-slate-400">当前回答优先使用以下招聘资料</p>
    </div>

    <div v-loading="props.loading" class="min-h-0 flex-1 overflow-y-auto p-4">
      <section v-if="props.job" class="border-b border-slate-100 pb-4">
        <div class="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
          <span class="flex h-7 w-7 items-center justify-center rounded bg-blue-50 text-blue-600">
            <BriefcaseBusiness :size="15" />
          </span>
          岗位信息
        </div>
        <h3 class="text-sm font-semibold text-slate-800">{{ props.job.title }}</h3>
        <p class="mt-1 text-xs text-slate-400">{{ props.job.code }}</p>
        <dl class="mt-3 space-y-2 text-xs">
          <div class="flex gap-2">
            <dt class="w-14 shrink-0 text-slate-400">地点</dt>
            <dd class="text-slate-600">{{ props.job.location || '未填写' }}</dd>
          </div>
          <div class="flex gap-2">
            <dt class="w-14 shrink-0 text-slate-400">招聘人数</dt>
            <dd class="text-slate-600">{{ props.job.headcount }} 人</dd>
          </div>
          <div class="flex gap-2">
            <dt class="w-14 shrink-0 text-slate-400">岗位要求</dt>
            <dd class="line-clamp-4 text-slate-600">
              {{ props.job.requirements || '未填写' }}
            </dd>
          </div>
        </dl>
        <div v-if="props.job.skills.length" class="mt-3 flex flex-wrap gap-1">
          <el-tag
            v-for="skill in props.job.skills.slice(0, 8)"
            :key="skill"
            size="small"
            effect="plain"
          >
            {{ skill }}
          </el-tag>
        </div>
      </section>

      <section v-if="props.candidate" class="py-4">
        <div class="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
          <span class="flex h-7 w-7 items-center justify-center rounded bg-emerald-50 text-emerald-600">
            <UserRoundSearch :size="15" />
          </span>
          候选人信息
        </div>
        <h3 class="text-sm font-semibold text-slate-800">{{ props.candidate.name }}</h3>
        <p class="mt-1 flex items-center gap-1 text-xs text-slate-400">
          <Building2 :size="13" />
          {{ props.candidate.current_company || '未填写当前公司' }}
        </p>
        <dl class="mt-3 space-y-2 text-xs">
          <div class="flex gap-2">
            <dt class="w-14 shrink-0 text-slate-400">当前职位</dt>
            <dd class="text-slate-600">
              {{ props.candidate.current_title || '未填写' }}
            </dd>
          </div>
          <div class="flex gap-2">
            <dt class="w-14 shrink-0 text-slate-400">工作年限</dt>
            <dd class="text-slate-600">
              {{ props.candidate.work_years ?? '-' }} 年
            </dd>
          </div>
          <div class="flex gap-2">
            <dt class="w-14 shrink-0 text-slate-400">个人摘要</dt>
            <dd class="line-clamp-5 text-slate-600">
              {{ props.candidate.summary || '未填写' }}
            </dd>
          </div>
        </dl>
        <div v-if="props.candidate.skills.length" class="mt-3 flex flex-wrap gap-1">
          <el-tag
            v-for="skill in props.candidate.skills.slice(0, 8)"
            :key="skill"
            size="small"
            effect="plain"
            type="success"
          >
            {{ skill }}
          </el-tag>
        </div>
      </section>

      <div
        v-if="!props.loading && !props.job && !props.candidate"
        class="flex h-full min-h-52 flex-col items-center justify-center text-center"
      >
        <BriefcaseBusiness :size="28" class="text-slate-300" />
        <p class="mt-3 text-sm text-slate-500">尚未选择岗位或候选人</p>
        <p class="mt-1 flex items-center text-xs text-slate-400">
          选择后可为回答补充招聘上下文
          <ChevronRight :size="13" />
        </p>
      </div>
    </div>
  </div>
</template>
