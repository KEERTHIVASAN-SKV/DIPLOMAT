'use client'

import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, RefreshCw, Play } from 'lucide-react'

interface TraceStep {
  step: string
  status: string
  attempt?: number
  bounces?: any[]
  detail?: string
  output?: any
  settlement?: any
  rules_applied?: string[]
}

interface TraceLogProps {
  steps: TraceStep[]
}

function getStepIcon(_step: string, status: string) {
  if (status === 'PASSED') return <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
  if (status.includes('BOUNCED')) return <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
  if (status === 'FEEDBACK_LOOP') return <RefreshCw className="w-4 h-4 text-indigo-400 flex-shrink-0 animate-spin" />
  if (status.includes('ATTEMPT')) return (
    <motion.div
      className="w-4 h-4 rounded-full border-2 border-indigo-400 border-t-transparent flex-shrink-0"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  )
  return <Play className="w-4 h-4 text-slate-500 flex-shrink-0" />
}

function getStepColor(status: string) {
  if (status === 'PASSED') return 'text-emerald-300'
  if (status.includes('BOUNCED')) return 'text-red-300'
  if (status === 'FEEDBACK_LOOP') return 'text-indigo-300'
  if (status.includes('ATTEMPT')) return 'text-slate-200'
  return 'text-slate-400'
}

function formatStep(step: TraceStep): string {
  const { step: name, status } = step
  if (name === 'PIPELINE' && status === 'FEEDBACK_LOOP') return `↩ ${step.detail || 'Feedback loop'}`
  if (status === 'PASSED') return `${name} → PASSED (attempt ${step.attempt ?? '?'})`
  if (status.includes('BOUNCED')) {
    const n = (step.bounces || []).length
    return `${name} → BOUNCED — ${n} issue${n !== 1 ? 's' : ''} sent as feedback`
  }
  if (status.includes('ATTEMPT')) {
    const out = step.output || step.settlement || {}
    const em = out?._extraction_method ? ` [${out._extraction_method}]` : ''
    const am = out?._adjudication_method ? ` [${out._adjudication_method}]` : ''
    return `${name} — ${status}${em}${am}`
  }
  if (name === 'A2_POLICY' && status === 'COMPLETE') {
    const rules = step.rules_applied || []
    return `POLICY ENGINE — ${rules.length} rule${rules.length !== 1 ? 's' : ''} applied`
  }
  return `${name}: ${status}`
}

export default function TraceLog({ steps }: TraceLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  return (
    <motion.div
      className="glass-lg p-5"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest">Live Trace</h3>
        <span className="ml-auto text-xs text-slate-500 font-mono">{steps.length} steps</span>
      </div>

      <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1 custom-scroll">
        <AnimatePresence initial={false}>
          {steps.length === 0 && (
            <motion.p
              key="empty"
              className="text-xs text-slate-600 text-center py-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              Pipeline trace will appear here…
            </motion.p>
          )}
          {steps.map((s, i) => (
            <motion.div
              key={i}
              className="flex items-start gap-3 px-3 py-2.5 rounded-lg bg-slate-800/40 hover:bg-slate-800/60 transition-colors"
              initial={{ opacity: 0, x: -12, height: 0 }}
              animate={{ opacity: 1, x: 0, height: 'auto' }}
              transition={{ duration: 0.25 }}
            >
              <div className="mt-0.5">{getStepIcon(s.step, s.status)}</div>
              <div className="flex-1 min-w-0">
                <p className={`text-xs font-mono ${getStepColor(s.status)} leading-relaxed`}>
                  {formatStep(s)}
                </p>
                {s.status === 'PASSED' && s.step === 'G2_DIPLOMAT' && (
                  <p className="text-xs text-emerald-500/70 mt-0.5">All checks passed ✓</p>
                )}
              </div>
              <span className="text-xs text-slate-600 font-mono flex-shrink-0">{String(i + 1).padStart(2, '0')}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </motion.div>
  )
}
