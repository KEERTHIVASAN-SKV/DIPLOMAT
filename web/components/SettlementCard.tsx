'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendingDown, IndianRupee, CheckCircle2, AlertTriangle } from 'lucide-react'

interface Deduction {
  deduction_id: string
  description: string
  amount: number
  clause_id: string
  category: string
  calculation?: string
}

interface Settlement {
  bill_total: number
  deductions: Deduction[]
  total_deductions: number
  payable: number
  sum_insured_remaining?: number
  _adjudication_method?: string
}

interface SettlementCardProps {
  settlement: Settlement | null
  status: string
  bounces?: any[]
}

function AnimatedNumber({ target, prefix = '₹' }: { target: number; prefix?: string }) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    let start = 0
    const duration = 1200
    const startTime = performance.now()

    const tick = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 4) // ease-out-quart
      const current = Math.round(start + (target - start) * eased)
      setDisplay(current)
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target])

  return (
    <span>
      {prefix}{display.toLocaleString('en-IN')}
    </span>
  )
}

const categoryColors: Record<string, string> = {
  room_rent: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  proportionate: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  non_payable: 'text-red-400 bg-red-500/10 border-red-500/20',
  copay: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
}

export default function SettlementCard({ settlement, status, bounces = [] }: SettlementCardProps) {
  const isApproved = status === 'APPROVED'
  const isEscalated = status === 'ESCALATED_TO_HUMAN'

  if (isEscalated) {
    return (
      <motion.div
        className="glass-lg p-8 border border-amber-500/30 bg-gradient-to-br from-amber-500/5 to-transparent"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <div className="flex items-center gap-3 mb-6">
          <motion.div
            className="p-3 rounded-xl bg-amber-500/20"
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <AlertTriangle className="w-6 h-6 text-amber-400" />
          </motion.div>
          <div>
            <h3 className="text-xl font-bold text-amber-300">Escalated to Human Review</h3>
            <p className="text-sm text-slate-400">LLM failed after max retries — human intervention required</p>
          </div>
        </div>

        {bounces.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Unresolved issues</p>
            {bounces.map((b, i) => (
              <motion.div
                key={i}
                className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/40"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <p className="text-xs font-mono text-amber-300 mb-1">{b.check || b.validator}</p>
                <p className="text-xs text-slate-400">{b.message}</p>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    )
  }

  if (!isApproved || !settlement) {
    return (
      <motion.div
        className="glass-lg p-12 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <p className="text-slate-500 text-sm">Run a claim to see the settlement</p>
      </motion.div>
    )
  }

  return (
    <motion.div
      className="glass-lg overflow-hidden border border-emerald-500/20"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500/10 to-transparent p-6 border-b border-emerald-500/20">
        <div className="flex items-center gap-3">
          <motion.div
            className="p-2.5 rounded-xl bg-emerald-500/20"
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
          >
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          </motion.div>
          <div>
            <h3 className="text-xl font-bold text-emerald-300">Claim Approved</h3>
            <p className="text-xs text-slate-400">
              Method: {settlement._adjudication_method === 'llm' ? '🤖 LLM adjudication' : '🔧 Mock adjudication'}
            </p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-xs text-slate-500 mb-1">Payable Amount</p>
            <motion.p
              className="text-3xl font-bold text-emerald-300 font-mono"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <AnimatedNumber target={settlement.payable} />
            </motion.p>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-6 space-y-3">
        {/* Bill total */}
        <div className="flex justify-between items-center py-2">
          <span className="text-sm text-slate-400 flex items-center gap-2">
            <IndianRupee className="w-3.5 h-3.5" />
            Bill Total
          </span>
          <span className="font-semibold text-white font-mono">
            ₹{settlement.bill_total.toLocaleString('en-IN')}
          </span>
        </div>

        {/* Deductions */}
        <div className="pt-2 border-t border-slate-700/30">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="w-3.5 h-3.5 text-red-400" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Deductions</span>
          </div>
          <div className="space-y-2">
            {settlement.deductions.map((d, i) => (
              <motion.div
                key={d.deduction_id}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50"
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.08 }}
              >
                <div className="flex-1 min-w-0 mr-4">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={`text-xs font-mono font-semibold px-1.5 py-0.5 rounded border ${categoryColors[d.category] || 'text-slate-400 bg-slate-700/30 border-slate-600/30'}`}>
                      {d.clause_id}
                    </span>
                    <span className="text-xs text-slate-400 truncate">{d.description}</span>
                  </div>
                  {d.calculation && (
                    <p className="text-xs text-slate-600 font-mono">{d.calculation}</p>
                  )}
                </div>
                <span className="text-sm font-semibold text-red-400 font-mono flex-shrink-0">
                  −₹{d.amount.toLocaleString('en-IN')}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Summary row */}
        <motion.div
          className="pt-4 border-t border-slate-700/30 space-y-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <div className="flex justify-between items-center">
            <span className="text-sm text-slate-400">Total Deductions</span>
            <span className="font-semibold text-red-400 font-mono">
              −₹{settlement.total_deductions.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex justify-between items-center py-3 px-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <span className="font-bold text-emerald-300">Final Payable</span>
            <span className="text-2xl font-bold text-emerald-300 font-mono">
              <AnimatedNumber target={settlement.payable} />
            </span>
          </div>
          {settlement.sum_insured_remaining !== undefined && (
            <div className="flex justify-between items-center text-xs text-slate-500">
              <span>Sum Insured Remaining</span>
              <span className="font-mono">₹{settlement.sum_insured_remaining.toLocaleString('en-IN')}</span>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  )
}
