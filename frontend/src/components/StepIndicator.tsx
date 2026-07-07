/**
 * 步骤指示器 - 水平紧凑步骤条，SVG 图标
 */

import { memo } from 'react'
import type { NodeStatus } from '../types/events'

/** SVG 图标组件 */
const Icons = {
  log_fetch: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  retrieve: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  grade: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 20V10" />
      <path d="M18 20V4" />
      <path d="M6 20v-4" />
    </svg>
  ),
  rule_check: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
  analyze: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  ),
}

/** 步骤定义 */
const STEPS = [
  { key: 'log_fetch' as const, label: '日志获取' },
  { key: 'retrieve' as const, label: '知识检索' },
  { key: 'grade' as const, label: '文档评分' },
  { key: 'rule_check' as const, label: '规则校验' },
  { key: 'analyze' as const, label: '原因分析' },
]

/** 状态图标 */
function StepIcon({ nodeKey, status }: { nodeKey: string; status: NodeStatus }) {
  if (status === 'completed') {
    return (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    )
  }
  const Icon = Icons[nodeKey as keyof typeof Icons]
  return Icon ? <Icon /> : null
}

/** 单个步骤 */
const Step = memo(({ step, status }: {
  step: typeof STEPS[number]
  status: NodeStatus
}) => {
  const colors = {
    idle: 'text-[var(--text-muted)]',
    running: 'text-indigo-500',
    completed: 'text-emerald-600',
    skipped: 'text-[var(--text-muted)]',
  }

  const ringColors = {
    idle: 'border-slate-200 bg-white',
    running: 'border-indigo-500 bg-indigo-50 shadow-[0_0_12px_rgba(99,102,241,0.2)]',
    completed: 'border-emerald-500 bg-emerald-50',
    skipped: 'border-slate-200 bg-white',
  }

  return (
    <div className="flex flex-col items-center gap-1.5 min-w-0">
      <div
        className={`
          relative w-9 h-9 rounded-full border-2 flex items-center justify-center
          transition-all duration-500 ${ringColors[status]}
          ${status === 'running' ? 'step-pulse' : ''}
        `}
      >
        <span className={colors[status]}>
          <StepIcon nodeKey={step.key} status={status} />
        </span>
      </div>
      <span className={`text-[11px] font-medium whitespace-nowrap ${colors[status]}`}>
        {step.label}
      </span>
    </div>
  )
})
Step.displayName = 'Step'

/** 连接线 */
function Connector({ from, to }: { from: NodeStatus; to: NodeStatus }) {
  let cls = 'step-connector'
  if (from === 'completed' && (to === 'completed' || to === 'running')) cls += ' completed'
  else if (from === 'running') cls += ' active'
  return <div className={cls} style={{ minWidth: '24px' }} />
}

export default function StepIndicator({
  nodeStatuses,
}: {
  nodeStatuses: Record<string, NodeStatus>
}) {
  return (
    <div className="flex items-center justify-center px-6 py-3 gap-0">
      {STEPS.map((step, i) => {
        const status = (nodeStatuses[step.key] || 'idle') as NodeStatus
        const nextStep = STEPS[i + 1]
        const nextStatus = nextStep
          ? (nodeStatuses[nextStep.key] || 'idle') as NodeStatus
          : null

        return (
          <div key={step.key} className="flex items-center flex-1 last:flex-none">
            <Step step={step} status={status} />
            {nextStep && nextStatus !== null && (
              <Connector from={status} to={nextStatus} />
            )}
          </div>
        )
      })}
    </div>
  )
}
/**
 * 步骤指示器 - 水平紧凑步骤条，替代 React Flow 工作流图
 *
 * 展示 Agent 执行进度：灰色圆点 → 蓝色脉冲 → 绿色对勾
 */

