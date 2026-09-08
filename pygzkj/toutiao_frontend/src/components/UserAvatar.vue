<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getUserInfo } from '../api/users'
import { authState, setAuth, clearAuth } from '../utils/auth'

const emit = defineEmits(['login'])

// 未设置头像时的兜底图
const DEFAULT_AVATAR = 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'

const isOpen = ref(false)
const loading = ref(false)
const error = ref('')

const isLoggedIn = computed(() => !!authState.token)
const avatar = computed(() => authState.userinfo?.avatar || DEFAULT_AVATAR)
const username = computed(() => authState.userinfo?.username || '')

// 性别枚举值 → 中文展示
function genderLabel(value) {
  if (value === 'male') return '男'
  if (value === 'female') return '女'
  return '保密'
}

// 点击头像：未登录跳登录页，已登录切换个人信息面板
function toggle() {
  if (!isLoggedIn.value) {
    emit('login')
    return
  }
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    fetchInfo()
  }
}

// 打开面板时用 token 拉取最新个人信息
async function fetchInfo() {
  loading.value = true
  error.value = ''
  try {
    const info = await getUserInfo()
    // 用后端返回的最新信息更新本地（token 保持不变）
    setAuth(authState.token, { ...authState.userinfo, ...info })
  } catch (e) {
    error.value = e.message || '获取用户信息失败'
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  clearAuth()
  isOpen.value = false
}

// 点击面板以外区域时收起面板
function onDocumentClick(e) {
  if (!e.target.closest('.user-avatar')) {
    isOpen.value = false
  }
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>

<template>
  <div class="user-avatar">
    <!-- 未登录：登录入口 -->
    <button v-if="!isLoggedIn" class="avatar-login" @click="toggle">登录</button>

    <!-- 已登录：头像 + 下拉个人信息面板 -->
    <template v-else>
      <button class="avatar-btn" @click="toggle">
        <img class="avatar-img" :src="avatar" :alt="username" />
        <span class="avatar-name">{{ username }}</span>
        <span class="avatar-arrow" :class="{ open: isOpen }">▾</span>
      </button>

      <transition name="fade">
        <div v-if="isOpen" class="avatar-panel">
          <div class="panel-head">
            <img class="panel-avatar" :src="avatar" :alt="username" />
            <div class="panel-head-text">
              <p class="panel-username">{{ username }}</p>
              <p class="panel-nick">{{ authState.userinfo?.nickname || '还没有昵称' }}</p>
            </div>
          </div>

          <div v-if="loading" class="panel-loading">加载中…</div>
          <div v-else-if="error" class="panel-error">{{ error }}</div>
          <ul v-else class="panel-list">
            <li class="panel-item">
              <span class="panel-key">用户 ID</span>
              <span class="panel-val">{{ authState.userinfo?.id }}</span>
            </li>
            <li class="panel-item">
              <span class="panel-key">性别</span>
              <span class="panel-val">{{ genderLabel(authState.userinfo?.gender) }}</span>
            </li>
            <li class="panel-item">
              <span class="panel-key">个人简介</span>
              <span class="panel-val">{{ authState.userinfo?.bio || '这个人很懒，什么都没留下' }}</span>
            </li>
          </ul>

          <button class="panel-logout" @click="handleLogout">退出登录</button>
        </div>
      </transition>
    </template>
  </div>
</template>

<style scoped>
.user-avatar {
  position: relative;
}

/* 未登录入口 */
.avatar-login {
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  background: transparent;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.avatar-login:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* 已登录头像按钮 */
.avatar-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border: none;
  border-radius: 24px;
  background: rgba(0, 0, 0, 0.15);
  color: #fff;
  cursor: pointer;
  transition: background 0.15s ease;
}
.avatar-btn:hover {
  background: rgba(0, 0, 0, 0.25);
}
.avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  background: #fff;
}
.avatar-name {
  font-size: 14px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.avatar-arrow {
  font-size: 12px;
  transition: transform 0.15s ease;
}
.avatar-arrow.open {
  transform: rotate(180deg);
}

/* 下拉个人信息面板 */
.avatar-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 240px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  text-align: left;
  color: #1f2329;
}
.panel-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f1f3;
}
.panel-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  background: #f0f1f3;
}
.panel-head-text {
  min-width: 0;
}
.panel-username {
  font-size: 16px;
  font-weight: 700;
  color: #1f2329;
}
.panel-nick {
  margin-top: 2px;
  font-size: 13px;
  color: #8a919f;
}
.panel-loading,
.panel-error {
  padding: 12px 0;
  font-size: 13px;
  color: #8a919f;
}
.panel-error {
  color: #e02e24;
}
.panel-list {
  list-style: none;
  margin-top: 8px;
}
.panel-item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
}
.panel-key {
  flex-shrink: 0;
  width: 60px;
  font-size: 13px;
  color: #8a919f;
}
.panel-val {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: #1f2329;
  word-break: break-all;
}
.panel-logout {
  width: 100%;
  margin-top: 12px;
  padding: 9px 0;
  border: 1px solid #e02e24;
  border-radius: 8px;
  background: #fff;
  color: #e02e24;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.panel-logout:hover {
  background: #e02e24;
  color: #fff;
}

/* 面板展开/收起过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
