'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, RotateCcw, Shield, Zap, AlertTriangle, CheckCircle2, Activity } from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import TopBar from '@/components/TopBar'
import AgentPipeline, { PipelineNode } from '@/components/AgentPipeline'
import MetricsCard from '@/components/MetricsCard'
import ScenarioPicker from '@/components/ScenarioPicker'
import ClaimSnapshot from '@/components/ClaimSnapshot'
import BouncePanel from '@/components/BouncePanel'
import TraceLog from '@/components/TraceLog'
import SettlementCard from '@/components/SettlementCard'

// ── pipeline node definitions ────────────────────────────────────────────────
const INITIAL_NODES: PipelineNode[] = [
  { id: 'intake',    name: 'Intake',         icon: '📥', type: 'agent', status: 'idle' },
  { id: 'veritas',   name: 'VERITAS',        icon: '🛂', type: 'gate',  status: 'idle' },
  { id: 'policy',    name: 'Policy Engine',  icon: '📋', type: 'agent', status: 'idle' },
  { id: 'adjudicator', name: 'Adjudicator', icon: '⚖️', type: 'agent', status: 'idle' },
  { id: 'diplomat',  name: 'DIPLOMAT',       icon: '🔒', type: 'gate',  status: 'idle' },
  { id: 'settlement',name: 'Settlement',     icon: '💰', type: 'agent', status: 'idle' },
]

// ── parse trace → node states ────────────────────────────────────────────────
function buildNodesFromTrace(trace: any[]): PipelineNode[] {
  const nodes: PipelineNode[] = INITIAL_NODES.map(n => ({ ...n }))

  const nodeMap: Record<string, PipelineNode> = {}
  nodes.forEach(n => { nodeMap[n.id] = n })

  for (const step of trace) {
    const { step: name, status } = step

    if (name === 'A1_INTAKE') {
      if (status.startsWith('ATTEMPT')) {
        nodeMap.intake.status = 'processing'
        const out = step.output
        if (out?._extraction_method) nodeMap.intake.method = out._extraction_method
      }
    }

    if (name === 'G1_VERITAS') {
      if (status === 'PASSED') {
        nodeMap.intake.status = 'pass'
        const prev = trace.filter(s => s.step === 'A1_INTAKE').pop()
        if (prev?.output?._extraction_method) nodeMap.intake.method = prev.output._extraction_method
        nodeMap.veritas.status = 'pass'
        nodeMap.veritas.attempt = step.attempt
      } else if (status.includes('BOUNCED')) {
        const att = parseInt(status.replace('BOUNCED_ATTEMPT_', '')) || 1
        nodeMap.veritas.status = 'bounce'
        nodeMap.veritas.attempt = att
      }
    }

    if (name === 'A2_POLICY') {
      if (status === 'RUNNING' || status === 'COMPLETE') {
        nodeMap.intake.status = nodeMap.intake.status === 'idle' ? 'pass' : nodeMap.intake.status
        nodeMap.veritas.status = nodeMap.veritas.status === 'idle' ? 'pass' : nodeMap.veritas.status
        nodeMap.policy.status = status === 'RUNNING' ? 'processing' : 'pass'
      }
    }

    if (name === 'A3_ADJUDICATOR') {
      if (status.startsWith('ATTEMPT')) {
        nodeMap.policy.status = 'pass'
        nodeMap.adjudicator.status = 'processing'
        const s = step.settlement
        if (s?._adjudication_method) nodeMap.adjudicator.method = s._adjudication_method
      }
    }

    if (name === 'G2_DIPLOMAT') {
      if (status === 'PASSED') {
        const prev = trace.filter(s => s.step === 'A3_ADJUDICATOR').pop()
        if (prev?.settlement?._adjudication_method) nodeMap.adjudicator.method = prev.settlement._adjudication_method
        nodeMap.adjudicator.status = 'pass'
        nodeMap.diplomat.status = 'pass'
        nodeMap.diplomat.attempt = step.attempt
        nodeMap.settlement.status = 'pass'
      } else if (status.includes('BOUNCED')) {
        const att = parseInt(status.replace('BOUNCED_ATTEMPT_', '')) || 1
        nodeMap.diplomat.status = 'bounce'
        nodeMap.diplomat.attempt = att
      }
    }
  }

  return nodes
}

// ── collect bounces from trace ───────────────────────────────────────────────
function collectBounces(trace: any[]) {
  const g1: any[] = []
  const g2: any[] = []
  for (const step of trace) {
    if (step.step === 'G1_VERITAS' && step.status?.includes('BOUNCED')) g1.push(...(step.bounces || []))
    if (step.step === 'G2_DIPLOMAT' && step.status?.includes('BOUNCED')) g2.push(...(step.bounces || []))
  }
  return { g1, g2 }
}

