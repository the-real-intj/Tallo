const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 로컬 outputs 폴더를 정적 파일로 제공
  async rewrites() {
    return [
      {
        source: '/outputs/:path*',
        destination: '/api/static-outputs/:path*', // API Route로 리다이렉트
      },
    ];
  },
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
