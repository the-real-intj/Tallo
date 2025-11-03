/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // TODO: 백엔드 API 서버가 준비되면 아래 주석 해제
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: 'http://localhost:8000/api/:path*', // FastAPI 서버
  //     },
  //   ]
  // },
}

module.exports = nextConfig
