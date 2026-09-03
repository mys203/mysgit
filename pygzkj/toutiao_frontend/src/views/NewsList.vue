<script setup>
import { ref, watch } from 'vue'
import { getNewsList } from '../api/news'

const props = defineProps({
  // 当前选中的分类对象，来自 App.vue
  category: {
    type: Object,
    default: null
  }
})

const list = ref([])
const loading = ref(false)
const error = ref('')

async function fetchList() {
  if (!props.category) {
    list.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    // 注意：响应拦截器已剥掉 code/msg/data，这里拿到的是后端 data 的内容 { List: [...] }
    const res = await getNewsList({
      categoryId: props.category.id,
      page: 1,
      pageSize: 20
    })
    list.value = res.List || []
  } catch (e) {
    error.value = e.message || '加载失败'
    list.value = []
  } finally {
    loading.value = false
  }
}

// 分类变化时重新拉取（含首次挂载）
watch(() => props.category?.id, fetchList, { immediate: true })
</script>

<template>
  <section v-if="category" class="news-list">
    <div class="section-head">
      <h2>{{ category.name }} · 新闻列表</h2>
      <span v-if="!loading && !error" class="count">共 {{ list.length }} 条</span>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="state-box">
      <div class="spinner" aria-label="加载中"></div>
      <p>加载中…</p>
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="state-box error">
      <p class="error-text">{{ error }}</p>
      <button class="retry-btn" @click="fetchList">重试</button>
    </div>

    <!-- 空数据 -->
    <div v-else-if="list.length === 0" class="state-box">
      <p>该分类暂无新闻</p>
    </div>

    <!-- 新闻列表 -->
    <div v-else class="news-items">
      <article v-for="item in list" :key="item.id" class="news-item">
        <img
          v-if="item.image"
          class="news-img"
          :src="item.image"
          :alt="item.title"
        />
        <div class="news-body">
          <h3 class="news-title">{{ item.title }}</h3>
          <p v-if="item.description" class="news-desc">{{ item.description }}</p>
          <div class="news-meta">
            <span v-if="item.author" class="meta-author">{{ item.author }}</span>
            <span class="meta-views">{{ item.views }} 阅读</span>
            <span v-if="item.publish_time" class="meta-time">{{ item.publish_time }}</span>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.news-list {
  margin-top: 32px;
}

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

.news-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-item {
  display: flex;
  gap: 14px;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.news-img {
  flex-shrink: 0;
  width: 100px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  background: #f0f1f3;
}

.news-body {
  min-width: 0;
}

.news-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2329;
  line-height: 1.4;
}

.news-desc {
  margin-top: 6px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
  color: #8a919f;
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
