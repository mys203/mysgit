<script setup>
import { ref, computed } from 'vue'
import NewsCategories from './views/NewsCategories.vue'
import NewsList from './views/NewsList.vue'
import NewsDetail from './views/NewsDetail.vue'
import FavoriteList from './views/FavoriteList.vue'
import UserAuth from './views/UserAuth.vue'
import UserAvatar from './components/UserAvatar.vue'

// 当前选中的分类
const activeCategory = ref(null)
// 当前选中的新闻（非空时显示详情页）
const selectedNews = ref(null)
// 当前模块：news 新闻 / favorite 我的收藏 / user 用户
const currentModule = ref('news')

// 切换模块：清空详情态，避免跨模块残留详情页
function switchModule(m) {
  currentModule.value = m
  selectedNews.value = null
}

// 根据当前模块动态显示标题
const moduleTitle = computed(() =>
  currentModule.value === 'news' ? '头条新闻' : '头条用户'
)
const moduleSubtitle = computed(() =>
  currentModule.value === 'news' ? 'Toutiao News' : 'Toutiao Account'
)
</script>

<template>
  <div class="app">
    <header class="app-header">
      <div class="header-avatar">
        <UserAvatar @login="currentModule = 'user'" />
      </div>
      <div class="header-brand">
        <h1>{{ moduleTitle }}</h1>
        <p class="app-subtitle">{{ moduleSubtitle }}</p>
      </div>
      <nav class="app-nav">
        <button
          :class="['nav-btn', { active: currentModule === 'news' }]"
          @click="switchModule('news')"
        >📰 新闻</button>
        <button
          :class="['nav-btn', { active: currentModule === 'favorite' }]"
          @click="switchModule('favorite')"
        >⭐ 收藏</button>
        <button
          :class="['nav-btn', { active: currentModule === 'user' }]"
          @click="switchModule('user')"
        >👤 用户</button>
      </nav>
    </header>

    <main class="app-main">
      <!-- 新闻模块 -->
      <template v-if="currentModule === 'news'">
        <!-- 详情页 -->
        <NewsDetail
          v-if="selectedNews"
          :news="selectedNews"
          @back="selectedNews = null"
          @login="currentModule = 'user'"
        />
        <!-- 分类 + 列表页 -->
        <template v-else>
          <NewsCategories @select="activeCategory = $event" />
          <NewsList
            :category="activeCategory"
            @select="selectedNews = $event"
          />
        </template>
      </template>
      <!-- 收藏模块：我的收藏列表 -->
      <template v-else-if="currentModule === 'favorite'">
        <NewsDetail
          v-if="selectedNews"
          :news="selectedNews"
          @back="selectedNews = null"
          @login="switchModule('user')"
        />
        <FavoriteList v-else @select="selectedNews = $event" @login="switchModule('user')" />
      </template>

      <!-- 用户模块：登录 / 注册 -->
      <UserAuth v-else />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: #f4f5f7;
  color: #1f2329;
  -webkit-font-smoothing: antialiased;
}

.app-header {
  position: relative;
  background: linear-gradient(135deg, #e02e24 0%, #ff5a3c 100%);
  color: #fff;
  padding: 40px 24px 28px;
  text-align: center;
}

.header-avatar {
  position: absolute;
  top: 16px;
  right: 20px;
  z-index: 10;
}

.header-brand h1 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 1px;
}

.app-subtitle {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.85;
}

.app-nav {
  display: inline-flex;
  gap: 4px;
  margin-top: 24px;
  padding: 4px;
  background: rgba(0, 0, 0, 0.12);
  border-radius: 24px;
}

.nav-btn {
  padding: 9px 30px;
  border: none;
  border-radius: 20px;
  background: transparent;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-btn:hover {
  color: #fff;
}

.nav-btn.active {
  background: #fff;
  color: #e02e24;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}

.app-main {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}
</style>
