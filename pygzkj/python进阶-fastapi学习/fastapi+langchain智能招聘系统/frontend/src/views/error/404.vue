<script setup lang="ts">
import { useRouter } from 'vue-router'
import { FileQuestion } from 'lucide-vue-next'

const router = useRouter()
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-workspace p-6">
    <div class="text-center">
      <FileQuestion :size="64" class="mx-auto text-slate-300" />
      <h1 class="mt-5 text-2xl font-semibold text-slate-700">页面不存在</h1>
      <p class="mt-2 text-sm text-slate-500">访问地址无效或页面已被移除。</p>
      <el-button class="mt-5" type="primary" @click="router.push('/dashboard')">
        返回工作台
      </el-button>
    </div>
  </div>
</template>
