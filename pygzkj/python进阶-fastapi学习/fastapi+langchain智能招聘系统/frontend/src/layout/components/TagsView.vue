<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { TabsPaneContext, TabPaneName } from 'element-plus'
import { MoreHorizontal } from 'lucide-vue-next'
import { useTagsViewStore } from '@/stores/tagsView'

const route = useRoute()
const router = useRouter()
const tagsStore = useTagsViewStore()

const activePath = computed({
  get: () => route.path,
  set: (path: string) => {
    if (path !== route.path) {
      void router.push(path)
    }
  },
})

function handleTabClick(pane: TabsPaneContext): void {
  const path = String(pane.paneName)
  if (path !== route.path) {
    void router.push(path)
  }
}

function handleTabRemove(name: TabPaneName): void {
  const path = String(name)
  const nextPath = tagsStore.removeTab(path)

  if (path === route.path && nextPath && nextPath !== path) {
    void router.push(nextPath)
    return
  }

  if (path === route.path && tagsStore.tabs.length === 0) {
    void router.push('/dashboard')
  }
}

function handleCommand(command: string): void {
  if (command === 'current') {
    handleTabRemove(route.path)
  }

  if (command === 'others') {
    tagsStore.removeOtherTabs(route.path)
  }
}

</script>

<template>
  <div
    class="flex h-[var(--tags-height)] shrink-0 items-center border-b border-slate-200 bg-white px-2"
  >
    <el-tabs
      v-if="tagsStore.tabs.length > 0"
      v-model="activePath"
      class="tags-view-tabs min-w-0 flex-1"
      type="card"
      @tab-click="handleTabClick"
      @tab-remove="handleTabRemove"
    >
      <el-tab-pane
        v-for="tab in tagsStore.tabs"
        :key="tab.path"
        :name="tab.path"
        :label="tab.title"
        :closable="tagsStore.tabs.length > 1"
      />
    </el-tabs>

    <el-dropdown trigger="click" @command="handleCommand">
      <button
        type="button"
        class="ml-2 flex h-7 w-7 shrink-0 items-center justify-center rounded border border-slate-200 text-slate-500 transition hover:border-blue-300 hover:text-blue-600"
        title="标签页操作"
      >
        <MoreHorizontal :size="16" />
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="current">关闭当前</el-dropdown-item>
          <el-dropdown-item command="others">关闭其他</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<style scoped>
.tags-view-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.tags-view-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.tags-view-tabs :deep(.el-tabs__item) {
  height: 28px;
  margin-right: 4px;
  border: 1px solid #e5eaf0;
  border-radius: 4px;
  color: #5b6676;
  font-size: 12px;
  line-height: 26px;
}

.tags-view-tabs :deep(.el-tabs__item.is-active) {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
}

.tags-view-tabs :deep(.el-tabs__item.is-active .el-icon) {
  color: #fff;
}

.tags-view-tabs :deep(.el-tabs__nav) {
  border: 0 !important;
}

.tags-view-tabs :deep(.el-tabs__content) {
  display: none;
}
</style>
