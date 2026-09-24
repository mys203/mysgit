<script setup lang="ts">
defineProps<{
  page: number
  pageSize: number
  total: number
}>()

defineEmits<{
  'update:page': [value: number]
  'update:page-size': [value: number]
}>()
</script>

<template>
  <div class="pagination-row">
    <el-pagination
      background
      layout="total, sizes, prev, pager, next"
      :current-page="page"
      :page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      @update:current-page="$emit('update:page', $event)"
      @update:page-size="$emit('update:page-size', $event)"
    />
  </div>
</template>
