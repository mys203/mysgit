import axios from 'axios'
import type { ApiResponse } from '@/types/common'

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiResponse<unknown>>(error)) {
    return (
      error.response?.data?.message ||
      error.message ||
      '网络请求失败，请稍后重试'
    )
  }

  if (error instanceof Error) {
    return error.message
  }

  return '操作失败，请稍后重试'
}
