import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DIPLOMAT Dashboard',
  description: 'Premium Insurance AI Pipeline Visualization',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gradient-to-br from-dark via-slate-900 to-slate-950">
        {children}
      </body>
    </html>
  )
}
