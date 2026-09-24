<script setup lang="ts">
import { computed, type Component } from 'vue'
import { useRoute } from 'vue-router'
import {
  BarChart3,
  BriefcaseBusiness,
  Building2,
  ChevronLeft,
  ClipboardList,
  FileSearch,
  FileText,
  Gauge,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  MessageSquareText,
  ScanSearch,
  Send,
  Sparkles,
  Tags,
  UserRound,
  UserRoundSearch,
  UsersRound,
} from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { PERMISSIONS } from '@/constants/permissions'

interface MenuItem {
  label: string
  path: string
  icon: Component
  permission?: string
}

interface MenuGroup {
  key: string
  label: string
  icon: Component
  children: MenuItem[]
}

const route = useRoute()
const appStore = useAppStore()
const authStore = useAuthStore()

const menuGroups: MenuGroup[] = [
  {
    key: 'jobs',
    label: '岗位管理',
    icon: BriefcaseBusiness,
    children: [
      { label: '岗位列表', path: '/jobs', icon: ListChecks, permission: PERMISSIONS.JOBS_READ },
      {
        label: '岗位发布',
        path: '/jobs/create',
        icon: Send,
        permission: PERMISSIONS.JOBS_WRITE,
      },
      {
        label: '岗位分类',
        path: '/jobs/categories',
        icon: Tags,
        permission: PERMISSIONS.JOBS_READ,
      },
    ],
  },
  {
    key: 'resumes',
    label: '简历管理',
    icon: FileText,
    children: [
      {
        label: '简历库',
        path: '/resumes',
        icon: FileSearch,
        permission: PERMISSIONS.RESUMES_READ,
      },
      {
        label: '简历上传',
        path: '/resumes/upload',
        icon: FileText,
        permission: PERMISSIONS.RESUMES_WRITE,
      },
      {
        label: '解析记录',
        path: '/resumes/parse-records',
        icon: ClipboardList,
        permission: PERMISSIONS.RESUMES_WRITE,
      },
    ],
  },
  {
    key: 'candidates',
    label: '候选人管理',
    icon: UsersRound,
    children: [
      {
        label: '候选人列表',
        path: '/candidates',
        icon: UserRoundSearch,
        permission: PERMISSIONS.CANDIDATES_READ,
      },
      {
        label: '应聘流程',
        path: '/candidates/applications',
        icon: BarChart3,
        permission: PERMISSIONS.APPLICATIONS_READ,
      },
      {
        label: '面试安排',
        path: '/candidates/interviews',
        icon: MessageSquareText,
        permission: PERMISSIONS.INTERVIEWS_READ,
      },
      {
        label: '录用管理',
        path: '/candidates/offers',
        icon: UserRound,
        permission: PERMISSIONS.APPLICATIONS_READ,
      },
    ],
  },
  {
    key: 'ai',
    label: 'AI 招聘助手',
    icon: Sparkles,
    children: [
      {
        label: 'AI 招聘问答',
        path: '/ai/chat',
        icon: MessageSquareText,
        permission: PERMISSIONS.AI_EXECUTE,
      },
      {
        label: '智能人岗匹配',
        path: '/ai/matches',
        icon: Gauge,
        permission: PERMISSIONS.AI_EXECUTE,
      },
      {
        label: '简历深度解析',
        path: '/ai/resume-parse',
        icon: ScanSearch,
        permission: PERMISSIONS.RESUMES_WRITE,
      },
      {
        label: '面试题生成',
        path: '/ai/interview-questions',
        icon: MessageSquareText,
        permission: PERMISSIONS.AI_EXECUTE,
      },
    ],
  },
  {
    key: 'system',
    label: '系统管理',
    icon: Building2,
    children: [
      {
        label: '用户管理',
        path: '/system/users',
        icon: UserRound,
        permission: PERMISSIONS.SYSTEM_MANAGE,
      },
      {
        label: '角色权限',
        path: '/system/roles',
        icon: KeyRound,
        permission: PERMISSIONS.SYSTEM_MANAGE,
      },
      {
        label: '操作日志',
        path: '/system/logs',
        icon: ClipboardList,
        permission: PERMISSIONS.LOGS_READ,
      },
    ],
  },
]

const baseMenuItems: MenuItem[] = [
  {
    label: '工作台',
    path: '/dashboard',
    icon: LayoutDashboard,
  },
]

const visibleMenuItems = computed(() =>
  baseMenuItems.filter((item) => authStore.canAccess(item.permission)),
)

const visibleMenuGroups = computed(() =>
  menuGroups
    .map((group) => ({
      ...group,
      children: group.children.filter((item) => authStore.canAccess(item.permission)),
    }))
    .filter((group) => group.children.length > 0),
)
</script>

<template>
  <aside
    class="sidebar-container flex h-screen shrink-0 flex-col"
    :class="{ 'is-collapsed': appStore.sidebarCollapsed }"
  >
    <div class="flex h-14 shrink-0 items-center border-b border-white/10 px-2">
      <button
        type="button"
        class="flex h-9 min-w-8 flex-1 items-center gap-2 overflow-hidden rounded px-1.5 text-left text-white transition hover:bg-white/10"
        :title="appStore.sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
        @click="appStore.toggleSidebar"
      >
        <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#409eff]">
          <BriefcaseBusiness :size="19" />
        </span>
        <span class="sidebar-logo-text text-sm font-semibold">智能招聘</span>
      </button>
      <button
        v-if="!appStore.sidebarCollapsed"
        type="button"
        class="flex h-8 w-7 shrink-0 items-center justify-center rounded text-slate-300 transition hover:bg-white/10 hover:text-white"
        title="折叠侧边栏"
        @click="appStore.setSidebarCollapsed(true)"
      >
        <ChevronLeft :size="17" />
      </button>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden">
      <el-menu
        class="sidebar-menu"
        :default-active="route.path"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        :unique-opened="true"
        router
      >
        <el-menu-item
          v-for="item in visibleMenuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" :size="18" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>

        <el-sub-menu
          v-for="group in visibleMenuGroups"
          :key="group.key"
          :index="group.key"
        >
          <template #title>
            <el-icon><component :is="group.icon" :size="18" /></el-icon>
            <span>{{ group.label }}</span>
          </template>
          <el-menu-item
            v-for="item in group.children"
            :key="item.path"
            :index="item.path"
          >
            <el-icon><component :is="item.icon" :size="17" /></el-icon>
            <template #title>{{ item.label }}</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
  </aside>
</template>
