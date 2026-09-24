import { request } from '@/api/http'
import type { DashboardSummary } from '@/types/system'

export function fetchDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>({
    url: '/dashboard/summary',
    method: 'GET',
  })
}
