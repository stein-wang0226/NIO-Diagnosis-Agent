/**
 * 执行日志 - 现代化日志卡片
 */

import { useEffect, useRef } from 'react'
import type { LogEntry } from '../types/events'

/** 节点图标映射 */
const NODE_ICONS: Record<string, string> = {
  log_fetch: '📋',
  retrieve: '🔍',
  grade: '⚖️',
  rewrite: '✏️',
  rule_check: '✅',
  analyze: '🧠',
}

/** 节点颜色映射 */
const NODE_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  log_fetch:   { border: 'border-blue-500/20',    bg: 'bg-blue-500/5',    text: 'text-blue-300' },
  retrieve:    { border: 'border-violet-500/20',  bg: 'bg-violet-500/5',  text: 'text-violet-300' },
  grade:       { border: 'border-amber-500/20',   bg: 'bg-amber-500/5',   text: 'text-amber-300' },
  rewrite:     { border: 'border-orange-500/20',  bg: 'bg-orange-500/5',  text: 'text-orange-300' },
  rule_check:  { border: 'border-cyan-500/20',    bg: 'bg-cyan-500/5',    text: 'text-cyan-300' },
  analyze:     { border: 'border-emerald-500/20', bg: 'bg-emerald-500/5', text: 'text-emerald-300' },
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
      <div className="flex items-center justify-center h-full text-[var(--text-muted)] text-sm">
        <div className="text-center">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 text-[var(--text-muted)] opacity-50">
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
        const colors = NODE_COLORS[entry.node] || { border: 'border-[var(--border-subtle)]', bg: '', text: 'text-[var(--text-secondary)]' }
        const icon = NODE_ICONS[entry.node] || '•'
        const time = new Date(entry.timestamp).toLocaleTimeString('zh-CN', { hour12: false })
        const fieldSummary = getFieldSummary(entry)

        return (
          <div
            key={i}
            className={`rounded-xl border ${colors.border} ${colors.bg} px-4 py-3 animate-fade-in`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className={`font-semibold text-sm flex items-center gap-1.5 ${colors.text}`}>
                <span className="text-base">{icon}</span>
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
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                    : 'bg-amber-500/15 text-amber-400 border border-amber-500/25'
                }`}>
                  {entry.is_relevant ? '✓ 相关' : '✗ 不相关'}
                </span>
              </div>
            )}
            {entry.retry_count > 0 && (
              <span className="mt-1.5 inline-block text-[11px] px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/20">
                重试 #{entry.retry_count}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

/** 从状态字段中提取摘要信息 */
function getFieldSummary(entry: LogEntry): string {
  const fields = entry.fields
  const parts: string[] = []

  if ('log_data' in fields && typeof fields.log_data === 'string') {
    parts.push(`日志数据: ${fields.log_data.length} 字符`)
  }
  if ('retrieved_docs' in fields && typeof fields.retrieved_docs === 'string') {
    parts.push(`检索结果: ${fields.retrieved_docs.length} 字符`)
  }
  if ('rule_check_result' in fields && typeof fields.rule_check_result === 'string') {
    parts.push(`规则校验: ${fields.rule_check_result.length} 字符`)
  }
  if ('diagnosis_report' in fields && typeof fields.diagnosis_report === 'string') {
    parts.push(`诊断报告: ${fields.diagnosis_report.length} 字符`)
  }
  if ('rewritten_question' in fields && typeof fields.rewritten_question === 'string' && fields.rewritten_question) {
    parts.push(`改写后: ${fields.rewritten_question.slice(0, 50)}...`)
  }

  return parts.join(' · ')
}
