<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Gauge, Play, RefreshCw } from 'lucide-vue-next'
import { createMatchTask, fetchAiTask } from '@/api/ai'
import { fetchCandidates } from '@/api/candidates'
import { fetchJobs } from '@/api/jobs'
import MatchResultPanel from '@/components/MatchResultPanel.vue'
import PageHeader from '@/components/PageHeader.vue'
import AiTaskStatus from '@/components/AiTaskStatus.vue'
import type { MatchQuery, MatchResponse, MatchResult } from '@/types/ai'
import type { Candidate } from '@/types/candidate'
import type { Job } from '@/types/job'
import { getErrorMessage } from '@/utils/error'
import { parsePositiveId } from '@/utils/contracts'
import { useAiTaskPolling } from '@/utils/aiTaskPolling'

const route = useRoute()
const jobs = ref<Job[]>([])
const candidates = ref<Candidate[]>([])
const response = ref<MatchResponse | null>(null)
const selectedResult = ref<MatchResult | null>(null)
const submitting = ref(false)
const errorMessage = ref('')
const { task: matchTask, start: startMatchPolling } = useAiTaskPolling<MatchResponse>()

const form = reactive<MatchQuery>({
  job_id: 0,
  candidate_ids: [],
  top_k: 20,
  force_refresh: false,
})

const candidateMap = computed(
  () => new Map(candidates.value.map((item) => [item.id, item.name])),
)

async function loadOptions(): Promise<void> {
  const [jobResult, candidateResult] = await Promise.allSettled([
    fetchJobs({ status: 'PUBLISHED', page: 1, page_size: 100 }),
    fetchCandidates({ page: 1, page_size: 100 }),
  ])

  if (jobResult.status === 'fulfilled') {
    jobs.value = jobResult.value.items
  }
  if (candidateResult.status === 'fulfilled') {
    candidates.value = candidateResult.value.items
  }

  form.job_id = parsePositiveId(route.query.job_id) ?? 0
}

async function submit(): Promise<void> {
  if (!form.job_id) {
    ElMessage.warning('请选择目标岗位')
    return
  }

  submitting.value = true
  errorMessage.value = ''
  response.value = null
  selectedResult.value = null

  try {
    const accepted = await createMatchTask({
      ...form,
      candidate_ids: form.candidate_ids?.length ? form.candidate_ids : undefined,
    })
    const task = await startMatchPolling({
      taskNo: accepted.task_no,
      getTask: (taskNo) => fetchAiTask<MatchResponse>(taskNo),
    })
    const output = task.output_payload
    if (!output) {
      throw new Error('匹配任务成功但未返回结果')
    }
    response.value = output
    selectedResult.value = output.items[0] ?? null
    ElMessage.success(output.degraded ? '匹配完成，当前使用降级能力' : '人岗匹配已完成')
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    submitting.value = false
  }
}

onMounted(loadOptions)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="智能人岗匹配" description="按岗位和候选人生成规则、向量与模型综合评分">
      <template #actions>
        <el-button :icon="RefreshCw" @click="loadOptions">刷新选项</el-button>
      </template>
    </PageHeader>

    <el-alert
      v-if="errorMessage"
      class="mb-4"
      :title="errorMessage"
      type="error"
      :closable="false"
      show-icon
    />

    <section class="panel p-5">
      <div class="grid items-end gap-4 xl:grid-cols-[minmax(220px,1fr)_minmax(280px,1.4fr)_120px_auto]">
        <el-form-item label="目标岗位" class="mb-0">
          <el-select v-model="form.job_id" class="w-full" filterable placeholder="请选择招聘岗位">
            <el-option
              v-for="job in jobs"
              :key="job.id"
              :label="`${job.title} · ${job.code}`"
              :value="job.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="候选人范围" class="mb-0">
          <el-select
            v-model="form.candidate_ids"
            class="w-full"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            placeholder="不选择时匹配前 20 位正常候选人"
          >
            <el-option
              v-for="candidate in candidates"
              :key="candidate.id"
              :label="`${candidate.name} · ${candidate.current_title || '暂无职位'}`"
              :value="candidate.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="返回数量" class="mb-0">
          <el-input-number v-model="form.top_k" class="w-full" :min="1" :max="100" />
        </el-form-item>
        <div class="flex items-center gap-3 pb-1">
          <el-checkbox v-model="form.force_refresh">重新计算</el-checkbox>
          <el-button type="primary" :icon="Play" :loading="submitting" @click="submit">
            开始匹配
          </el-button>
        </div>
      </div>
    </section>

    <div v-if="matchTask || submitting" class="mt-4">
      <AiTaskStatus :task="matchTask" />
    </div>

    <section v-if="response" class="panel mt-4">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
        <div>
          <h2 class="text-sm font-semibold text-slate-700">匹配结果</h2>
          <p class="mt-1 text-xs text-slate-400">
            任务号 {{ response.task_no }} · 算法 {{ response.algorithm_version }}
          </p>
        </div>
        <el-tag :type="response.degraded ? 'warning' : 'success'" effect="light">
          {{ response.degraded ? '降级模式' : '完整模式' }}
        </el-tag>
      </div>

      <el-table
        :data="response.items"
        highlight-current-row
        @current-change="(row: MatchResult | null) => (selectedResult = row)"
      >
        <el-table-column label="候选人" min-width="150">
          <template #default="{ row }">
            {{ candidateMap.get(row.candidate_id) || `候选人 #${row.candidate_id}` }}
          </template>
        </el-table-column>
        <el-table-column prop="score" label="综合评分" width="100" />
        <el-table-column prop="rule_score" label="规则评分" width="100" />
        <el-table-column label="向量评分" width="100">
          <template #default="{ row }">{{ row.vector_score ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="模型评分" width="100">
          <template #default="{ row }">{{ row.llm_score ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="level" label="等级" width="100" />
        <el-table-column label="匹配依据" min-width="300">
          <template #default="{ row }">
            {{ row.reasons.slice(0, 3).join('；') || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="selectedResult" class="panel mt-4 p-5">
      <div class="mb-4 flex items-center gap-2">
        <Gauge :size="18" class="text-blue-600" />
        <h2 class="text-base font-semibold text-slate-700">
          {{ candidateMap.get(selectedResult.candidate_id) || `候选人 #${selectedResult.candidate_id}` }}
        </h2>
      </div>
      <MatchResultPanel :result="selectedResult" />
    </section>

    <section v-else-if="!response" class="panel mt-4">
      <el-empty description="选择岗位和候选人后开始匹配" :image-size="92" />
    </section>
  </div>
</template>
