/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const apiBase =
      process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
