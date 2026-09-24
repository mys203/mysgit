<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { CheckCircle2, FileText, RefreshCw } from 'lucide-vue-next'
import { fetchResumes } from '@/api/resumes'
import PageHeader from '@/components/PageHeader.vue'
import ResumeUploader from '@/components/ResumeUploader.vue'
import StatusTag from '@/components/StatusTag.vue'
import type { Resume } from '@/types/resume'
import { formatDateTime, formatFileSize } from '@/utils/format'

const recentResumes = ref<Resume[]>([])
const loading = ref(false)

async function loadRecent(): Promise<void> {
  loading.value = true

  try {
    const result = await fetchResumes({
      page: 1,
      page_size: 8,
    })
    recentResumes.value = result.items
  } finally {
    loading.value = false
  }
}

function handleUploaded(resume: Resume): void {
  recentResumes.value = [resume, ...recentResumes.value.filter((item) => item.id !== resume.id)]
}

onMounted(loadRecent)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="简历上传" description="上传简历文件并自动建立简历库记录">
      <template #actions>
        <el-button :icon="RefreshCw" :loading="loading" @click="loadRecent">
          刷新记录
        </el-button>
      </template>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.8fr)]">
      <section class="panel p-5">
        <div class="mb-4">
          <h2 class="text-base font-semibold text-slate-700">选择文件</h2>
          <p class="mt-1 text-sm text-slate-500">
            文件上传后进入简历库，可继续触发 AI 深度解析。
          </p>
        </div>
        <ResumeUploader @uploaded="handleUploaded" />
      </section>

      <section class="panel overflow-hidden">
        <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
          <CheckCircle2 :size="17" class="text-emerald-600" />
          <h2 class="text-sm font-semibold text-slate-700">最近上传</h2>
        </div>
        <div v-if="loading" class="p-4">
          <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="recentResumes.length > 0" class="divide-y divide-slate-100">
          <div
            v-for="resume in recentResumes"
            :key="resume.id"
            class="flex items-start gap-3 p-4"
          >
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-blue-50 text-blue-600">
              <FileText :size="17" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-slate-700">
                {{ resume.filename }}
              </p>
              <p class="mt-1 text-xs text-slate-400">
                {{ formatFileSize(resume.file_size) }} · {{ formatDateTime(resume.created_at) }}
              </p>
            </div>
            <StatusTag :status="resume.status" />
          </div>
        </div>
        <el-empty v-else description="暂无上传记录" :image-size="76" />
      </section>
    </div>
  </div>
</template>
