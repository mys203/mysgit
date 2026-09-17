<script setup>
import { ref, computed, onMounted } from 'vue'
import { getNewsDetail } from '../api/news'
import { checkFavorite, addFavorite, removeFavorite } from '../api/favorite'
import { addNewsHistory } from '../api/history'
import { authState } from '../utils/auth'

const props = defineProps({
  // 从新闻列表点进来的那条新闻（至少包含 id）
  news: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['back', 'login'])

// 详情数据
const detail = ref(null)
const loading = ref(true)
const error = ref('')
// 当前展示的新闻 id（点击相关推荐后切换，默认用列表带进来的 id）
const currentId = ref(props.news.id)

// 收藏相关状态
const isFavorite = ref(false)
const favLoading = ref(false)
const favError = ref('')
// 是否已登录（token 存在即视为已登录）
const isLoggedIn = computed(() => !!authState.token)

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
    // 详情加载完后再查收藏状态（不阻塞详情展示）
    fetchFavorite(id)
    // 已登录则记录浏览历史（失败不打断阅读）
    recordHistory(id)
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// 查询当前新闻是否已被收藏（未登录则跳过）
async function fetchFavorite(id = currentId.value) {
  isFavorite.value = false
  favError.value = ''
  if (!isLoggedIn.value) return
  try {
    const res = await checkFavorite(id)
    isFavorite.value = !!res.isFavorite
  } catch (e) {
    // 检查失败不打断阅读，保持未收藏状态
    isFavorite.value = false
  }
}

// 记录浏览历史：未登录跳过，失败静默处理不打断阅读
async function recordHistory(id) {
  if (!isLoggedIn.value) return
  try {
    await addNewsHistory(id)
  } catch (e) {
    // 记录失败不影响阅读体验，忽略即可
  }
}

// 点击收藏按钮：未登录跳登录；已收藏则取消收藏，否则收藏当前新闻
async function toggleFavorite() {
  if (!isLoggedIn.value) {
    emit('login')
    return
  }
  if (favLoading.value) return
  const willRemove = isFavorite.value
  favLoading.value = true
  favError.value = ''
  try {
    if (willRemove) {
      await removeFavorite(currentId.value)
      isFavorite.value = false
    } else {
      await addFavorite(currentId.value)
      isFavorite.value = true
    }
  } catch (e) {
    favError.value = e.message || (willRemove ? '取消收藏失败，请稍后重试' : '收藏失败，请稍后重试')
  } finally {
    favLoading.value = false
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
        <div class="detail-head">
          <h1 class="detail-title">{{ detail.title }}</h1>
          <button
            class="fav-btn"
            :class="{ active: isFavorite }"
            :disabled="favLoading"
            @click="toggleFavorite"
          >
            <span v-if="favLoading" class="fav-spinner" aria-label="收藏中"></span>
            <span v-else>{{ isFavorite ? '★ 已收藏' : '☆ 收藏' }}</span>
          </button>
        </div>
        <p v-if="favError" class="fav-error">{{ favError }}</p>

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
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: #15151a;
  color: #ececf0;
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.back-btn:hover {
  border-color: rgba(212, 175, 55, 0.5);
}

.detail-card {
  background: #15151a;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 14px;
  padding: 28px;
}

.detail-title {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.4;
  color: #ececf0;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.detail-head .detail-title {
  flex: 1;
  min-width: 0;
}

.fav-btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid rgba(212, 175, 55, 0.5);
  border-radius: 20px;
  background: transparent;
  color: #d4af37;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.fav-btn:hover:not(:disabled) {
  background: rgba(212, 175, 55, 0.12);
}

.fav-btn.active {
  background: linear-gradient(135deg, #d4af37 0%, #b8962f 100%);
  color: #1a1a1a;
}

.fav-btn:disabled {
  cursor: not-allowed;
}

.fav-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-top-color: #d4af37;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.fav-error {
  margin-top: 10px;
  font-size: 13px;
  color: #ff6b6b;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 14px;
  font-size: 13px;
  color: #6e6e78;
}

.meta-author {
  color: #d4af37;
  font-weight: 600;
}

.detail-img {
  display: block;
  width: 100%;
  max-height: 360px;
  object-fit: cover;
  border-radius: 10px;
  margin-top: 20px;
  background: #1e1e25;
}

.detail-content {
  margin-top: 20px;
  font-size: 15px;
  line-height: 1.8;
  color: #d5d5dc;
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
  background: #15151a;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  color: #9b9ba6;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(212, 175, 55, 0.2);
  border-top-color: #d4af37;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-text {
  color: #ff6b6b;
}

.retry-btn {
  padding: 8px 22px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #d4af37 0%, #b8962f 100%);
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.retry-btn:hover {
  opacity: 0.85;
}

/* 相关推荐 */
.related-section {
  background: #15151a;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 14px;
  padding: 24px 28px;
}

.related-title {
  font-size: 18px;
  font-weight: 700;
  color: #ececf0;
  padding-bottom: 12px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
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
  background: #d4af37;
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
  background: rgba(255, 255, 255, 0.04);
  transform: translateX(4px);
}

.related-img {
  flex-shrink: 0;
  width: 96px;
  height: 72px;
  object-fit: cover;
  border-radius: 8px;
  background: #1e1e25;
}

.related-body {
  flex: 1;
  min-width: 0;
}

.related-item-title {
  font-size: 15px;
  font-weight: 600;
  color: #ececf0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.related-item:hover .related-item-title {
  color: #d4af37;
}

.related-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #9b9ba6;
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
  color: #6e6e78;
}

.related-arrow {
  flex-shrink: 0;
  font-size: 22px;
  color: #5a5a64;
  line-height: 1;
}
</style>
