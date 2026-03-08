/** @type {import('next').NextConfig} */
const API_URL = process.env.API_URL || process.env.LOCAL_APP_URL || 'http://127.0.0.1:8000';
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/adk/:path*',
        destination: `${API_URL}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
