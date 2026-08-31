'use client'

import { motion } from 'framer-motion'

interface Scenario {
  id: string
  label: string
  desc: string
  inject_fault: string | null
  icon: string
  color: string
  glow: string
}

interface ScenarioPickerProps {
  selected: string
  onChange: (id: string, fault: string | null) => void
  disabled?: boolean
}

const SCENARIOS: Scenario[] = [
  {
    id: 'room_rent',
    label: 'Room Rent Misread',
    desc: 'Gate 1 catches OCR error, agent self-corrects on retry',
    inject_fault: 'room_rent_misread',
    icon: '🏥',
    color: 'from-amber-500/20 to-orange-500/10 border-amber-500/40',
    glow: 'shadow-amber-500/20',
  },
  {
    id: 'missing_citation',
    label: 'Missing Citation',
    desc: 'Gate 2 bounces for missing clause, adjudicator retries',
    inject_fault: 'missing_citation',
    icon: '📋',
    color: 'from-red-500/20 to-rose-500/10 border-red-500/40',
    glow: 'shadow-red-500/20',
  },
  {
    id: 'clean',
    label: 'Clean Run',
    desc: 'No fault injection — both gates pass on first attempt',
    inject_fault: null,
    icon: '✅',
    color: 'from-emerald-500/20 to-green-500/10 border-emerald-500/40',
    glow: 'shadow-emerald-500/20',
  },
]

export default function ScenarioPicker({ selected, onChange, disabled }: ScenarioPickerProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {SCENARIOS.map((s, i) => (
        <motion.button
          key={s.id}
          onClick={() => !disabled && onChange(s.id, s.inject_fault)}
          className={`relative text-left p-5 rounded-xl border transition-all duration-300 bg-gradient-to-br ${s.color} ${
            selected === s.id
              ? `ring-2 ring-offset-2 ring-offset-slate-900 shadow-lg ${s.glow} ${
                  s.id === 'room_rent' ? 'ring-amber-400' : s.id === 'missing_citation' ? 'ring-red-400' : 'ring-emerald-400'
                }`
              : 'hover:scale-[1.02] opacity-70 hover:opacity-100'
          } ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1, duration: 0.4 }}
          whileHover={!disabled ? { y: -2 } : {}}
          whileTap={!disabled ? { scale: 0.98 } : {}}
        >
          {selected === s.id && (
            <motion.div
              className="absolute inset-0 rounded-xl"
              layoutId="selectedScenario"
              style={{ background: 'rgba(99,102,241,0.05)' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            />
          )}
          <div className="relative">
            <div className="text-2xl mb-2">{s.icon}</div>
            <p className="font-bold text-white text-sm mb-1">{s.label}</p>
            <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
          </div>
        </motion.button>
      ))}
    </div>
  )
}
