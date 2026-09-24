<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronDown, CircleUserRound, LogOut, Settings } from 'lucide-vue-next'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const breadcrumbs = computed(() => {
  const records = route.matched
    .map((item) => (typeof item.meta.title === 'string' ? item.meta.title : ''))
    .filter(Boolean)
  return records.length > 0 ? records : ['工作台']
})

async function handleCommand(command: string): Promise<void> {
  if (command === 'profile') {
    await router.push('/system/users')
    return
  }

  if (command === 'logout') {
    await ElMessageBox.confirm('确定退出当前账号吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    try {
      await authStore.logout()
    } finally {
      await router.replace('/login')
    }
  }
}
</script>

<template>
  <header
    class="flex h-[var(--header-height)] shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4"
  >
    <el-breadcrumb separator="/">
      <el-breadcrumb-item v-for="item in breadcrumbs" :key="item">
        {{ item }}
      </el-breadcrumb-item>
    </el-breadcrumb>

    <el-dropdown trigger="click" @command="handleCommand">
      <button
        type="button"
        class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-slate-700 transition hover:bg-slate-50"
      >
        <span class="flex h-7 w-7 items-center justify-center rounded-full bg-blue-50 text-blue-600">
          <CircleUserRound :size="18" />
        </span>
        <span class="max-w-28 truncate font-medium">{{ authStore.displayName }}</span>
        <ChevronDown :size="15" class="text-slate-400" />
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="profile">
            <Settings :size="15" class="mr-2" />
            账号信息
          </el-dropdown-item>
          <el-dropdown-item command="logout" divided>
            <LogOut :size="15" class="mr-2" />
            退出登录
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </header>
</template>
