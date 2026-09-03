<script setup>
defineProps({
  category: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['select'])
</script>

<template>
  <div class="category-card" @click="emit('select', category)">
    <div class="category-rank">#{{ category.sort_order ?? '-' }}</div>
    <div class="category-body">
      <h3 class="category-name">{{ category.name }}</h3>
      <p class="category-id">ID: {{ category.id }}</p>
    </div>
  </div>
</template>

<style scoped>
.category-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.category-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.category-rank {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #fff1f0;
  color: #e02e24;
  font-weight: 700;
  font-size: 15px;
}

.category-name {
  font-size: 17px;
  font-weight: 600;
  color: #1f2329;
}

.category-id {
  margin-top: 2px;
  font-size: 12px;
  color: #8a919f;
}
</style>
