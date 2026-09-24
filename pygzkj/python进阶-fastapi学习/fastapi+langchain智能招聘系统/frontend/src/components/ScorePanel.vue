<script setup lang="ts">
import { computed } from 'vue'
import type { MatchResult } from '@/types/ai'

const props = defineProps<{
  result: MatchResult
}>()

const dimensions = computed(() => [
  { key: '规则评分', score: props.result.rule_score },
  { key: '向量评分', score: props.result.vector_score ?? 0 },
  { key: '模型评分', score: props.result.llm_score ?? 0 },
])

const scoreColor = computed(() => {
  if (props.result.score >= 80) {
    return '#22a06b'
  }

  if (props.result.score >= 60) {
    return '#409eff'
  }

  return '#d98b12'
})
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[180px_1fr]">
    <div class="flex flex-col items-center justify-center rounded bg-slate-50 p-4">
      <el-progress
        type="circle"
        :percentage="Math.round(result.score)"
        :width="118"
        :stroke-width="10"
        :color="scoreColor"
      />
      <el-tag class="mt-3" type="primary" effect="light">{{ result.level }}</el-tag>
    </div>

    <div class="min-w-0">
      <div
        v-for="dimension in dimensions"
        :key="dimension.key"
        class="mb-3 last:mb-0"
      >
        <div class="mb-1 flex items-center justify-between gap-3 text-sm">
          <span class="truncate text-slate-700">{{ dimension.key }}</span>
          <span class="shrink-0 text-slate-500">
            {{ Math.round(dimension.score) }} 分
          </span>
        </div>
        <el-progress
          :percentage="Math.round(dimension.score)"
          :show-text="false"
          :stroke-width="7"
        />
      </div>
      <p v-if="result.degraded" class="mt-3 text-xs text-amber-600">
        当前结果包含降级评分项
      </p>
    </div>
  </div>
</template>
