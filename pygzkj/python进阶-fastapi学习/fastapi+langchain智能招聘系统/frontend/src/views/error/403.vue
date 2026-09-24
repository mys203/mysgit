<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ShieldX } from 'lucide-vue-next'

const router = useRouter()
</script>

<template>
  <div class="flex min-h-[calc(100vh-120px)] items-center justify-center p-6">
    <div class="text-center">
      <ShieldX :size="64" class="mx-auto text-slate-300" />
      <h1 class="mt-5 text-2xl font-semibold text-slate-700">暂无访问权限</h1>
      <p class="mt-2 text-sm text-slate-500">当前账号没有访问该页面的权限，请联系管理员授权。</p>
      <el-button class="mt-5" type="primary" @click="router.push('/dashboard')">
        返回工作台
      </el-button>
    </div>
  </div>
</template>
