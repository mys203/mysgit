import { request } from '@/api/http'
import type { PaginatedData } from '@/types/common'
import type {
  Department,
  DepartmentOption,
  Job,
  JobCategory,
  JobCreatePayload,
  JobQuery,
  JobUpdatePayload,
  PaginationQuery,
} from '@/types/job'
import type { MatchResult } from '@/types/ai'
import { compactParams } from '@/utils/contracts'

export function fetchJobs(query: JobQuery): Promise<PaginatedData<Job>> {
  return request<PaginatedData<Job>>({
    url: '/jobs',
    method: 'GET',
    params: compactParams(query),
  })
}

export function fetchJob(id: number): Promise<Job> {
  return request<Job>({
    url: `/jobs/${id}`,
    method: 'GET',
  })
}

export function createJob(payload: JobCreatePayload): Promise<Job> {
  return request<Job>({
    url: '/jobs',
    method: 'POST',
    data: payload,
  })
}

export function updateJob(id: number, payload: JobUpdatePayload): Promise<Job> {
  return request<Job>({
    url: `/jobs/${id}`,
    method: 'PATCH',
    data: payload,
  })
}

export function deleteJob(id: number): Promise<void> {
  return request<void>({
    url: `/jobs/${id}`,
    method: 'DELETE',
  })
}

export function publishJob(id: number): Promise<Job> {
  return request<Job>({
    url: `/jobs/${id}/publish`,
    method: 'POST',
  })
}

export function closeJob(id: number): Promise<Job> {
  return request<Job>({
    url: `/jobs/${id}/close`,
    method: 'POST',
  })
}

export function fetchJobMatches(id: number): Promise<MatchResult[]> {
  return request<MatchResult[]>({
    url: `/jobs/${id}/matches`,
    method: 'GET',
  })
}

export function fetchJobCategories(
  query: PaginationQuery = { page: 1, page_size: 100 },
): Promise<PaginatedData<JobCategory>> {
  return request<PaginatedData<JobCategory>>({
    url: '/job-categories',
    method: 'GET',
    params: query,
  })
}

export function fetchDepartments(
  query: PaginationQuery = { page: 1, page_size: 100 },
): Promise<PaginatedData<Department>> {
  return request<PaginatedData<Department>>({
    url: '/departments',
    method: 'GET',
    params: query,
  })
}

export function fetchDepartmentOptions(
  search = '',
  limit = 200,
): Promise<DepartmentOption[]> {
  return request<DepartmentOption[]>({
    url: '/departments/options',
    method: 'GET',
    params: compactParams({ search, limit }),
  })
}
