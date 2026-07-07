/**
 * App 主组件 - 现代化单栏布局
 *
 * 布局：Header → Input → 步骤条(紧凑) → Tabs(日志/报告)
 * 设计：玻璃态 + Indigo 主色 + 深色背景
 */

import { useState, useEffect, useCallback } from 'react'
import QuestionInput from './components/QuestionInput'
import StepIndicator from './components/StepIndicator'
import ExecutionLog from './components/ExecutionLog'
import DiagnosisReport from './components/DiagnosisReport'
import { fetchConfig, streamDiagnosis } from './api/client'
import type {
  AgentConfig,
  NodeStatus,
  NodeUpdateEvent,
  DoneEvent,
  LogEntry,
} from './types/events'

/** 节点顺序映射 */
function getNextNode(node: string, isRelevant: boolean, retryCount: number, maxRetry: number): string | null {
  if (node === 'log_fetch') return 'retrieve'
  if (node === 'retrieve') return 'grade'
  if (node === 'grade') {
    if (isRelevant || retryCount >= maxRetry) return 'rule_check'
    return 'rewrite'
  }
  if (node === 'rewrite') return 'retrieve'
  if (node === 'rule_check') return 'analyze'
  return null
}

const INITIAL_STATUSES: Record<string, NodeStatus> = {
  log_fetch: 'idle',
  retrieve: 'idle',
  grade: 'idle',
  rewrite: 'idle',
  rule_check: 'idle',
  analyze: 'idle',
}

export default function App() {
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, NodeStatus>>(INITIAL_STATUSES)
  const [logEntries, setLogEntries] = useState<LogEntry[]>([])
  const [result, setResult] = useState<DoneEvent | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState<'log' | 'report'>('log')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    fetchConfig()
      .then(setConfig)
      .catch((e) => setErrorMsg(`获取配置失败: ${e.message}`))
  }, [])

  const handleDiagnose = useCallback(
    async (question: string) => {
      setIsRunning(true)
      setResult(null)
      setErrorMsg('')
      setLogEntries([])
      setNodeStatuses({ ...INITIAL_STATUSES, log_fetch: 'running' })
      setActiveTab('log')

      await streamDiagnosis(question, {
        onNodeUpdate: (event: NodeUpdateEvent) => {
          setNodeStatuses((prev) => ({ ...prev, [event.node]: 'completed' }))
          setLogEntries((prev) => [
            ...prev,
            {
              node: event.node,
              label: event.label,
              timestamp: Date.now(),
              fields: event.fields,
              retry_count: event.retry_count,
              is_relevant: event.is_relevant,
            },
          ])
          const maxRetry = config?.max_retry_count ?? 3
          const next = getNextNode(event.node, event.is_relevant, event.retry_count, maxRetry)
          if (next) {
            setNodeStatuses((prev) => ({ ...prev, [next]: 'running' }))
          }
          if (event.node === 'analyze') {
            setActiveTab('report')
          }
        },
        onDone: (event: DoneEvent) => {
          setResult(event)
          setIsRunning(false)
          setNodeStatuses((prev) => ({ ...prev, analyze: 'completed' }))
          setActiveTab('report')
        },
        onError: (error: string) => {
          setErrorMsg(error)
          setIsRunning(false)
          setNodeStatuses((prev) => {
            const updated = { ...prev }
            for (const [k, v] of Object.entries(updated)) {
              if (v === 'running') updated[k] = 'idle'
            }
            return updated
          })
        },
      })
    },
    [config],
  )

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ─────────────────────────────────────── */}
      <header className="px-6 pt-5 pb-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo 图标 */}
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-[var(--text-primary)] tracking-tight">
                NIO Diagnosis Agent
              </h1>
              <p className="text-[11px] text-[var(--text-muted)]">
                蔚来效能平台 · AI 智能诊断
              </p>
            </div>
          </div>

          {config && (
            <div className="flex items-center gap-2 text-[11px]">
              <span className="px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200">
                {config.llm_model}
              </span>
              <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
                {config.embedding_provider}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* ── 输入区域 ──────────────────────────────────────── */}
      <section className="px-6 pb-4">
        <div className="max-w-5xl mx-auto">
          <QuestionInput
            examples={config?.examples || []}
            isRunning={isRunning}
            onSubmit={handleDiagnose}
          />
          {errorMsg && (
            <div className="mt-3 px-4 py-2.5 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs animate-fade-in">
              <span className="font-medium">错误：</span>{errorMsg}
            </div>
          )}
        </div>
      </section>

      {/* ── 步骤条（紧凑进度指示器）─────────────────────── */}
      {(isRunning || logEntries.length > 0) && (
        <section className="px-6 pb-3 animate-fade-in">
          <div className="max-w-5xl mx-auto">
            <div className="glass-card px-5 py-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                  执行进度
                </span>
                {isRunning && (
                  <span className="text-[11px] text-indigo-500 flex items-center gap-1.5">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                    运行中
                  </span>
                )}
                {!isRunning && logEntries.length > 0 && (
                  <span className="text-[11px] text-emerald-500 flex items-center gap-1.5">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    已完成
                  </span>
                )}
              </div>
              <StepIndicator nodeStatuses={nodeStatuses} />
            </div>
          </div>
        </section>
      )}

      {/* ── 主内容区：Tabs ──────────────────────────────────── */}
      <section className="flex-1 px-6 pb-6 flex flex-col min-h-0">
        <div className="max-w-5xl mx-auto w-full flex-1 flex flex-col min-h-0">
          <div className="glass-card flex-1 flex flex-col min-h-0 overflow-hidden">
            {/* Tab 切换 */}
            <div className="flex border-b border-[var(--border-subtle)] px-2">
              <button
                onClick={() => setActiveTab('log')}
                className={`
                  relative px-4 py-3 text-[13px] font-medium transition-colors
                  ${activeTab === 'log'
                    ? 'text-indigo-600 tab-active'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                  }
                `}
              >
                <span className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                  执行日志
                  {logEntries.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 rounded-full bg-slate-100 text-[10px] text-[var(--text-secondary)]">
                      {logEntries.length}
                    </span>
                  )}
                </span>
              </button>
              <button
                onClick={() => setActiveTab('report')}
                className={`
                  relative px-4 py-3 text-[13px] font-medium transition-colors
                  ${activeTab === 'report'
                    ? 'text-indigo-600 tab-active'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                  }
                `}
              >
                <span className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                  诊断报告
                </span>
              </button>
            </div>

            {/* Tab 内容 */}
            <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
              {activeTab === 'log' ? (
                <ExecutionLog entries={logEntries} />
              ) : (
                <DiagnosisReport result={result} isRunning={isRunning} />
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
