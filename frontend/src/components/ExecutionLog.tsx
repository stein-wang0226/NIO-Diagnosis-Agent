/**
 * 执行日志 - SVG 图标 + 浅色主题
 */

import { useEffect, useRef } from 'react'
import type { LogEntry } from '../types/events'

/** SVG 图标 */
const NodeIcons: Record<string, () => JSX.Element> = {
  log_fetch: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  retrieve: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  grade: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" />
    </svg>
  ),
  rewrite: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  rule_check: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
  analyze: () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  ),
}

/** 节点颜色映射 */
const NODE_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  log_fetch:   { border: 'border-blue-200',    bg: 'bg-blue-50',    text: 'text-blue-600' },
  retrieve:    { border: 'border-violet-200',  bg: 'bg-violet-50',  text: 'text-violet-600' },
  grade:       { border: 'border-amber-200',   bg: 'bg-amber-50',   text: 'text-amber-600' },
  rewrite:     { border: 'border-orange-200',  bg: 'bg-orange-50',  text: 'text-orange-600' },
  rule_check:  { border: 'border-cyan-200',    bg: 'bg-cyan-50',    text: 'text-cyan-600' },
  analyze:     { border: 'border-emerald-200', bg: 'bg-emerald-50', text: 'text-emerald-600' },
}

export default function ExecutionLog({ entries }: { entries: LogEntry[] }) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [entries])

  if (entries.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-0 text-[var(--text-muted)] text-sm">
        <div className="text-center">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 text-slate-300">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          等待诊断开始...
        </div>
      </div>
    )
  }

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto p-4 space-y-2.5">
      {entries.map((entry, i) => {
        const colors = NODE_COLORS[entry.node] || { border: 'border-slate-200', bg: 'bg-white', text: 'text-slate-600' }
        const Icon = NodeIcons[entry.node]
        const time = new Date(entry.timestamp).toLocaleTimeString('zh-CN', { hour12: false })
        const fieldSummary = getFieldSummary(entry)

        return (
          <div
            key={i}
            className={`rounded-xl border ${colors.border} ${colors.bg} px-4 py-3 animate-fade-in`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className={`font-semibold text-sm flex items-center gap-2 ${colors.text}`}>
                {Icon && <Icon />}
                {entry.label}
              </span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">{time}</span>
            </div>
            {fieldSummary && (
              <div className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">{fieldSummary}</div>
            )}
            {entry.node === 'grade' && (
              <div className="mt-2 flex items-center gap-2">
                <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                  entry.is_relevant
                    ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                    : 'bg-amber-50 text-amber-600 border border-amber-200'
                }`}>
                  {entry.is_relevant ? '✓ 相关' : '✗ 不相关'}
                </span>
              </div>
            )}
            {entry.retry_count > 0 && (
              <span className="mt-1.5 inline-block text-[11px] px-2 py-0.5 rounded-full bg-orange-50 text-orange-600 border border-orange-200">
                重试 #{entry.retry_count}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function getFieldSummary(entry: LogEntry): string {
  const fields = entry.fields
  const parts: string[] = []
  if ('log_data' in fields && typeof fields.log_data === 'string')
    parts.push(`日志数据: ${fields.log_data.length} 字符`)
  if ('retrieved_docs' in fields && typeof fields.retrieved_docs === 'string')
    parts.push(`检索结果: ${fields.retrieved_docs.length} 字符`)
  if ('rule_check_result' in fields && typeof fields.rule_check_result === 'string')
    parts.push(`规则校验: ${fields.rule_check_result.length} 字符`)
  if ('diagnosis_report' in fields && typeof fields.diagnosis_report === 'string')
    parts.push(`诊断报告: ${fields.diagnosis_report.length} 字符`)
  if ('rewritten_question' in fields && typeof fields.rewritten_question === 'string' && fields.rewritten_question)
    parts.push(`改写后: ${fields.rewritten_question.slice(0, 50)}...`)
  return parts.join(' · ')
}
