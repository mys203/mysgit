import { describe, expect, it } from 'vitest'
import { ROLE_CODES } from '@/constants/permissions'
import {
  buildUserCreatePayload,
  buildUserUpdatePayload,
  canManageUsers,
  createEmptyUserForm,
} from '@/utils/users'

describe('用户管理工具', () => {
  it('构造创建用户 payload 并清理可选字段', () => {
    const payload = buildUserCreatePayload({
      ...createEmptyUserForm(),
      username: '  New.User  ',
      password: 'password123',
      real_name: '  新用户  ',
      email: '  new.user@example.com  ',
      phone: '   ',
      department_id: 8,
      role_codes: [ROLE_CODES.RECRUITER, ROLE_CODES.INTERVIEWER],
    })

    expect(payload).toEqual({
      username: 'new.user',
      password: 'password123',
      real_name: '新用户',
      email: 'new.user@example.com',
      phone: null,
      department_id: 8,
      role_codes: [ROLE_CODES.RECRUITER, ROLE_CODES.INTERVIEWER],
      status: 'ACTIVE',
    })
  })

  it('编辑时留空密码表示不修改', () => {
    const form = {
      ...createEmptyUserForm(),
      username: 'recruiter',
      real_name: '招聘专员',
      email: '',
      phone: '',
      role_codes: [ROLE_CODES.RECRUITER],
    }

    expect(buildUserUpdatePayload(form)).not.toHaveProperty('password')
    expect(buildUserUpdatePayload({ ...form, password: 'newpassword' })).toHaveProperty(
      'password',
      'newpassword',
    )
  })

  it('管理员或具备系统管理权限时显示用户操作', () => {
    expect(canManageUsers([ROLE_CODES.ADMIN], [])).toBe(true)
    expect(canManageUsers([ROLE_CODES.HR_MANAGER], ['system:manage'])).toBe(true)
    expect(canManageUsers([ROLE_CODES.VIEWER], ['jobs:read'])).toBe(false)
  })
})
