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
      <p class="category-id">进入分类</p>
    </div>
  </div>
</template>

<style scoped>
.category-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #15151a;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.category-card:hover {
  transform: translateY(-2px);
  border-color: rgba(212, 175, 55, 0.45);
}

.category-rank {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(212, 175, 55, 0.12);
  color: #d4af37;
  font-weight: 700;
  font-size: 15px;
}

.category-name {
  font-size: 17px;
  font-weight: 600;
  color: #ececf0;
}

.category-id {
  margin-top: 2px;
  font-size: 12px;
  color: #6e6e78;
}
</style>
