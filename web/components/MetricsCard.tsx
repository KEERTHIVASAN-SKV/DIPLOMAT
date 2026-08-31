'use client'

import { motion } from 'framer-motion'
import { ReactNode } from 'react'

interface MetricsCardProps {
  icon: ReactNode
  label: string
  value: string | number
  trend?: string
  color?: 'primary' | 'success' | 'warning' | 'danger'
}

export default function MetricsCard({
  icon,
  label,
  value,
  trend,
  color = 'primary',
}: MetricsCardProps) {
  const colorClasses = {
    primary: 'from-primary to-secondary',
    success: 'from-success to-emerald-500',
    warning: 'from-warning to-orange-500',
    danger: 'from-danger to-red-500',
  }

  return (
    <motion.div
      className="glass-lg p-6 hover-lift transition-smooth"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-start justify-between mb-4">
        <motion.div
          className={`p-3 rounded-lg bg-gradient-to-br ${colorClasses[color]} text-white glow-primary`}
          whileHover={{ scale: 1.1, rotate: 5 }}
        >
          {icon}
        </motion.div>
        {trend && (
          <span className={`text-xs font-semibold ${trend.includes('+') ? 'text-success' : 'text-danger'}`}>
            {trend}
          </span>
        )}
      </div>
      <p className="text-slate-400 text-sm mb-2">{label}</p>
      <motion.p
        className="text-3xl font-bold text-white"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        {value}
      </motion.p>
    </motion.div>
  )
}
