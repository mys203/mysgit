export const ROLE_CODES = {
  ADMIN: 'ADMIN',
  HR_MANAGER: 'HR_MANAGER',
  RECRUITER: 'RECRUITER',
  INTERVIEWER: 'INTERVIEWER',
  VIEWER: 'VIEWER',
} as const

export type RoleCode = (typeof ROLE_CODES)[keyof typeof ROLE_CODES]

export const PERMISSIONS = {
  SYSTEM_MANAGE: 'system:manage',
  JOBS_READ: 'jobs:read',
  JOBS_WRITE: 'jobs:write',
  RESUMES_READ: 'resumes:read',
  RESUMES_WRITE: 'resumes:write',
  CANDIDATES_READ: 'candidates:read',
  CANDIDATES_WRITE: 'candidates:write',
  APPLICATIONS_READ: 'applications:read',
  APPLICATIONS_WRITE: 'applications:write',
  AI_EXECUTE: 'ai:execute',
  INTERVIEWS_READ: 'interviews:read',
  INTERVIEWS_WRITE: 'interviews:write',
  INTERVIEWS_SCHEDULE: 'interviews:schedule',
  INTERVIEWS_MANAGE: 'interviews:manage',
  LOGS_READ: 'logs:read',
} as const

export type PermissionCode = (typeof PERMISSIONS)[keyof typeof PERMISSIONS]

export function isAdminRole(roles: readonly string[] | undefined): boolean {
  return roles?.includes(ROLE_CODES.ADMIN) === true
}
