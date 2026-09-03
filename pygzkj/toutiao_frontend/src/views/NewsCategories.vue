<script setup>
import { ref, computed, onMounted } from 'vue'
import { getNewsCategories } from '../api/news'
import CategoryCard from '../components/CategoryCard.vue'

// 分类列表数据
const categories = ref([])
// 加载状态
const loading = ref(false)
// 错误信息
const error = ref('')

// 向父组件（App.vue）抛出选中的分类
const emit = defineEmits(['select'])

// 按 sort_order 升序排序后的列表
const sortedCategories = computed(() =>
  [...categories.value].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
)

// 拉取分类数据
async function fetchCategories() {
  loading.value = true
  error.value = ''
  try {
    const data = await getNewsCategories()
    categories.value = Array.isArray(data) ? data : []
  } catch (e) {
    error.value = e.message || '加载失败'
    categories.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchCategories)
</script>

<template>
  <section class="categories">
    <div class="section-head">
      <h2>全部分类</h2>
      <span v-if="!loading && !error" class="count">共 {{ categories.length }} 个</span>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="state-box">
      <div class="spinner" aria-label="加载中"></div>
      <p>加载中…</p>
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="state-box error">
      <p class="error-text">{{ error }}</p>
      <button class="retry-btn" @click="fetchCategories">重试</button>
    </div>

    <!-- 空数据 -->
    <div v-else-if="sortedCategories.length === 0" class="state-box">
      <p>暂无分类数据</p>
    </div>

    <!-- 数据列表 -->
    <div v-else class="category-grid">
      <CategoryCard
        v-for="item in sortedCategories"
        :key="item.id"
        :category="item"
        @select="emit('select', $event)"
      />
    </div>
  </section>
</template>

<style scoped>
.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-head h2 {
  font-size: 20px;
  font-weight: 700;
}

.count {
  font-size: 13px;
  color: #8a919f;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  background: #fff;
  border-radius: 12px;
  color: #8a919f;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #ffe3e1;
  border-top-color: #e02e24;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-text {
  color: #e02e24;
}

.retry-btn {
  padding: 8px 22px;
  border: none;
  border-radius: 8px;
  background: #e02e24;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.retry-btn:hover {
  opacity: 0.85;
}
</style>
