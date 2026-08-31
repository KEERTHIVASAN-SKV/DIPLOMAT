'use client'

import { Bell, Settings, User } from 'lucide-react'
import { motion } from 'framer-motion'

export default function TopBar() {
  return (
    <motion.div
      className="glass-lg h-20 fixed top-0 left-64 right-0 border-b border-slate-700/30 flex items-center justify-between px-8"
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div>
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <p className="text-sm text-slate-400">Real-time claim processing pipeline</p>
      </div>

      <div className="flex items-center gap-4">
        <motion.button
          className="relative p-3 rounded-lg glass hover:bg-primary/10 transition-smooth"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <Bell className="w-5 h-5 text-slate-400" />
          <motion.span
            className="absolute top-2 right-2 w-2 h-2 bg-danger rounded-full animate-pulse-glow"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </motion.button>

        <motion.button
          className="p-3 rounded-lg glass hover:bg-primary/10 transition-smooth"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <Settings className="w-5 h-5 text-slate-400" />
        </motion.button>

        <motion.button
          className="flex items-center gap-3 px-4 py-2 rounded-lg glass hover:bg-primary/10 transition-smooth"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary" />
          <div className="text-left">
            <p className="text-sm font-medium text-white">Admin</p>
            <p className="text-xs text-slate-400">Online</p>
          </div>
        </motion.button>
      </div>
    </motion.div>
  )
}
