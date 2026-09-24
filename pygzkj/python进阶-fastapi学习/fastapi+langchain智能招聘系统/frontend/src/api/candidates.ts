import { request } from '@/api/http'
import type { PaginatedData } from '@/types/common'
import type {
  Application,
  ApplicationQuery,
  ApplicationStagePayload,
  Candidate,
  CandidatePayload,
  CandidateQuery,
} from '@/types/candidate'
import { compactParams } from '@/utils/contracts'

export function fetchCandidates(
  query: CandidateQuery,
): Promise<PaginatedData<Candidate>> {
  return request<PaginatedData<Candidate>>({
    url: '/candidates',
    method: 'GET',
    params: compactParams(query),
  })
}

export function fetchCandidate(id: number): Promise<Candidate> {
  return request<Candidate>({
    url: `/candidates/${id}`,
    method: 'GET',
  })
}

export function createCandidate(payload: CandidatePayload): Promise<Candidate> {
  return request<Candidate>({
    url: '/candidates',
    method: 'POST',
    data: payload,
  })
}

export function updateCandidate(
  id: number,
  payload: Partial<CandidatePayload>,
): Promise<Candidate> {
  return request<Candidate>({
    url: `/candidates/${id}`,
    method: 'PATCH',
    data: payload,
  })
}

export function deleteCandidate(id: number): Promise<void> {
  return request<void>({
    url: `/candidates/${id}`,
    method: 'DELETE',
  })
}

export function fetchApplications(
  query: ApplicationQuery,
): Promise<PaginatedData<Application>> {
  return request<PaginatedData<Application>>({
    url: '/applications',
    method: 'GET',
    params: compactParams(query),
  })
}

export function updateApplicationStage(
  id: number,
  payload: ApplicationStagePayload,
): Promise<Application> {
  return request<Application>({
    url: `/applications/${id}/stage`,
    method: 'PATCH',
    data: payload,
  })
}