// ── main page ─────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [claimData, setClaimData] = useState<any>(null)
  const [selectedScenario, setSelectedScenario] = useState('room_rent')
  const [injectFault, setInjectFault] = useState<string | null>('room_rent_misread')
  const [running, setRunning] = useState(false)
  const [nodes, setNodes] = useState<PipelineNode[]>(INITIAL_NODES)
  const [trace, setTrace] = useState<any[]>([])
  const [result, setResult] = useState<any>(null)
  const [_runCount, setRunCount] = useState(0)
  const [apiError, setApiError] = useState<string | null>(null)

  // Load claim data on mount
  useEffect(() => {
    fetch('/api/claim-data')
      .then(r => r.json())
      .then(d => setClaimData(d))
      .catch(() => setApiError('Cannot reach API server. Make sure the FastAPI backend is running on :8000'))
  }, [])

  const handleReset = useCallback(() => {
    setNodes(INITIAL_NODES.map(n => ({ ...n })))
    setTrace([])
    setResult(null)
    setApiError(null)
  }, [])

  const handleRun = useCallback(async () => {
    if (running) return
    handleReset()
    setRunning(true)
    setApiError(null)

    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inject_fault: injectFault }),
      })

      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const data = await res.json()

      // Animate trace steps one by one
      const steps: any[] = data.trace || []
      for (let i = 0; i < steps.length; i++) {
        await new Promise(r => setTimeout(r, 220))
        const partial = steps.slice(0, i + 1)
        setTrace(partial)
        setNodes(buildNodesFromTrace(partial))
      }

      setResult(data)
      setRunCount(c => c + 1)
    } catch (e: any) {
      setApiError(e.message || 'Failed to run pipeline')
    } finally {
      setRunning(false)
    }
  }, [running, injectFault, handleReset])

  const { g1: g1Bounces, g2: g2Bounces } = collectBounces(trace)
  const veritasChecks = trace.filter(s => s.step === 'G1_VERITAS').length
  const diplomatChecks = trace.filter(s => s.step === 'G2_DIPLOMAT').length
  const totalBounces = g1Bounces.length + g2Bounces.length
  const finalStatus = result?.status || '—'

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Sidebar />

      <div className="flex-1 ml-64 flex flex-col">
        <TopBar />

        <main className="flex-1 pt-20 p-8 space-y-6 max-w-[1600px]">

          {/* ── API error banner ── */}
          <AnimatePresence>
            {apiError && (
              <motion.div
                className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">{apiError}</p>
                <code className="ml-2 text-xs text-red-400 bg-red-500/10 px-2 py-1 rounded font-mono">
                  python -m uvicorn web.api.server:app --reload --port 8000
                </code>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Page title row ── */}
          <motion.div
            className="flex items-center justify-between"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <Shield className="w-8 h-8 text-indigo-400" />
                DIPLOMAT
              </h1>
              <p className="text-slate-400 mt-1">Fail-Closed Trust Layer for Insurance AI Agents</p>
            </div>

            <div className="flex items-center gap-3">
              {result && (
                <motion.button
                  onClick={handleReset}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-600/50 text-slate-300 hover:border-slate-500 hover:text-white transition-all text-sm font-medium"
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                >
                  <RotateCcw className="w-4 h-4" />
                  Reset
                </motion.button>
              )}

              <motion.button
                onClick={handleRun}
                disabled={running}
                className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm transition-all ${
                  running
                    ? 'bg-indigo-500/30 text-indigo-300 cursor-not-allowed'
                    : 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white hover:from-indigo-400 hover:to-violet-400 shadow-lg shadow-indigo-500/25'
                }`}
                whileHover={!running ? { scale: 1.03 } : {}}
                whileTap={!running ? { scale: 0.97 } : {}}
              >
                {running ? (
                  <>
                    <motion.div
                      className="w-4 h-4 rounded-full border-2 border-indigo-300 border-t-transparent"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                    />
                    Running…
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Claim
                  </>
                )}
              </motion.button>
            </div>
          </motion.div>

          {/* ── Scenario picker ── */}
          <motion.div
            className="glass-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Choose Scenario</h3>
            <ScenarioPicker
              selected={selectedScenario}
              onChange={(id, fault) => {
                setSelectedScenario(id)
                setInjectFault(fault)
                handleReset()
              }}
              disabled={running}
            />
          </motion.div>

          {/* ── Claim snapshot ── */}
          {claimData && (
            <ClaimSnapshot
              bill={claimData.bill}
              discharge={claimData.discharge}
              policy={claimData.policy}
            />
          )}

          {/* ── Agent pipeline ── */}
          <AgentPipeline nodes={nodes} />

          {/* ── Bounce panels ── */}
          <AnimatePresence>
            {g1Bounces.length > 0 && (
              <motion.div key="g1" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <BouncePanel gateName="VERITAS Gate 1" bounces={g1Bounces} gateColor="veritas" />
              </motion.div>
            )}
            {g2Bounces.length > 0 && (
              <motion.div key="g2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <BouncePanel gateName="DIPLOMAT Gate 2" bounces={g2Bounces} gateColor="diplomat" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Two column: trace + settlement ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TraceLog steps={trace} />
            <SettlementCard
              settlement={result?.settlement || null}
              status={result?.status || ''}
              bounces={result?.bounces || []}
            />
          </div>

          {/* ── Run metrics ── */}
          <AnimatePresence>
            {result && (
              <motion.div
                className="grid grid-cols-2 md:grid-cols-4 gap-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
              >
                <MetricsCard
                  icon={<Shield className="w-5 h-5" />}
                  label="VERITAS Checks"
                  value={veritasChecks}
                  color="primary"
                />
                <MetricsCard
                  icon={<Zap className="w-5 h-5" />}
                  label="DIPLOMAT Checks"
                  value={diplomatChecks}
                  color="primary"
                />
                <MetricsCard
                  icon={<Activity className="w-5 h-5" />}
                  label="Total Bounces"
                  value={totalBounces}
                  color={totalBounces > 0 ? 'warning' : 'success'}
                />
                <MetricsCard
                  icon={finalStatus === 'APPROVED' ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                  label="Final Status"
                  value={finalStatus}
                  color={finalStatus === 'APPROVED' ? 'success' : 'warning'}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Footer ── */}
          <motion.div
            className="text-center py-4 text-xs text-slate-600"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            DIPLOMAT • Fail-Closed Trust Layer for Insurance AI Agents • Hackathon Demo
          </motion.div>
        </main>
      </div>
    </div>
  )
}
