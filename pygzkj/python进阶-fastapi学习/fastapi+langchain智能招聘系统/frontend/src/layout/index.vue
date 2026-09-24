<script setup lang="ts">
import { RouterView } from 'vue-router'
import HeaderBar from '@/layout/components/HeaderBar.vue'
import Sidebar from '@/layout/components/Sidebar.vue'
import TagsView from '@/layout/components/TagsView.vue'
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-workspace">
    <Sidebar />
    <section class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <HeaderBar />
      <TagsView />
      <main class="min-h-0 flex-1 overflow-auto">
        <RouterView v-slot="{ Component, route }">
          <component :is="Component" :key="route.fullPath" />
        </RouterView>
      </main>
    </section>
  </div>
</template>
