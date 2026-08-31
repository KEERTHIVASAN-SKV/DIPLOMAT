'use client'

import { Shield, BarChart3, Settings, LogOut } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Sidebar() {
  const menuItems = [
    { icon: Shield, label: 'Dashboard', active: true },
    { icon: BarChart3, label: 'Analytics' },
    { icon: Settings, label: 'Settings' },
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0 },
  }

  return (
    <motion.div
      className="glass-lg w-64 h-screen flex flex-col fixed left-0 top-0 border-r border-slate-700/30 p-6"
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <motion.div
        className="flex items-center gap-3 mb-12 cursor-pointer"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="p-2 rounded-lg bg-gradient-to-br from-primary to-secondary glow-primary">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            DIPLOMAT
          </h1>
          <p className="text-xs text-slate-400">Insurance AI</p>
        </div>
      </motion.div>

      <motion.nav
        className="flex-1 space-y-2"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {menuItems.map((item, idx) => (
          <motion.button
            key={idx}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-smooth ${
              item.active
                ? 'bg-gradient-to-r from-primary/20 to-secondary/20 border border-primary/30 text-primary'
                : 'text-slate-400 hover:text-slate-300'
            }`}
            variants={itemVariants}
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.98 }}
          >
            <item.icon className="w-5 h-5" />
            <span className="text-sm font-medium">{item.label}</span>
            {item.active && (
              <motion.div
                className="ml-auto w-2 h-2 rounded-full bg-primary"
                layoutId="activeIndicator"
              />
            )}
          </motion.button>
        ))}
      </motion.nav>

      <motion.button
        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:text-slate-300 transition-smooth mt-auto"
        whileHover={{ x: 4 }}
        whileTap={{ scale: 0.98 }}
      >
        <LogOut className="w-5 h-5" />
        <span className="text-sm font-medium">Logout</span>
      </motion.button>
    </motion.div>
  )
}
