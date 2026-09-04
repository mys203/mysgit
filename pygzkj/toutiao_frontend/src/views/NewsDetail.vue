<script setup>
import { ref, computed, onMounted } from 'vue'
import { getNewsDetail } from '../api/news'

const props = defineProps({
  // 从新闻列表点进来的那条新闻（至少包含 id）
  news: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['back'])

// 详情数据
const detail = ref(null)
const loading = ref(true)
const error = ref('')
// 当前展示的新闻 id（点击相关推荐后切换，默认用列表带进来的 id）
const currentId = ref(props.news.id)

// 相关推荐：后端按同分类热度取前 5，可能把当前这篇也算进去，这里过滤掉自己
const relatedNews = computed(() =>
  (detail.value?.relater || []).filter((item) => item.id !== currentId.value)
)

// 格式化后端返回的时间（ISO 字符串 → YYYY-MM-DD HH:mm）
function formatDate(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function fetchDetail(id = currentId.value) {
  loading.value = true
  error.value = ''
  try {
    detail.value = await getNewsDetail({ id })
    currentId.value = id
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// 点击相关推荐项，切换详情并回到顶部
function openRelated(item) {
  if (!item?.id || item.id === currentId.value) return
  fetchDetail(item.id)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => fetchDetail())
</script>

<template>
  <section class="news-detail">
    <button class="back-btn" @click="emit('back')">← 返回列表</button>

    <!-- 加载中 -->
    <div v-if="loading" class="state-box">
      <div class="spinner" aria-label="加载中"></div>
      <p>加载中…</p>
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="state-box error">
      <p class="error-text">{{ error }}</p>
      <button class="retry-btn" @click="fetchDetail">重试</button>
    </div>

    <!-- 详情内容 + 相关推荐 -->
    <template v-else-if="detail">
      <article class="detail-card">
        <h1 class="detail-title">{{ detail.title }}</h1>

        <div class="detail-meta">
          <span v-if="detail.author" class="meta-author">{{ detail.author }}</span>
          <span v-if="detail.publishTime" class="meta-time">{{ formatDate(detail.publishTime) }}</span>
          <span class="meta-views">{{ detail.views ?? 0 }} 阅读</span>
        </div>

        <img
          v-if="detail.image"
          class="detail-img"
          :src="detail.image"
          :alt="detail.title"
        />

        <div class="detail-content">{{ detail.content }}</div>
      </article>

      <!-- 相关推荐 -->
      <section v-if="relatedNews.length" class="related-section">
        <h2 class="related-title">相关推荐</h2>
        <div class="related-items">
          <article
            v-for="item in relatedNews"
            :key="item.id"
            class="related-item"
            @click="openRelated(item)"
          >
            <img
              v-if="item.image"
              class="related-img"
              :src="item.image"
              :alt="item.title"
            />
            <div class="related-body">
              <h3 class="related-item-title">{{ item.title }}</h3>
              <p v-if="item.description" class="related-desc">{{ item.description }}</p>
              <div class="related-meta">
                <span v-if="item.author" class="meta-author">{{ item.author }}</span>
                <span class="meta-views">{{ item.views ?? 0 }} 阅读</span>
                <span v-if="item.publish_time" class="meta-time">{{ formatDate(item.publish_time) }}</span>
              </div>
            </div>
            <span class="related-arrow" aria-hidden="true">›</span>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.news-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-btn {
  align-self: flex-start;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #fff;
  color: #1f2329;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.15s ease;
}

.back-btn:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.detail-card {
  background: #fff;
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.detail-title {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.4;
  color: #1f2329;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 14px;
  font-size: 13px;
  color: #8a919f;
}

.meta-author {
  color: #e02e24;
  font-weight: 600;
}

.detail-img {
  display: block;
  width: 100%;
  max-height: 360px;
  object-fit: cover;
  border-radius: 10px;
  margin-top: 20px;
  background: #f0f1f3;
}

.detail-content {
  margin-top: 20px;
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
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

/* 相关推荐 */
.related-section {
  background: #fff;
  border-radius: 14px;
  padding: 24px 28px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.related-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2329;
  padding-bottom: 12px;
  margin-bottom: 8px;
  border-bottom: 1px solid #f0f1f3;
  position: relative;
}

.related-title::before {
  content: '';
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 36px;
  height: 3px;
  border-radius: 2px;
  background: #e02e24;
}

.related-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.related-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.15s ease;
}

.related-item:hover {
  background: #f7f8fa;
  transform: translateX(4px);
}

.related-img {
  flex-shrink: 0;
  width: 96px;
  height: 72px;
  object-fit: cover;
  border-radius: 8px;
  background: #f0f1f3;
}

.related-body {
  flex: 1;
  min-width: 0;
}

.related-item-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2329;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.related-item:hover .related-item-title {
  color: #e02e24;
}

.related-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.related-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 6px;
  font-size: 12px;
  color: #8a919f;
}

.related-arrow {
  flex-shrink: 0;
  font-size: 22px;
  color: #c9cdd4;
  line-height: 1;
}
</style>
