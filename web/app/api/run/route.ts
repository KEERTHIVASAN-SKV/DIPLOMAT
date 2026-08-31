import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const body = await request.json()

  // If a Python backend is configured, proxy to it
  const apiBase = process.env.NEXT_PUBLIC_API_URL
  if (apiBase) {
    try {
      const res = await fetch(`${apiBase}/api/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        cache: 'no-store',
      })
      if (res.ok) {
        const data = await res.json()
        return NextResponse.json(data)
      }
      const err = await res.text()
      return NextResponse.json({ error: `Backend error: ${err}` }, { status: 502 })
    } catch (e: any) {
      return NextResponse.json(
        { error: `Could not reach backend at ${apiBase} — ${e?.message}` },
        { status: 503 }
      )
    }
  }

  // No backend configured — return a clear demo response
  return NextResponse.json(
    {
      error: 'no_backend',
      message:
        'The DIPLOMAT validation pipeline runs on a Python backend. ' +
        'Set NEXT_PUBLIC_API_URL in Vercel environment variables to point to your deployed backend (e.g. Railway). ' +
        'See HOW_TO_START.md §5 for setup instructions.',
    },
    { status: 503 }
  )
}
