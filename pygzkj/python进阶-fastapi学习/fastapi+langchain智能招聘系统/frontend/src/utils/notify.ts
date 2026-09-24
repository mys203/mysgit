import { ElMessage } from 'element-plus'

const recentMessages = new Map<string, number>()
const ERROR_DEDUPE_WINDOW_MS = 1200

export function notifyError(message: string): void {
  const now = Date.now()
  const lastShownAt = recentMessages.get(message) ?? 0

  if (now - lastShownAt < ERROR_DEDUPE_WINDOW_MS) {
    return
  }

  recentMessages.set(message, now)
  ElMessage.error(message)
}
