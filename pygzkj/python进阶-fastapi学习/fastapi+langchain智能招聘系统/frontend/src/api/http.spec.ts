import { describe, expect, it } from 'vitest'
import {
  AuthenticationExpiredError,
  shouldExpireSessionAfterRefreshError,
} from '@/api/http'

describe('authentication refresh errors', () => {
  it('普通网络错误与 Abort 不触发会话过期', () => {
    expect(
      shouldExpireSessionAfterRefreshError(new TypeError('Network Error')),
    ).toBe(false)
    expect(
      shouldExpireSessionAfterRefreshError(
        new DOMException('The operation was aborted', 'AbortError'),
      ),
    ).toBe(false)
  })

  it('refresh 明确失效时触发会话过期', () => {
    expect(
      shouldExpireSessionAfterRefreshError(
        new AuthenticationExpiredError('refresh token invalid'),
      ),
    ).toBe(true)
  })
})
