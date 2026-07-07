/**
 * 诊断报告展示 - 现代卡片样式 + react-markdown
 */

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { DoneEvent } from '../types/events'

export default function DiagnosisReport({
  result,
  isRunning,
}: {
  result: DoneEvent | null
  isRunning: boolean
}) {
  if (isRunning && !result) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="relative inline-block mb-4">
            <div className="w-10 h-10 rounded-full border-2 border-indigo-500/30 border-t-indigo-500 animate-spin" />
          </div>
          <div className="text-[var(--text-secondary)] text-sm">AI 正在分析并生成诊断报告...</div>
          <div className="text-[var(--text-muted)] text-xs mt-1">通常需要 10-30 秒</div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-muted)] text-sm">
        <div className="text-center">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 opacity-50">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
          诊断完成后将在此显示报告
        </div>
      </div>
    )
  }

  const stats = [
    { label: '评分结果', value: result.is_relevant ? '✓ 相关' : '✗ 不相关', color: result.is_relevant ? 'text-emerald-400' : 'text-amber-400' },
    { label: '重试次数', value: `${result.retry_count}`, color: 'text-[var(--text-primary)]' },
    { label: '日志数据', value: `${result.log_data_len} 字符`, color: 'text-[var(--text-primary)]' },
    { label: '检索结果', value: `${result.retrieved_docs_len} 字符`, color: 'text-[var(--text-primary)]' },
    { label: '规则校验', value: `${result.rule_check_result_len} 字符`, color: 'text-[var(--text-primary)]' },
  ]

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* 执行摘要面板 */}
      <div className="rounded-xl border border-[var(--border-subtle)] bg-indigo-500/[0.03] p-4">
        <div className="text-xs font-semibold text-indigo-300 mb-3 uppercase tracking-wider">执行摘要</div>
        <div className="grid grid-cols-5 gap-3">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-[11px] text-[var(--text-muted)] mb-1">{s.label}</div>
              <div className={`text-sm font-semibold ${s.color}`}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Markdown 报告 */}
      <div className="rounded-xl border border-[var(--border-subtle)] p-5">
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {result.diagnosis_report || '（报告内容为空）'}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
