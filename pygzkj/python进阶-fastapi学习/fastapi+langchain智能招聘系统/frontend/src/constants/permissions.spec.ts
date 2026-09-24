import { describe, expect, it } from 'vitest'
import {
  PERMISSIONS,
  ROLE_CODES,
  isAdminRole,
} from '@/constants/permissions'

describe('权限常量', () => {
  it('管理员角色使用后端大写编码', () => {
    expect(isAdminRole([ROLE_CODES.ADMIN])).toBe(true)
    expect(isAdminRole(['admin'])).toBe(false)
    expect(isAdminRole([ROLE_CODES.RECRUITER])).toBe(false)
  })

  it('权限码与后端种子保持一致', () => {
    expect(PERMISSIONS.JOBS_READ).toBe('jobs:read')
    expect(PERMISSIONS.JOBS_WRITE).toBe('jobs:write')
    expect(PERMISSIONS.RESUMES_WRITE).toBe('resumes:write')
    expect(PERMISSIONS.AI_EXECUTE).toBe('ai:execute')
    expect(PERMISSIONS.INTERVIEWS_SCHEDULE).toBe('interviews:schedule')
    expect(PERMISSIONS.INTERVIEWS_MANAGE).toBe('interviews:manage')
    expect(PERMISSIONS.SYSTEM_MANAGE).toBe('system:manage')
  })
})
