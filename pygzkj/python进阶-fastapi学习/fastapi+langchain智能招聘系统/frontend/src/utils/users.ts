import {
  PERMISSIONS,
  isAdminRole,
  type RoleCode,
} from '@/constants/permissions'
import type {
  SystemUser,
  UserCreatePayload,
  UserStatus,
  UserUpdatePayload,
} from '@/types/system'

export interface UserFormModel {
  username: string
  password: string
  real_name: string
  email: string
  phone: string
  department_id: number | null
  role_codes: RoleCode[]
  status: UserStatus
}

export function createEmptyUserForm(): UserFormModel {
  return {
    username: '',
    password: '',
    real_name: '',
    email: '',
    phone: '',
    department_id: null,
    role_codes: ['VIEWER'],
    status: 'ACTIVE',
  }
}

export function toUserForm(user: SystemUser): UserFormModel {
  return {
    username: user.username,
    password: '',
    real_name: user.real_name,
    email: user.email ?? '',
    phone: user.phone ?? '',
    department_id: user.department_id,
    role_codes: [...user.roles],
    status: user.status,
  }
}

export function buildUserCreatePayload(
  form: UserFormModel,
): UserCreatePayload {
  return {
    username: form.username.trim().toLowerCase(),
    password: form.password,
    real_name: form.real_name.trim(),
    email: normalizeOptionalText(form.email),
    phone: normalizeOptionalText(form.phone),
    department_id: form.department_id,
    role_codes: [...form.role_codes],
    status: form.status,
  }
}

export function buildUserUpdatePayload(
  form: UserFormModel,
): UserUpdatePayload {
  const payload: UserUpdatePayload = {
    real_name: form.real_name.trim(),
    email: normalizeOptionalText(form.email),
    phone: normalizeOptionalText(form.phone),
    department_id: form.department_id,
    role_codes: [...form.role_codes],
    status: form.status,
  }

  if (form.password) {
    payload.password = form.password
  }

  return payload
}

export function canManageUsers(
  roles: readonly string[] | undefined,
  permissions: readonly string[] | undefined,
): boolean {
  return (
    isAdminRole(roles) ||
    permissions?.includes(PERMISSIONS.SYSTEM_MANAGE) === true
  )
}

export function getRoleDisplayName(
  code: RoleCode,
  roleNames: ReadonlyMap<RoleCode, string>,
): string {
  return roleNames.get(code) ?? code
}

function normalizeOptionalText(value: string): string | null {
  const normalized = value.trim()
  return normalized || null
}
