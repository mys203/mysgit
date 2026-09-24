<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, type UploadRawFile, type UploadRequestOptions } from 'element-plus'
import { UploadAjaxError } from 'element-plus/es/components/upload/src/ajax'
import { FileUp, UploadCloud } from 'lucide-vue-next'
import { uploadResume } from '@/api/resumes'
import type { Resume } from '@/types/resume'

const emits = defineEmits<{
  uploaded: [resume: Resume]
}>()

const uploadRef = ref()
const selectedFiles = ref<File[]>([])
const uploading = ref(false)
const progress = ref(0)
const acceptedExtensions = ['pdf', 'docx', 'txt']

function beforeUpload(file: UploadRawFile): boolean {
  const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
  const validType = acceptedExtensions.includes(extension)
  const validSize = file.size / 1024 / 1024 <= 10

  if (!validType) {
    ElMessage.error('仅支持 PDF、DOCX 或 TXT 文件')
    return false
  }

  if (!validSize) {
    ElMessage.error('单个文件不能超过 10MB')
    return false
  }

  return true
}

function handleChange(file: { raw?: File }): void {
  selectedFiles.value = file.raw ? [file.raw] : []
}

function clearFiles(): void {
  selectedFiles.value = []
  progress.value = 0
  uploadRef.value?.clearFiles()
}

async function handleUpload(options: UploadRequestOptions): Promise<void> {
  uploading.value = true
  progress.value = 0

  try {
    const result = await uploadResume(options.file, (percentage) => {
      progress.value = percentage
    })
    options.onSuccess(result)
    emits('uploaded', result)
    ElMessage.success('简历上传成功')
    clearFiles()
  } catch (error) {
    const message = error instanceof Error ? error.message : '上传失败'
    options.onError(new UploadAjaxError(message, 0, 'POST', '/resumes/upload'))
    clearFiles()
  } finally {
    uploading.value = false
  }
}

function submitUpload(): void {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择简历文件')
    return
  }

  uploadRef.value?.submit()
}
</script>

<template>
  <div class="rounded-md border border-dashed border-slate-300 bg-slate-50/60 p-5">
    <el-upload
      ref="uploadRef"
      drag
      action="#"
      :auto-upload="false"
      :limit="1"
      :multiple="false"
      accept=".pdf,.docx,.txt"
      :before-upload="beforeUpload"
      :http-request="handleUpload"
      :on-change="handleChange"
      :on-remove="clearFiles"
      :show-file-list="true"
    >
      <div class="flex flex-col items-center px-5 py-8 text-slate-500">
        <UploadCloud :size="42" class="mb-3 text-blue-500" />
        <p class="text-base font-medium text-slate-700">拖拽简历到此处，或点击选择文件</p>
        <p class="mt-2 text-xs text-slate-400">支持 PDF、DOCX、TXT，单个文件最大 10MB</p>
      </div>
    </el-upload>

    <el-progress
      v-if="uploading"
      class="mt-3"
      :percentage="progress"
      :stroke-width="8"
      striped
      striped-flow
    />

    <div class="mt-3 flex justify-end">
      <el-button
        type="primary"
        :icon="FileUp"
        :loading="uploading"
        :disabled="selectedFiles.length === 0"
        @click="submitUpload"
      >
        上传并入库
      </el-button>
    </div>
  </div>
</template>
