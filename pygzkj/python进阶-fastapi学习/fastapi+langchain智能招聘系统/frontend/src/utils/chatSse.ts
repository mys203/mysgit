import type { ChatStreamEvent } from '@/types/chat'

interface ParsedFrame {
  data: string[]
  event: string
  id?: string
  retry?: number
}

const FRAME_SEPARATOR = /\r\n\r\n|\n\n|\r\r/
const LINE_SEPARATOR = /\r\n|\n|\r/

function parseFrame(frame: string): ChatStreamEvent | null {
  const parsed: ParsedFrame = {
    data: [],
    event: 'message',
  }

  for (const line of frame.split(LINE_SEPARATOR)) {
    if (!line || line.startsWith(':')) {
      continue
    }

    const separatorIndex = line.indexOf(':')
    const field = separatorIndex === -1 ? line : line.slice(0, separatorIndex)
    let value = separatorIndex === -1 ? '' : line.slice(separatorIndex + 1)

    if (value.startsWith(' ')) {
      value = value.slice(1)
    }

    if (field === 'data') {
      parsed.data.push(value)
    } else if (field === 'event') {
      parsed.event = value || 'message'
    } else if (field === 'id') {
      parsed.id = value
    } else if (field === 'retry' && /^\d+$/.test(value)) {
      parsed.retry = Number(value)
    }
  }

  if (parsed.data.length === 0) {
    return null
  }

  return {
    event: parsed.event,
    data: parsed.data.join('\n'),
    id: parsed.id,
    retry: parsed.retry,
  }
}

export class ChatSseParser {
  private buffer = ''

  push(chunk: string): ChatStreamEvent[] {
    this.buffer += chunk
    const events: ChatStreamEvent[] = []

    while (true) {
      const match = FRAME_SEPARATOR.exec(this.buffer)
      if (!match || match.index === undefined) {
        break
      }

      const frame = this.buffer.slice(0, match.index)
      this.buffer = this.buffer.slice(match.index + match[0].length)
      const event = parseFrame(frame)

      if (event) {
        events.push(event)
      }
    }

    return events
  }

  flush(): ChatStreamEvent[] {
    const remaining = this.buffer
    this.buffer = ''

    if (!remaining.trim()) {
      return []
    }

    const event = parseFrame(remaining)
    return event ? [event] : []
  }
}
