<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle, ListChecks } from 'lucide-vue-next'
import type { MatchResult } from '@/types/ai'
import ScorePanel from '@/components/ScorePanel.vue'

const props = defineProps<{
  result: MatchResult
}>()

const detailEntries = computed(() =>
  Object.entries(props.result.detail).filter(([, value]) =>
    ['string', 'number', 'boolean'].includes(typeof value),
  ),
)
</script>

<template>
  <div class="space-y-5">
    <ScorePanel :result="result" />

    <section>
      <h3 class="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-700">
        <ListChecks :size="16" class="text-blue-600" />
        匹配依据
      </h3>
      <div class="space-y-2">
        <p
          v-for="(reason, index) in result.reasons"
          :key="`${reason}-${index}`"
          class="rounded bg-slate-50 p-3 text-sm leading-6 text-slate-600"
        >
          {{ reason }}
        </p>
        <span v-if="result.reasons.length === 0" class="text-sm text-slate-400">
          暂无匹配依据
        </span>
      </div>
    </section>

    <section v-if="detailEntries.length > 0">
      <h3 class="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-700">
        <AlertTriangle :size="16" class="text-amber-500" />
        评分详情
      </h3>
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item
          v-for="[key, value] in detailEntries"
          :key="key"
          :label="key"
        >
          {{ value }}
        </el-descriptions-item>
      </el-descriptions>
    </section>
  </div>
</template>
