/**
 * 问题输入组件 - 现代化样式
 * 示例问题胶囊 + 输入框 + 渐变按钮
 */

import { useState } from 'react'

export default function QuestionInput({
  examples,
  isRunning,
  onSubmit,
}: {
  examples: string[]
  isRunning: boolean
  onSubmit: (question: string) => void
}) {
  const [input, setInput] = useState('')
  const [focused, setFocused] = useState(false)

  const handleSubmit = () => {
    const q = input.trim()
    if (!q || isRunning) return
    onSubmit(q)
  }

  const handleExample = (q: string) => {
    if (isRunning) return
    setInput(q)
    onSubmit(q)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="space-y-3">
      {/* 示例问题 */}
      {examples.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {examples.map((q, i) => (
            <button
              key={i}
              onClick={() => handleExample(q)}
              disabled={isRunning}
              className={`
                group px-3 py-1.5 rounded-xl text-[11px] text-left transition-all
                ${isRunning
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  : 'glass-card glass-card-hover text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer'
                }
              `}
              title={q}
            >
              <span className="text-indigo-500 mr-1.5 font-bold">{i + 1}</span>
              {q.length > 24 ? q.slice(0, 24) + '...' : q}
            </button>
          ))}
        </div>
      )}

      {/* 输入框 + 按钮 */}
      <div className={`
        flex items-center gap-2 p-1.5 rounded-xl transition-all
        ${focused
          ? 'glass-card border-indigo-500/30 shadow-[0_0_20px_rgba(99,102,241,0.08)]'
          : 'glass-card'
        }
      `}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={isRunning}
          placeholder="描述故障现象，或选择上方的示例问题..."
          className="
            flex-1 px-4 py-2.5 bg-transparent rounded-lg
            text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm
            focus:outline-none
            disabled:opacity-50 disabled:cursor-not-allowed
          "
        />
        <button
          onClick={handleSubmit}
          disabled={isRunning || !input.trim()}
          className={`
            px-5 py-2.5 rounded-lg font-medium text-sm transition-all whitespace-nowrap
            ${isRunning || !input.trim()
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white hover:shadow-lg hover:shadow-indigo-500/25 hover:brightness-110'
            }
          `}
        >
          {isRunning ? (
            <span className="flex items-center gap-2">
              <span className="inline-block w-3.5 h-3.5 border-2 border-white/80 border-t-transparent rounded-full animate-spin" />
              诊断中...
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polygon points="10 8 16 12 10 16 10 8" />
              </svg>
              开始诊断
            </span>
          )}
        </button>
      </div>
    </div>
  )
}
