import { describe, expect, it, vi } from 'vitest'
import type { AiTask, AiTaskStatus } from '@/types/common'
import { pollAiTask } from '@/utils/aiTaskPolling'

interface MatchOutput {
  task_no: string
  items: Array<{ candidate_id: number; score: number }>
}

function createTask(
  status: AiTaskStatus,
  outputPayload: MatchOutput | null = null,
): AiTask<MatchOutput> {
  return {
    id: 1,
    task_no: 'AI-TEST-001',
    task_type: 'JOB_MATCH',
    status,
    provider: 'local',
    model_name: null,
    output_payload: outputPayload,
    error_message: null,
    degraded: false,
    started_at: null,
    finished_at: null,
    created_at: '2026-09-20T08:00:00Z',
    updated_at: '2026-09-20T08:00:00Z',
  }
}

describe('AI 任务轮询器', () => {
  it('按 PENDING、RUNNING、SUCCEEDED 轮询并返回 output_payload', async () => {
    const output: MatchOutput = {
      task_no: 'AI-TEST-001',
      items: [{ candidate_id: 8, score: 88 }],
    }
    const getTask = vi
      .fn()
      .mockResolvedValueOnce(createTask('PENDING'))
      .mockResolvedValueOnce(createTask('RUNNING'))
      .mockResolvedValueOnce(createTask('SUCCEEDED', output))
    const updates: AiTaskStatus[] = []

    const task = await pollAiTask<MatchOutput>({
      taskNo: 'AI-TEST-001',
      getTask,
      wait: async () => undefined,
      onUpdate: (value) => updates.push(value.status),
    })

    expect(updates).toEqual(['PENDING', 'RUNNING', 'SUCCEEDED'])
    expect(task.output_payload).toEqual(output)
    expect(task.output_payload?.items[0]?.score).toBe(88)
    expect(getTask).toHaveBeenCalledTimes(3)
  })

  it('FAILED 时抛出包含 error_code 和 error_message 的错误', async () => {
    const getTask = vi.fn().mockResolvedValue({
      ...createTask('FAILED'),
      error_code: 'AI_TASK_FAILED',
      error_message: '模型调用失败',
    })

    await expect(
      pollAiTask<MatchOutput>({
        taskNo: 'AI-TEST-001',
        getTask,
        wait: async () => undefined,
      }),
    ).rejects.toThrow('[AI_TASK_FAILED] 模型调用失败')
  })
})
