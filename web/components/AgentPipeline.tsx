'use client'

import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, Clock, ArrowRight } from 'lucide-react'

export interface PipelineNode {
  id: string
  name: string
  icon: string
  type: 'agent' | 'gate'
  status: 'idle' | 'processing' | 'pass' | 'bounce' | 'escalate'
  attempt?: number
  method?: string
}

interface AgentPipelineProps {
  nodes: PipelineNode[]
}

const STATUS_CONFIG = {
  idle: {
    border: 'border-slate-600/40',
    bg: 'bg-slate-800/40',
    text: 'text-slate-500',
    glow: '',
    icon: null,
  },
  processing: {
    border: 'border-indigo-400/60',
    bg: 'bg-indigo-500/10',
    text: 'text-indigo-300',
    glow: 'shadow-[0_0_16px_rgba(99,102,241,0.35)]',
    icon: null,
  },
  pass: {
    border: 'border-emerald-400/60',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-300',
    glow: 'shadow-[0_0_16px_rgba(16,185,129,0.3)]',
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  },
  bounce: {
    border: 'border-red-400/60',
    bg: 'bg-red-500/10',
    text: 'text-red-300',
    glow: 'shadow-[0_0_16px_rgba(239,68,68,0.3)]',
    icon: <XCircle className="w-4 h-4 text-red-400" />,
  },
  escalate: {
    border: 'border-amber-400/60',
    bg: 'bg-amber-500/10',
    text: 'text-amber-300',
    glow: 'shadow-[0_0_16px_rgba(245,158,11,0.3)]',
    icon: <Clock className="w-4 h-4 text-amber-400" />,
  },
}

function PipeConnector({ active, passing }: { active: boolean; passing: boolean }) {
  return (
    <div className="flex items-center justify-center w-8 flex-shrink-0 relative">
      {/* Track */}
      <div className="absolute w-full h-0.5 bg-slate-700/60 rounded-full" />
      {/* Fill */}
      {active && (
        <motion.div
          className={`absolute left-0 top-1/2 -translate-y-1/2 h-0.5 rounded-full ${passing ? 'bg-emerald-400' : 'bg-indigo-400'}`}
          initial={{ width: '0%' }}
          animate={{ width: '100%' }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        />
      )}
      {/* Arrow */}
      <ArrowRight className={`w-3 h-3 relative z-10 ${active ? (passing ? 'text-emerald-400' : 'text-indigo-400') : 'text-slate-700'}`} />
    </div>
  )
}

export default function AgentPipeline({ nodes }: AgentPipelineProps) {
  return (
    <motion.div
      className="glass-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Agent Pipeline</h3>

      <div className="flex items-center justify-between overflow-x-auto pb-2 gap-1">
        {nodes.map((node, idx) => {
          const cfg = STATUS_CONFIG[node.status]
          const isProcessing = node.status === 'processing'
          const showConnector = idx < nodes.length - 1
          const connectorActive = node.status === 'pass' || node.status === 'bounce' || node.status === 'escalate'
          const connectorPassing = node.status === 'pass'

          return (
            <div key={node.id} className="flex items-center gap-1">
              <motion.div
                className={`flex-shrink-0 flex flex-col items-center gap-1.5 px-3 py-3 rounded-xl border transition-all duration-300 min-w-[90px] ${cfg.border} ${cfg.bg} ${cfg.glow}`}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: node.status === 'idle' ? 0.45 : 1, scale: 1 }}
                transition={{ delay: idx * 0.07, duration: 0.4 }}
                whileHover={{ scale: 1.04 }}
              >
                {/* Spinning ring for processing */}
                <div className="relative flex items-center justify-center">
                  {isProcessing && (
                    <motion.div
                      className="absolute inset-0 -m-1 rounded-full border-2 border-indigo-400/50 border-t-indigo-400"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    />
                  )}
                  <span className="text-xl leading-none">{node.icon}</span>
                </div>

                <span className={`text-xs font-semibold text-center leading-tight ${cfg.text}`}>
                  {node.name}
                </span>

                {/* Status indicator */}
                <div className="flex items-center gap-1">
                  {cfg.icon}
                  {node.attempt !== undefined && node.status === 'pass' && (
                    <span className="text-xs text-slate-500 font-mono">#{node.attempt}</span>
                  )}
                  {node.method && (
                    <span className={`text-xs font-mono px-1 rounded ${
                      node.method === 'llm' ? 'text-violet-400 bg-violet-500/10' : 'text-slate-500 bg-slate-700/30'
                    }`}>
                      {node.method}
                    </span>
                  )}
                  {node.status === 'bounce' && node.attempt !== undefined && (
                    <span className="text-xs text-slate-500 font-mono">#{node.attempt}</span>
                  )}
                </div>
              </motion.div>

              {showConnector && (
                <PipeConnector
                  active={connectorActive}
                  passing={connectorPassing}
                />
              )}
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
