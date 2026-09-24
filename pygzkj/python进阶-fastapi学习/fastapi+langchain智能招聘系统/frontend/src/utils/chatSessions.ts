import type { RouteLocationRaw } from 'vue-router'
import type {
  ChatCitation,
  ChatContext,
  ChatMessage,
  ChatMessageId,
  ChatMessagePage,
  ChatMessageRole,
  ChatMessageStatus,
  ChatSession,
  ChatSessionPage,
  ChatStreamEvent,
} from '@/types/chat'

export type UnknownRecord = Record<string, unknown>

export function isUnknownRecord(value: unknown): value is UnknownRecord {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

export function readRecord(
  record: UnknownRecord,
  keys: readonly string[],
): UnknownRecord | null {
  for (const key of keys) {
    const value = record[key]
    if (isUnknownRecord(value)) {
      return value
    }
  }

  return null
}

export function readString(
  record: UnknownRecord,
  keys: readonly string[],
): string | undefined {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'string') {
      return value
    }
    if (typeof value === 'number') {
      return String(value)
    }
  }

  return undefined
}

export function readNumber(
  record: UnknownRecord,
  keys: readonly string[],
): number | undefined {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value
    }
    if (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value))) {
      return Number(value)
    }
  }

  return undefined
}

export function readBoolean(
  record: UnknownRecord,
  keys: readonly string[],
): boolean | undefined {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'boolean') {
      return value
    }
  }

  return undefined
}

export function readMessageId(
  record: UnknownRecord,
  keys: readonly string[],
): ChatMessageId | undefined {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'number' || typeof value === 'string') {
      return value
    }
  }

  return undefined
}

export function parseChatSseData(event: ChatStreamEvent): UnknownRecord {
  if (!event.data) {
    return {}
  }

  try {
    const parsed: unknown = JSON.parse(event.data)
    if (isUnknownRecord(parsed)) {
      return parsed
    }
    if (typeof parsed === 'string') {
      return { content: parsed }
    }
  } catch {
    return { content: event.data }
  }

  return { content: event.data }
}

