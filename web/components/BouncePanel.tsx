'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, Info } from 'lucide-react'

interface Bounce {
  check?: string
  validator?: string
  message?: string
  severity?: string
  expected?: any
  got?: any
  hint?: string
}

interface BouncePanelProps {
  gateName: string
  bounces: Bounce[]
  gateColor?: 'veritas' | 'diplomat'
}

export default function BouncePanel({ gateName, bounces, gateColor = 'veritas' }: BouncePanelProps) {
  const accent = gateColor === 'veritas' ? 'amber' : 'red'
  const accentClasses = {
    amber: { border: 'border-amber-500/30', bg: 'bg-amber-500/5', badge: 'bg-amber-500/20 text-amber-300', text: 'text-amber-400', dot: 'bg-amber-400' },
    red: { border: 'border-red-500/30', bg: 'bg-red-500/5', badge: 'bg-red-500/20 text-red-300', text: 'text-red-400', dot: 'bg-red-400' },
  }
  const c = accentClasses[accent]

  return (
    <AnimatePresence>
      {bounces.length > 0 && (
        <motion.div
          className={`rounded-xl border ${c.border} ${c.bg} p-5`}
          initial={{ opacity: 0, height: 0, y: -10 }}
          animate={{ opacity: 1, height: 'auto', y: 0 }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          <div className="flex items-center gap-2 mb-4">
            <motion.div
              className={`w-2 h-2 rounded-full ${c.dot}`}
              animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            <AlertTriangle className={`w-4 h-4 ${c.text}`} />
            <span className={`text-sm font-bold ${c.text}`}>{gateName} — Bounce Feedback Sent to Agent</span>
          </div>

          <div className="space-y-3">
            {bounces.map((b, i) => {
              const checkName = b.check || b.validator || 'VALIDATION_ERROR'
              return (
                <motion.div
                  key={i}
                  className="rounded-lg bg-slate-900/60 p-4 border border-slate-700/40"
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${c.badge}`}>
                      {checkName}
                    </span>
                    {b.severity && (
                      <span className="text-xs text-slate-500 font-mono">{b.severity}</span>
                    )}
                  </div>

                  <p className="text-sm text-slate-300 mb-2">{b.message}</p>

                  {(b.expected !== undefined || b.got !== undefined) && (
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      <div className="rounded-md bg-emerald-500/10 border border-emerald-500/20 px-3 py-2">
                        <p className="text-xs text-emerald-500 font-semibold mb-1">Expected</p>
                        <p className="text-xs font-mono text-slate-300 break-all">{JSON.stringify(b.expected)}</p>
                      </div>
                      <div className="rounded-md bg-red-500/10 border border-red-500/20 px-3 py-2">
                        <p className="text-xs text-red-400 font-semibold mb-1">Got</p>
                        <p className="text-xs font-mono text-slate-300 break-all">{JSON.stringify(b.got)}</p>
                      </div>
                    </div>
                  )}

                  {b.hint && (
                    <div className="flex items-start gap-2 mt-3 pt-3 border-t border-slate-700/30">
                      <Info className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <p className="text-xs text-indigo-300">{b.hint}</p>
                    </div>
                  )}
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
