/**
 * API 客户端 - 与后端 FastAPI 交互
 *
 * 核心功能：通过 fetch + ReadableStream 消费 POST /api/diagnose 的 SSE 流。
 * 标准 EventSource API 只支持 GET，所以需要手动解析 SSE 格式。
 */

import type {
  AgentConfig,
  NodeUpdateEvent,
  DoneEvent,
} from '../types/events'

/** 获取 Agent 配置 */
export async function fetchConfig(): Promise<AgentConfig> {
  const res = await fetch('/api/config')
  if (!res.ok) throw new Error(`获取配置失败: ${res.status}`)
  return res.json()
}

/** SSE 回调接口 */
export interface SSECallbacks {
  onNodeUpdate: (event: NodeUpdateEvent) => void
  onDone: (event: DoneEvent) => void
  onError: (error: string) => void
}

/**
 * 流式诊断 - POST /api/diagnose，消费 SSE 流
 *
 * SSE 格式：
 *   event: node_update\n
 *   data: {"node": "...", ...}\n
 *   \n
 */
export async function streamDiagnosis(
  question: string,
  callbacks: SSECallbacks,
): Promise<void> {
  const response = await fetch('/api/diagnose', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

  if (!response.ok) {
    callbacks.onError(`HTTP ${response.status}: ${response.statusText}`)
    return
  }

  if (!response.body) {
    callbacks.onError('响应体为空')
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE 事件以双换行分隔
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const eventText of events) {
        const parsed = parseSSEEvent(eventText)
        if (!parsed) continue

        if (parsed.event === 'node_update') {
          callbacks.onNodeUpdate(parsed.data as NodeUpdateEvent)
        } else if (parsed.event === 'done') {
          callbacks.onDone(parsed.data as DoneEvent)
        } else if (parsed.event === 'error') {
          callbacks.onError((parsed.data as { error: string }).error)
        }
      }
    }
  } catch (err) {
    callbacks.onError(err instanceof Error ? err.message : String(err))
  }
}

/** 解析单个 SSE 事件文本 */
function parseSSEEvent(
  text: string,
): { event: string; data: unknown } | null {
  let eventType = 'message'
  let dataStr = ''

  for (const line of text.split('\n')) {
    if (line.startsWith('event: ')) {
      eventType = line.slice(7).trim()
    } else if (line.startsWith('data: ')) {
      dataStr += line.slice(6)
    }
  }

  if (!dataStr) return null

  try {
    return { event: eventType, data: JSON.parse(dataStr) }
  } catch {
    return null
  }
}
