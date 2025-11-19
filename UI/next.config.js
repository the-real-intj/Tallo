/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    // public 폴더의 이미지는 자동으로 허용됨
    // 외부 이미지를 사용할 경우 여기에 도메인 추가
    domains: [],
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
