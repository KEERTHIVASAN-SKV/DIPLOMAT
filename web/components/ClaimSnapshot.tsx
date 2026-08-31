'use client'

import { motion } from 'framer-motion'
import { Calendar, Building2, User, FileText, CreditCard } from 'lucide-react'

interface ClaimSnapshotProps {
  bill: any
  discharge: any
  policy: any
}

export default function ClaimSnapshot({ bill, discharge, policy }: ClaimSnapshotProps) {
  const fields = [
    { icon: User, label: 'Patient', value: bill?.patient_name || '—' },
    { icon: Building2, label: 'Hospital', value: (bill?.hospital || '—').split(',')[0] },
    { icon: Calendar, label: 'Admitted', value: bill?.admission_date || '—' },
    { icon: Calendar, label: 'Discharged', value: bill?.discharge_date || '—' },
    { icon: FileText, label: 'Diagnosis', value: discharge?.diagnosis || '—' },
    { icon: CreditCard, label: 'Bill Total', value: bill?.bill_total ? `₹${Number(bill.bill_total).toLocaleString('en-IN')}` : '—' },
  ]

  return (
    <motion.div
      className="glass-lg p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
    >
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Claim Snapshot</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {fields.map((f, i) => (
          <motion.div
            key={f.label}
            className="flex flex-col gap-1"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 + 0.2 }}
          >
            <div className="flex items-center gap-1.5 text-slate-500">
              <f.icon className="w-3 h-3" />
              <span className="text-xs">{f.label}</span>
            </div>
            <p className="text-sm font-semibold text-white truncate">{f.value}</p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
