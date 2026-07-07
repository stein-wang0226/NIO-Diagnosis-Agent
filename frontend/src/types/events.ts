/** SSE 事件类型定义 */

/** 节点状态 */
export type NodeStatus = 'idle' | 'running' | 'completed' | 'skipped'

/** node_update 事件数据 */
export interface NodeUpdateEvent {
  node: string
  label: string
  fields: Record<string, unknown>
  retry_count: number
  is_relevant: boolean
}

/** done 事件数据 */
export interface DoneEvent {
  diagnosis_report: string
  retry_count: number
  is_relevant: boolean
  log_data_len: number
  retrieved_docs_len: number
  rule_check_result_len: number
}

/** error 事件数据 */
export interface ErrorEvent {
  error: string
}

/** Agent 配置信息 */
export interface AgentConfig {
  llm_provider: string
  llm_model: string
  embedding_provider: string
  max_retry_count: number
  examples: string[]
  node_labels: Record<string, string>
}

/** 节点定义（用于工作流可视化） */
export interface NodeDef {
  id: string
  label: string
  /** 节点在图中的位置 */
  position: { x: number; y: number }
  /** 阶段编号（1-4），0 表示辅助节点 */
  stage: number
}

/** 边定义 */
export interface EdgeDef {
  id: string
  source: string
  target: string
  label?: string
  /** 是否为条件边 */
  conditional?: boolean
  /** 是否为循环边 */
  loop?: boolean
}

/** 执行日志条目 */
export interface LogEntry {
  node: string
  label: string
  timestamp: number
  fields: Record<string, unknown>
  retry_count: number
  is_relevant: boolean
}