export function createChatRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  return `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function buildChatSessionTitle(content: string, maxLength = 26): string {
  const normalized = content.replace(/\s+/g, ' ').trim()
  if (!normalized) {
    return '新会话'
  }

  return normalized.length > maxLength
    ? `${normalized.slice(0, maxLength)}...`
    : normalized
}

export function normalizeChatContext(value: unknown): ChatContext {
  if (!isUnknownRecord(value)) {
    return {}
  }

  const context: ChatContext = {}
  const jobId = readContextId(value, 'job_id')
  const candidateId = readContextId(value, 'candidate_id')
  const resumeId = readContextId(value, 'resume_id')

  if (jobId !== undefined) {
    context.job_id = jobId
  }
  if (candidateId !== undefined) {
    context.candidate_id = candidateId
  }
  if (resumeId !== undefined) {
    context.resume_id = resumeId
  }

  return context
}

export function mergeChatContexts(
  primary: ChatContext,
  fallback: ChatContext,
): ChatContext {
  return {
    ...fallback,
    ...primary,
  }
}

function readContextId(
  value: UnknownRecord,
  key: string,
): number | null | undefined {
  if (!Object.prototype.hasOwnProperty.call(value, key)) {
    return undefined
  }

  const id = readNumber(value, [key])
  return id && id > 0 ? id : null
}

export function normalizeCitation(value: unknown): ChatCitation | null {
  if (!isUnknownRecord(value)) {
    return null
  }

  const title =
    readString(value, ['title', 'name', 'label']) ||
    readString(value, ['source_type', 'type']) ||
    '引用依据'

  return {
    id: readMessageId(value, ['id', 'citation_id']),
    source_type: readString(value, ['source_type', 'type', 'resource_type']),
    title,
    snippet: readString(value, ['snippet', 'content', 'excerpt']) ?? null,
    reference_id:
      readNumber(value, ['reference_id', 'target_id', 'source_id']) ?? null,
    job_id: readNumber(value, ['job_id']) ?? null,
    candidate_id: readNumber(value, ['candidate_id']) ?? null,
    resume_id: readNumber(value, ['resume_id']) ?? null,
    match_result_id: readNumber(value, ['match_result_id']) ?? null,
    interview_question_id: readNumber(value, ['interview_question_id', 'question_id']) ?? null,
    route: readString(value, ['route', 'path']) ?? null,
  }
}

export function normalizeCitations(value: unknown): ChatCitation[] {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((item) => normalizeCitation(item))
    .filter((item): item is ChatCitation => item !== null)
}

function normalizeRole(value: unknown): ChatMessageRole {
  const role = typeof value === 'string' ? value.toUpperCase() : ''
  if (role === 'USER' || role === 'ASSISTANT' || role === 'SYSTEM') {
    return role
  }

  return 'ASSISTANT'
}

export function normalizeChatMessageStatus(value: unknown): ChatMessageStatus {
  const status = typeof value === 'string' ? value.toUpperCase() : ''

  if (status === 'SUCCESS' || status === 'SUCCEEDED') {
    return 'COMPLETED'
  }
  if (status === 'CANCELED') {
    return 'CANCELLED'
  }
  if (
    status === 'PENDING' ||
    status === 'STREAMING' ||
    status === 'COMPLETED' ||
    status === 'STOPPED' ||
    status === 'CANCELLED' ||
    status === 'FAILED'
  ) {
    return status
  }

  return 'UNKNOWN'
}

export function resolveDoneMessageStatus(data: UnknownRecord): ChatMessageStatus {
  const status = readString(data, ['status'])
  return status ? normalizeChatMessageStatus(status) : 'COMPLETED'
}

function normalizeProgress(value: unknown): ChatMessage['progress'] {
  if (!isUnknownRecord(value)) {
    return null
  }

  return {
    stage: readString(value, ['stage', 'phase']),
    message: readString(value, ['message', 'text', 'status']),
    percent: readNumber(value, ['percent', 'progress']) ?? null,
  }
}

export function normalizeChatMessage(
  value: unknown,
  sessionId: number,
  index = 0,
): ChatMessage | null {
  if (!isUnknownRecord(value)) {
    return null
  }

  const sequence =
    readNumber(value, [
      'sequence_no',
      'sequence',
      'seq',
      'message_sequence',
    ]) ?? 0
  const id =
    readMessageId(value, ['id', 'message_id']) ??
    `message-${sessionId}-${sequence}-${index}`

  return {
    id,
    session_id: readNumber(value, ['session_id']) ?? sessionId,
    role: normalizeRole(value.role),
    content: readString(value, ['content', 'text', 'answer']) ?? '',
    sequence,
    status: normalizeChatMessageStatus(value.status),
    citations: normalizeCitations(value.citations),
    created_at:
      readString(value, ['created_at', 'created_time', 'timestamp']) ||
      new Date().toISOString(),
    updated_at: readString(value, ['updated_at']) ?? null,
    assistant_id: readString(value, ['assistant_id']) ?? null,
    client_id: readString(value, ['client_id', 'client_message_id']) ?? null,
    request_id: readString(value, ['request_id', 'idempotency_key']) ?? null,
    error_message: readString(value, ['error_message', 'error']) ?? null,
    progress: normalizeProgress(value.progress),
    degraded: readBoolean(value, ['degraded']) ?? false,
  }
}

export function normalizeChatMessagePage(
  value: unknown,
  sessionId: number,
): ChatMessagePage {
  if (Array.isArray(value)) {
    const items = value
      .map((item, index) => normalizeChatMessage(item, sessionId, index))
      .filter((item): item is ChatMessage => item !== null)
      .sort((left, right) => left.sequence - right.sequence)

    return {
      items,
      total: items.length,
      page: 1,
      page_size: items.length,
      has_more: false,
      next_before_sequence: null,
    }
  }

  const record = isUnknownRecord(value) ? value : {}
  const rawItems = Array.isArray(record.items) ? record.items : []
  const pageSize = readNumber(record, ['page_size', 'limit']) ?? rawItems.length
  const items = rawItems
    .map((item, index) => normalizeChatMessage(item, sessionId, index))
    .filter((item): item is ChatMessage => item !== null)
    .sort((left, right) => left.sequence - right.sequence)
  const firstSequence = items[0]?.sequence

  return {
    items,
    total: readNumber(record, ['total']) ?? items.length,
    page: readNumber(record, ['page']) ?? 1,
    page_size: pageSize,
    has_more:
      readBoolean(record, ['has_more']) ??
      (typeof firstSequence === 'number' ? firstSequence > 1 : false),
    next_before_sequence:
      readNumber(record, [
        'next_before_sequence',
        'before_sequence',
        'next_sequence',
      ]) ??
      (typeof firstSequence === 'number' ? firstSequence : null),
  }
}

export function normalizeChatSession(value: unknown): ChatSession | null {
  if (!isUnknownRecord(value)) {
    return null
  }

  const id = readNumber(value, ['id', 'session_id'])
  if (!id || id <= 0) {
    return null
  }

  const createdAt = readString(value, ['created_at']) || new Date().toISOString()
  const nestedContext = normalizeChatContext(
    readRecord(value, ['context', 'chat_context']),
  )
  const context = { ...nestedContext }
  const topLevelJobId = readContextId(value, 'job_id')
  const topLevelCandidateId = readContextId(value, 'candidate_id')
  const topLevelResumeId = readContextId(value, 'resume_id')

  if (topLevelJobId !== undefined) {
    context.job_id = topLevelJobId
  }
  if (topLevelCandidateId !== undefined) {
    context.candidate_id = topLevelCandidateId
  }
  if (topLevelResumeId !== undefined) {
    context.resume_id = topLevelResumeId
  }

  return {
    id,
    title: readString(value, ['title', 'name']) || '新会话',
    context,
    created_at: createdAt,
    updated_at: readString(value, ['updated_at']) || createdAt,
    last_message_at:
      readString(value, ['last_message_at', 'latest_message_at']) ?? null,
    message_count: readNumber(value, ['message_count', 'messages_count']) ?? 0,
  }
}

export function normalizeChatSessionPage(value: unknown): ChatSessionPage {
  if (Array.isArray(value)) {
    const items = value
      .map((item) => normalizeChatSession(item))
      .filter((item): item is ChatSession => item !== null)

    return {
      items,
      total: items.length,
      page: 1,
      page_size: items.length,
    }
  }

  const record = isUnknownRecord(value) ? value : {}
  const rawItems = Array.isArray(record.items) ? record.items : []
  const items = rawItems
    .map((item) => normalizeChatSession(item))
    .filter((item): item is ChatSession => item !== null)

  return {
    items,
    total: readNumber(record, ['total']) ?? items.length,
    page: readNumber(record, ['page']) ?? 1,
    page_size: readNumber(record, ['page_size', 'limit']) ?? items.length,
  }
}

function sameMessage(left: ChatMessage, right: ChatMessage): boolean {
  if (left.id === right.id) {
    return true
  }

  if (left.client_id && right.client_id && left.client_id === right.client_id) {
    return true
  }

  if (left.request_id && right.request_id && left.role === right.role) {
    return left.request_id === right.request_id
  }

  return Boolean(
    left.assistant_id &&
      right.assistant_id &&
      left.assistant_id === right.assistant_id,
  )
}

export function mergeChatCitations(
  current: ChatCitation[],
  incoming: ChatCitation[],
): ChatCitation[] {
  const result = [...current]

  for (const citation of incoming) {
    const key =
      citation.id ??
      `${getCitationTypeLabel(citation)}-${citation.reference_id ?? citation.title}`
    const exists = result.some((item) => {
      const itemKey =
        item.id ??
        `${getCitationTypeLabel(item)}-${item.reference_id ?? item.title}`
      return itemKey === key
    })

    if (!exists) {
      result.push(citation)
    }
  }

  return result
}

function mergeMessage(current: ChatMessage, incoming: ChatMessage): ChatMessage {
  return {
    ...current,
    ...incoming,
    id: incoming.id || current.id,
    content: incoming.content || current.content,
    citations: mergeChatCitations(current.citations, incoming.citations),
    progress: incoming.progress ?? current.progress,
    assistant_id: incoming.assistant_id ?? current.assistant_id,
    client_id: incoming.client_id ?? current.client_id,
    request_id: incoming.request_id ?? current.request_id,
    error_message: incoming.error_message ?? current.error_message,
  }
}

export function upsertChatMessages(
  current: readonly ChatMessage[],
  incoming: readonly ChatMessage[],
): ChatMessage[] {
  const result = [...current]

  for (const message of incoming) {
    const index = result.findIndex((item) => sameMessage(item, message))
    if (index === -1) {
      result.push(message)
    } else {
      result[index] = mergeMessage(result[index], message)
    }
  }

  return result.sort((left, right) => left.sequence - right.sequence)
}

export function resolveHistoryBeforeSequence(
  nextBeforeSequence: number | null | undefined,
  firstMessageSequence: number | undefined,
): number | undefined {
  if (
    typeof nextBeforeSequence === 'number' &&
    Number.isFinite(nextBeforeSequence) &&
    nextBeforeSequence > 0
  ) {
    return nextBeforeSequence
  }

  if (
    typeof firstMessageSequence === 'number' &&
    Number.isFinite(firstMessageSequence) &&
    firstMessageSequence > 0
  ) {
    return firstMessageSequence
  }

  return undefined
}

export function getCitationTypeLabel(citation: ChatCitation): string {
  const sourceType = citation.source_type?.toUpperCase() ?? ''

  if (sourceType.includes('JOB')) {
    return '岗位'
  }
  if (sourceType.includes('CANDIDATE')) {
    return '候选人'
  }
  if (sourceType.includes('RESUME')) {
    return '简历'
  }
  if (sourceType.includes('MATCH')) {
    return '匹配结果'
  }
  if (sourceType.includes('QUESTION') || sourceType.includes('INTERVIEW')) {
    return '面试题'
  }

  return '资料'
}

function isSafeInternalRoute(route: string): boolean {
  return route.startsWith('/') && !route.startsWith('//')
}

export function buildCitationRoute(citation: ChatCitation): RouteLocationRaw | null {
  if (citation.route && isSafeInternalRoute(citation.route)) {
    return citation.route
  }

  const sourceType = citation.source_type?.toUpperCase() ?? ''
  const referenceId = citation.reference_id

  if (sourceType.includes('JOB') && (citation.job_id || referenceId)) {
    return {
      path: '/jobs/create',
      query: { id: String(citation.job_id ?? referenceId) },
    }
  }

  if (sourceType.includes('CANDIDATE') && (citation.candidate_id || referenceId)) {
    return {
      path: '/candidates',
      query: { candidate_id: String(citation.candidate_id ?? referenceId) },
    }
  }

  if (sourceType.includes('RESUME') && (citation.resume_id || referenceId)) {
    return {
      path: '/resumes',
      query: { resume_id: String(citation.resume_id ?? referenceId) },
    }
  }

  if (sourceType.includes('MATCH')) {
    return {
      path: '/ai/matches',
      query: {
        ...(citation.job_id ? { job_id: String(citation.job_id) } : {}),
        ...(citation.candidate_id
          ? { candidate_id: String(citation.candidate_id) }
          : {}),
      },
    }
  }

  if (sourceType.includes('QUESTION') || sourceType.includes('INTERVIEW')) {
    return {
      path: '/ai/interview-questions',
      query: citation.interview_question_id
        ? { question_id: String(citation.interview_question_id) }
        : undefined,
    }
  }

  return null
}

export function getChatQuickPrompts(context: ChatContext): string[] {
  const hasJob = Boolean(context.job_id)
  const hasCandidate = Boolean(context.candidate_id)

  if (hasJob && hasCandidate) {
    return [
      '评估这位候选人与岗位的匹配情况',
      '列出候选人的优势与风险',
      '生成针对性的面试追问',
    ]
  }

  if (hasJob) {
    return [
      '提炼这个岗位的核心能力',
      '生成候选人筛选标准',
      '给出面试考察重点',
    ]
  }

  if (hasCandidate) {
    return [
      '总结候选人的核心优势',
      '分析候选人的潜在风险',
      '推荐适合候选人的岗位方向',
    ]
  }

  return [
    '如何写一份高质量的岗位描述？',
    '如何快速筛选匹配的简历？',
    '如何设计结构化面试流程？',
  ]
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}
