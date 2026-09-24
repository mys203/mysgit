import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTagsViewStore } from '@/stores/tagsView'
import { getAccessToken } from '@/utils/token'
import { PERMISSIONS } from '@/constants/permissions'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: {
      title: '登录',
      public: true,
      hidden: true,
    },
  },
  {
    path: '/',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台' },
      },
      {
        path: 'jobs',
        name: 'JobList',
        component: () => import('@/views/jobs/index.vue'),
        meta: { title: '岗位列表', permission: PERMISSIONS.JOBS_READ },
      },
      {
        path: 'jobs/create',
        name: 'JobCreate',
        component: () => import('@/views/jobs/create.vue'),
        meta: { title: '岗位发布', permission: PERMISSIONS.JOBS_WRITE },
      },
      {
        path: 'jobs/categories',
        name: 'JobCategories',
        component: () => import('@/views/jobs/categories.vue'),
        meta: { title: '岗位分类', permission: PERMISSIONS.JOBS_READ },
      },
      {
        path: 'resumes',
        name: 'ResumeList',
        component: () => import('@/views/resumes/index.vue'),
        meta: { title: '简历库', permission: PERMISSIONS.RESUMES_READ },
      },
      {
        path: 'resumes/upload',
        name: 'ResumeUpload',
        component: () => import('@/views/resumes/upload.vue'),
        meta: { title: '简历上传', permission: PERMISSIONS.RESUMES_WRITE },
      },
      {
        path: 'resumes/parse-records',
        name: 'ResumeParseRecords',
        component: () => import('@/views/resumes/parse-records.vue'),
        meta: { title: '解析记录', permission: PERMISSIONS.RESUMES_WRITE },
      },
      {
        path: 'candidates',
        name: 'CandidateList',
        component: () => import('@/views/candidates/index.vue'),
        meta: { title: '候选人列表', permission: PERMISSIONS.CANDIDATES_READ },
      },
      {
        path: 'candidates/applications',
        name: 'ApplicationList',
        component: () => import('@/views/candidates/applications.vue'),
        meta: { title: '应聘流程', permission: PERMISSIONS.APPLICATIONS_READ },
      },
      {
        path: 'candidates/interviews',
        name: 'InterviewList',
        component: () => import('@/views/candidates/interviews.vue'),
        meta: { title: '面试安排', permission: PERMISSIONS.INTERVIEWS_READ },
      },
      {
        path: 'candidates/offers',
        name: 'OfferList',
        component: () => import('@/views/candidates/offers.vue'),
        meta: { title: '录用管理', permission: PERMISSIONS.APPLICATIONS_READ },
      },
      {
        path: 'ai/chat',
        name: 'AiChat',
        component: () => import('@/views/ai/chat.vue'),
        meta: { title: 'AI 招聘问答', permission: PERMISSIONS.AI_EXECUTE },
      },
      {
        path: 'ai/matches',
        name: 'AiMatches',
        component: () => import('@/views/ai/matches.vue'),
        meta: { title: '智能人岗匹配', permission: PERMISSIONS.AI_EXECUTE },
      },
      {
        path: 'ai/resume-parse',
        name: 'AiResumeParse',
        component: () => import('@/views/ai/resume-parse.vue'),
        meta: { title: '简历深度解析', permission: PERMISSIONS.RESUMES_WRITE },
      },
      {
        path: 'ai/interview-questions',
        name: 'InterviewQuestions',
        component: () => import('@/views/ai/interview-questions.vue'),
        meta: { title: '面试题生成', permission: PERMISSIONS.AI_EXECUTE },
      },
      {
        path: 'system/users',
        name: 'SystemUsers',
        component: () => import('@/views/system/users.vue'),
        meta: { title: '用户管理', permission: PERMISSIONS.SYSTEM_MANAGE },
      },
      {
        path: 'system/roles',
        name: 'SystemRoles',
        component: () => import('@/views/system/roles.vue'),
        meta: { title: '角色权限', permission: PERMISSIONS.SYSTEM_MANAGE },
      },
      {
        path: 'system/logs',
        name: 'SystemLogs',
        component: () => import('@/views/system/logs.vue'),
        meta: { title: '操作日志', permission: PERMISSIONS.LOGS_READ },
      },
      {
        path: '403',
        name: 'Forbidden',
        component: () => import('@/views/error/403.vue'),
        meta: { title: '无权限', hidden: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      public: true,
      hidden: true,
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (to.meta.public === true) {
    if (to.path === '/login' && getAccessToken()) {
      return '/dashboard'
    }
    return true
  }

  if (!getAccessToken()) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  try {
    await authStore.initialize()
  } catch {
    authStore.clearSession()
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  const permission = typeof to.meta.permission === 'string' ? to.meta.permission : undefined
  if (permission && !authStore.canAccess(permission)) {
    return '/403'
  }

  return true
})

router.afterEach((to) => {
  const tagsStore = useTagsViewStore()
  tagsStore.addTab(to)
})

export default router
