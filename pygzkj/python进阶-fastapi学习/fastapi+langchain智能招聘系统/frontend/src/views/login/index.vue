<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { BriefcaseBusiness, LockKeyhole, LogIn, UserRound } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import type { LoginPayload } from '@/types/auth'
import { getErrorMessage } from '@/utils/error'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')
const form = reactive<LoginPayload>({
  username: '',
  password: '',
})

const rules: FormRules<LoginPayload> = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 50, message: '账号长度应为 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 个字符', trigger: 'blur' },
  ],
}

async function submit(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.login(form)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    await router.replace(redirect)
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#edf2f7]">
    <div class="grid min-h-screen lg:grid-cols-[minmax(0,1fr)_440px]">
      <section
        class="relative hidden overflow-hidden bg-[#1f2d3d] px-14 py-12 text-white lg:flex lg:flex-col lg:justify-between"
      >
        <div>
          <div class="flex items-center gap-3">
            <span class="flex h-10 w-10 items-center justify-center rounded bg-[#409eff]">
              <BriefcaseBusiness :size="22" />
            </span>
            <span class="text-lg font-semibold">智能招聘系统</span>
          </div>
          <div class="mt-24 max-w-xl">
            <p class="text-sm uppercase tracking-[0.2em] text-blue-300">Recruitment Workspace</p>
            <h1 class="mt-5 text-4xl font-semibold leading-tight tracking-normal">
              让岗位、简历与候选人流程在同一处高效协同
            </h1>
            <p class="mt-5 max-w-lg text-base leading-7 text-slate-300">
              管理招聘流程，使用 AI 完成简历解析、人岗匹配与面试题辅助生成。
            </p>
          </div>
        </div>
        <p class="text-xs text-slate-400">招聘管理与 AI 助手工作台</p>
      </section>

      <section class="flex items-center justify-center bg-white px-6 py-12">
        <div class="w-full max-w-sm">
          <div class="mb-8 lg:hidden">
            <span class="inline-flex h-11 w-11 items-center justify-center rounded bg-[#409eff] text-white">
              <BriefcaseBusiness :size="23" />
            </span>
            <h1 class="mt-4 text-2xl font-semibold text-slate-800">智能招聘系统</h1>
          </div>

          <h2 class="text-2xl font-semibold text-slate-800">账号登录</h2>
          <p class="mt-2 text-sm text-slate-500">请输入招聘系统账号进入管理后台</p>

          <el-alert
            v-if="errorMessage"
            class="mt-5"
            :title="errorMessage"
            type="error"
            :closable="false"
            show-icon
          />

          <el-form
            ref="formRef"
            class="mt-6"
            :model="form"
            :rules="rules"
            label-position="top"
            @keyup.enter="submit"
          >
            <el-form-item label="账号" prop="username">
              <el-input
                v-model="form.username"
                size="large"
                placeholder="请输入账号"
                autocomplete="username"
                :prefix-icon="UserRound"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                size="large"
                type="password"
                placeholder="请输入密码"
                autocomplete="current-password"
                show-password
                :prefix-icon="LockKeyhole"
              />
            </el-form-item>
            <el-button
              class="mt-2 w-full"
              type="primary"
              size="large"
              :loading="loading"
              :icon="LogIn"
              @click="submit"
            >
              登录
            </el-button>
          </el-form>
        </div>
      </section>
    </div>
  </div>
</template>
