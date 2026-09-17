<script setup>
import { ref, computed, onMounted } from 'vue'
import { getHistoryList, deleteHistory } from '../api/history'
import { authState } from '../utils/auth'

const emit = defineEmits(['select', 'login'])

const isLoggedIn = computed(() => !!authState.token)

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const hasMore = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const error = ref('')
const removeError = ref('')
const removingId = ref(null)

function formatDate(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function fetchList(isLoadMore = false) {
  if (isLoadMore) {
    loadingMore.value = true
  } else {
    loading.value = true
  }
  error.value = ''
  try {
    const res = await getHistoryList({ page: page.value, pageSize })
    list.value = isLoadMore ? list.value.concat(res.List || []) : (res.List || [])
    total.value = res.total || 0
    hasMore.value = !!res.hasMore
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  page.value += 1
  fetchList(true)
}

async function handleRemove(item) {
  if (removingId.value !== null) return
  removingId.value = item.id
  removeError.value = ''
  try {
    await deleteHistory(item.id)
    list.value = list.value.filter((n) => n.id !== item.id)
    total.value = Math.max(0, total.value - 1)
  } catch (e) {
    removeError.value = e.message || '删除失败'
  } finally {
    removingId.value = null
  }
}

onMounted(() => {
  if (isLoggedIn.value) fetchList()
})
</script>

<template>
  <section class="history-list">
    <!-- 未登录：提示去登录 -->
    <div v-if="!isLoggedIn" class="state-box">
      <p>登录后即可查看你的浏览历史</p>
      <button class="retry-btn" @click="emit('login')">去登录</button>
    </div>

    <template v-else>
      <div class="section-head">
        <h2>浏览历史</h2>
        <span v-if="!loading && !error" class="count">共 {{ total }} 条</span>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="state-box">
        <div class="spinner" aria-label="加载中"></div>
        <p>加载中…</p>
      </div>

      <!-- 错误 -->
      <div v-else-if="error" class="state-box error">
        <p class="error-text">{{ error }}</p>
        <button class="retry-btn" @click="fetchList()">重试</button>
      </div>

      <!-- 空数据 -->
      <div v-else-if="list.length === 0" class="state-box">
        <p>还没有浏览记录</p>
      </div>

      <!-- 历史列表 -->
      <template v-else>
        <p v-if="removeError" class="fav-error">{{ removeError }}</p>
        <div class="fav-items">
        <article
          v-for="item in list"
          :key="item.id"
          class="fav-item"
          @click="emit('select', item)"
        >
          <img
            v-if="item.image"
            class="fav-img"
            :src="item.image"
            :alt="item.title"
          />
          <div class="fav-body">
            <h3 class="fav-title">{{ item.title }}</h3>
            <p v-if="item.description" class="fav-desc">{{ item.description }}</p>
            <div class="fav-meta">
              <span v-if="item.author" class="meta-author">{{ item.author }}</span>
              <span class="meta-views">{{ item.views ?? 0 }} 阅读</span>
              <span v-if="item.publish_time" class="meta-time">发布于 {{ formatDate(item.publish_time) }}</span>
              <span v-if="item.view_time" class="meta-time">浏览于 {{ formatDate(item.view_time) }}</span>
            </div>
          </div>
          <button
            class="fav-remove"
            :disabled="removingId === item.id"
            @click.stop="handleRemove(item)"
          >
            {{ removingId === item.id ? '删除中…' : '删除' }}
          </button>
        </article>
      </div>
      </template>

      <!-- 加载更多 -->
      <div v-if="hasMore" class="load-more">
        <button class="more-btn" :disabled="loadingMore" @click="loadMore">
          {{ loadingMore ? '加载中…' : '加载更多' }}
        </button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.history-list {
  margin-top: 8px;
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
  color: #ececf0;
}

.count {
  font-size: 13px;
  color: #6e6e78;
}

.fav-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.fav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #15151a;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.fav-item:hover {
  transform: translateY(-2px);
  border-color: rgba(212, 175, 55, 0.45);
}

.fav-img {
  flex-shrink: 0;
  width: 100px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  background: #1e1e25;
}

.fav-body {
  flex: 1;
  min-width: 0;
}

.fav-title {
  font-size: 16px;
  font-weight: 600;
  color: #ececf0;
  line-height: 1.4;
}

.fav-desc {
  margin-top: 6px;
  font-size: 13px;
  color: #9b9ba6;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.fav-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
  color: #6e6e78;
}

.meta-author {
  color: #d4af37;
  font-weight: 600;
}

.fav-remove {
  flex-shrink: 0;
  padding: 7px 14px;
  border: 1px solid rgba(212, 175, 55, 0.5);
  border-radius: 20px;
  background: transparent;
  color: #d4af37;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.fav-remove:hover:not(:disabled) {
  background: rgba(212, 175, 55, 0.12);
}

.fav-remove:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.fav-error {
  margin-bottom: 12px;
  font-size: 13px;
  color: #ff6b6b;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.more-btn {
  padding: 10px 40px;
  border: 1px solid rgba(212, 175, 55, 0.5);
  border-radius: 24px;
  background: transparent;
  color: #d4af37;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.more-btn:hover:not(:disabled) {
  background: rgba(212, 175, 55, 0.12);
}

.more-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
</style>
