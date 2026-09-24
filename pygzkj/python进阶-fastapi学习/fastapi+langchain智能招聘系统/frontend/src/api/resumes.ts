import { request } from '@/api/http'
import type { PaginatedData } from '@/types/common'
import type {
  ParseConfirmPayload,
  ParseConfirmResponse,
  ParseRecordQuery,
  ParseResultResponse,
  Resume,
  ResumeDetail,
  ResumeParseRecord,
  ResumeQuery,
} from '@/types/resume'

export function fetchResumes(query: ResumeQuery): Promise<PaginatedData<Resume>> {
  return request<PaginatedData<Resume>>({
    url: '/resumes',
    method: 'GET',
    params: query,
  })
}

export function fetchResume(id: number): Promise<ResumeDetail> {
  return request<ResumeDetail>({
    url: `/resumes/${id}`,
    method: 'GET',
  })
}

export function uploadResume(
  file: File,
  onProgress?: (percentage: number) => void,
): Promise<Resume> {
  const formData = new FormData()
  formData.append('file', file)

  return request<Resume>({
    url: '/resumes/upload',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (event) => {
      if (event.total && event.total > 0) {
        onProgress?.(Math.round((event.loaded / event.total) * 100))
      }
    },
  })
}

export function parseResume(id: number): Promise<ParseResultResponse> {
  return request<ParseResultResponse>({
    url: `/resumes/${id}/parse`,
    method: 'POST',
  })
}

export function fetchResumeParseRecords(
  id: number,
  query: ParseRecordQuery,
): Promise<PaginatedData<ResumeParseRecord>> {
  return request<PaginatedData<ResumeParseRecord>>({
    url: `/resumes/${id}/parse-records`,
    method: 'GET',
    params: query,
  })
}

export function fetchParseRecord(id: number): Promise<ResumeParseRecord> {
  return request<ResumeParseRecord>({
    url: `/parse-records/${id}`,
    method: 'GET',
  })
}

export function confirmParseRecord(
  id: number,
  payload: ParseConfirmPayload,
): Promise<ParseConfirmResponse> {
  return request<ParseConfirmResponse>({
    url: `/parse-records/${id}/confirm`,
    method: 'POST',
    data: payload,
  })
}
