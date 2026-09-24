import { onScopeDispose, ref, type Ref } from 'vue'
import type { AiTask } from '@/types/common'

type TaskOutput = object

export class AiTaskFailedError<TOutput extends TaskOutput> extends Error {
  readonly task: AiTask<TOutput>

  constructor(task: AiTask<TOutput>) {
    const errorCode = task.error_code ? `[${task.error_code}] ` : ''
    super(`${errorCode}${task.error_message || 'AI 任务执行失败'}`)
    this.name = 'AiTaskFailedError'
    this.task = task
  }
}

export class AiTaskCancelledError extends Error {
  constructor() {
    super('AI 任务轮询已取消')
    this.name = 'AiTaskCancelledError'
  }
}

export class AiTaskTimeoutError extends Error {
  constructor() {
    super('AI 任务执行超时，请稍后重试')
    this.name = 'AiTaskTimeoutError'
  }
}

interface PollAiTaskOptions<TOutput extends TaskOutput> {
  taskNo: string
  getTask: (taskNo: string) => Promise<AiTask<TOutput>>
  intervalMs?: number
  timeoutMs?: number
  signal?: AbortSignal
  onUpdate?: (task: AiTask<TOutput>) => void
  wait?: (milliseconds: number, signal?: AbortSignal) => Promise<void>
}

function abortError(): AiTaskCancelledError {
  return new AiTaskCancelledError()
}

function defaultWait(milliseconds: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(abortError())
      return
    }

    const timer = globalThis.setTimeout(resolve, milliseconds)
    signal?.addEventListener(
      'abort',
      () => {
        globalThis.clearTimeout(timer)
        reject(abortError())
      },
      { once: true },
    )
  })
}

export async function pollAiTask<TOutput extends TaskOutput>(
  options: PollAiTaskOptions<TOutput>,
): Promise<AiTask<TOutput>> {
  const intervalMs = options.intervalMs ?? 1500
  const timeoutMs = options.timeoutMs ?? 120000
  const wait = options.wait ?? defaultWait
  const startedAt = Date.now()

  while (true) {
    if (options.signal?.aborted) {
      throw abortError()
    }

    const task = await options.getTask(options.taskNo)
    options.onUpdate?.(task)

    if (task.status === 'SUCCEEDED') {
      return task
    }

    if (task.status === 'FAILED') {
      throw new AiTaskFailedError(task)
    }

    const elapsed = Date.now() - startedAt
    if (elapsed >= timeoutMs) {
      throw new AiTaskTimeoutError()
    }

    await wait(Math.min(intervalMs, Math.max(1, timeoutMs - elapsed)), options.signal)
  }
}

export function useAiTaskPolling<TOutput extends TaskOutput>() {
  const task = ref<AiTask<TOutput> | null>(null) as Ref<AiTask<TOutput> | null>
  const polling = ref(false)
  let controller: AbortController | null = null

  function stop(): void {
    controller?.abort()
    controller = null
    polling.value = false
  }

  async function start(
    options: Omit<PollAiTaskOptions<TOutput>, 'signal' | 'onUpdate'>,
  ): Promise<AiTask<TOutput>> {
    stop()
    controller = new AbortController()
    polling.value = true

    try {
      return await pollAiTask({
        ...options,
        signal: controller.signal,
        onUpdate: (nextTask) => {
          task.value = nextTask
        },
      })
    } finally {
      polling.value = false
      controller = null
    }
  }

  onScopeDispose(stop)

  return {
    task,
    polling,
    start,
    stop,
  }
}
