<script setup>
import { ref } from 'vue'
import NewsCategories from './views/NewsCategories.vue'
import NewsList from './views/NewsList.vue'

// 当前选中的分类
const activeCategory = ref(null)
</script>

<template>
  <div class="app">
    <header class="app-header">
      <h1>头条新闻分类</h1>
      <p class="app-subtitle">News Categories</p>
    </header>
    <main class="app-main">
      <NewsCategories @select="activeCategory = $event" />
      <NewsList :category="activeCategory" />
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
  background: linear-gradient(135deg, #e02e24 0%, #ff5a3c 100%);
  color: #fff;
  padding: 32px 24px;
  text-align: center;
}

.app-header h1 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 1px;
}

.app-subtitle {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.85;
}

.app-main {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}
</style>
