'use client'

import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react'

interface FraudRiskProps {
  score?: number
  level?: 'low' | 'medium' | 'high' | 'critical'
  flags?: string[]
}

export default function FraudRisk({
  score = 0,
  level = 'low',
  flags = [],
}: FraudRiskProps) {
  const getLevelColor = (lv: string) => {
    switch (lv) {
      case 'critical':
        return { bg: 'from-danger to-red-700', text: 'text-danger', icon: AlertTriangle }
      case 'high':
        return { bg: 'from-warning to-orange-600', text: 'text-warning', icon: AlertCircle }
      case 'medium':
        return { bg: 'from-yellow-500 to-yellow-600', text: 'text-yellow-400', icon: AlertCircle }
      case 'low':
        return { bg: 'from-success to-emerald-600', text: 'text-success', icon: CheckCircle }
      default:
        return { bg: 'from-primary to-secondary', text: 'text-primary', icon: CheckCircle }
    }
  }

  const levelConfig = getLevelColor(level)
  const LevelIcon = levelConfig.icon

  return (
    <motion.div
      className="glass-lg p-8"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white">Fraud Risk Assessment</h3>
        <motion.div
          className={`flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r ${levelConfig.bg} ${levelConfig.text}`}
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <LevelIcon className="w-4 h-4" />
          <span className="text-sm font-semibold capitalize">{level} Risk</span>
        </motion.div>
      </div>

      {/* Risk Score Circle */}
      <motion.div className="flex justify-center mb-8">
        <svg width="200" height="200" className="transform -rotate-90">
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="rgba(148, 163, 184, 0.1)"
            strokeWidth="8"
          />
          <motion.circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke={
              level === 'critical'
                ? '#ef4444'
                : level === 'high'
                  ? '#f59e0b'
                  : level === 'medium'
                    ? '#eab308'
                    : '#10b981'
            }
            strokeWidth="8"
            strokeDasharray="565.49"
            initial={{ strokeDashoffset: 565.49 }}
            animate={{ strokeDashoffset: 565.49 - (score / 100) * 565.49 }}
            transition={{ duration: 1.5, ease: 'easeInOut' }}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center mt-2">
          <motion.span
            className={`text-4xl font-bold ${levelConfig.text}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {score}%
          </motion.span>
          <span className="text-xs text-slate-400">Risk Score</span>
        </div>
      </motion.div>

      {/* Risk Flags */}
      {flags.length > 0 && (
        <motion.div
          className="mt-8 pt-6 border-t border-slate-700/30"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <h4 className="text-sm font-semibold text-slate-300 mb-4">Risk Flags</h4>
          <div className="space-y-2">
            {flags.map((flag, idx) => (
              <motion.div
                key={idx}
                className="flex items-start gap-3 p-3 rounded-lg bg-slate-700/20"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
                <span className="text-sm text-slate-300">{flag}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
