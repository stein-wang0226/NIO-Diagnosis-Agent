/**
 * 步骤指示器 - 水平紧凑步骤条，替代 React Flow 工作流图
 *
 * 展示 Agent 执行进度：灰色圆点 → 蓝色脉冲 → 绿色对勾
 */

import { memo } from 'react'
import type { NodeStatus } from '../types/events'

/** 步骤定义 */
const STEPS = [
  { key: 'log_fetch', label: '日志获取', icon: '📋' },
  { key: 'retrieve', label: '知识检索', icon: '🔍' },
  { key: 'grade', label: '文档评分', icon: '⚖️' },
  { key: 'rule_check', label: '规则校验', icon: '✅' },
  { key: 'analyze', label: '原因分析', icon: '🧠' },
]

/** 步骤状态图标 */
function StepIcon({ status }: { status: NodeStatus }) {
  if (status === 'completed') {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    )
  }
  if (status === 'running') {
    return (
      <span className="inline-block w-3 h-3 rounded-full bg-indigo-400 animate-pulse" />
    )
  }
  return <span className="inline-block w-2 h-2 rounded-full bg-[var(--text-muted)]" />
}

/** 单个步骤 */
const Step = memo(({ step, status }: {
  step: typeof STEPS[number]
  status: NodeStatus
}) => {
  const colors = {
    idle: 'text-[var(--text-muted)]',
    running: 'text-indigo-400',
    completed: 'text-emerald-400',
    skipped: 'text-[var(--text-muted)]',
  }

  const ringColors = {
    idle: 'border-[var(--border-subtle)]',
    running: 'border-indigo-500 shadow-[0_0_12px_rgba(99,102,241,0.4)]',
    completed: 'border-emerald-500',
    skipped: 'border-[var(--border-subtle)]',
  }

  return (
    <div className="flex flex-col items-center gap-1.5 min-w-0">
      {/* 圆圈 */}
      <div
        className={`
          relative w-9 h-9 rounded-full border-2 flex items-center justify-center
          transition-all duration-500 ${ringColors[status]}
          ${status === 'running' ? 'step-pulse' : ''}
          ${status === 'completed' ? 'bg-emerald-500/10' : ''}
        `}
      >
        <span className={colors[status]}>
          <StepIcon status={status} />
        </span>
      </div>
      {/* 标签 */}
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
  if (from === 'completed' && (to === 'completed' || to === 'running')) {
    cls += ' completed'
  } else if (from === 'running') {
    cls += ' active'
  }
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
