<script setup lang="ts">
withDefaults(
  defineProps<{
    loading?: boolean
    error?: string
    empty?: boolean
    emptyText?: string
    rows?: number
  }>(),
  {
    loading: false,
    error: '',
    empty: false,
    emptyText: '暂无数据',
    rows: 6,
  },
)

defineEmits<{
  retry: []
}>()
</script>

<template>
  <div v-if="loading" class="p-4">
    <el-skeleton :rows="rows" animated />
  </div>
  <div v-else-if="error" class="p-4">
    <el-alert :title="error" type="error" :closable="false" show-icon>
      <template #default>
        <button
          type="button"
          class="mt-3 rounded border border-red-200 bg-white px-3 py-1 text-sm text-red-600 hover:bg-red-50"
          @click="$emit('retry')"
        >
          重新加载
        </button>
      </template>
    </el-alert>
  </div>
  <el-empty v-else-if="empty" :description="emptyText" :image-size="86" />
  <slot v-else></slot>
</template>
