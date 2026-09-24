import { request } from '@/api/http'
import type { PaginatedData } from '@/types/common'
import type {
  OperationLog,
  OperationLogQuery,
  Role,
  SystemUser,
  UserCreatePayload,
  UserDeleteResult,
  UserOption,
  UserQuery,
  UserUpdatePayload,
} from '@/types/system'
import { compactParams } from '@/utils/contracts'

export function fetchUsers(query: UserQuery): Promise<PaginatedData<SystemUser>> {
  return request<PaginatedData<SystemUser>>({
    url: '/users',
    method: 'GET',
    params: compactParams(query),
  })
}

export function fetchUser(userId: number): Promise<SystemUser> {
  return request<SystemUser>({
    url: `/users/${userId}`,
    method: 'GET',
  })
}

export function createUser(payload: UserCreatePayload): Promise<SystemUser> {
  return request<SystemUser>({
    url: '/users',
    method: 'POST',
    data: payload,
  })
}

export function updateUser(
  userId: number,
  payload: UserUpdatePayload,
): Promise<SystemUser> {
  return request<SystemUser>({
    url: `/users/${userId}`,
    method: 'PATCH',
    data: payload,
  })
}

export function deleteUser(userId: number): Promise<UserDeleteResult> {
  return request<UserDeleteResult>({
    url: `/users/${userId}`,
    method: 'DELETE',
  })
}

export function fetchUserOptions(params: {
  search?: string
  role_code?: string
  limit?: number
} = {}): Promise<UserOption[]> {
  return request<UserOption[]>({
    url: '/users/options',
    method: 'GET',
    params: compactParams({
      search: params.search ?? '',
      role_code: params.role_code,
      limit: params.limit ?? 200,
    }),
  })
}

export function fetchRoles(
  query: { page: number; page_size: number } = { page: 1, page_size: 100 },
): Promise<PaginatedData<Role>> {
  return request<PaginatedData<Role>>({
    url: '/roles',
    method: 'GET',
    params: compactParams(query),
  })
}

export function fetchOperationLogs(
  query: OperationLogQuery,
): Promise<PaginatedData<OperationLog>> {
  return request<PaginatedData<OperationLog>>({
    url: '/operation-logs',
    method: 'GET',
    params: compactParams(query),
  })
}
