import type { Metadata } from 'next';
import { Noto_Sans_KR } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const notoSansKr = Noto_Sans_KR({
  subsets: ['latin'],
  weight: ['300', '400', '500', '700'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Tallo - 페르소나 기반 인터랙티브 동화 서비스',
  description: '사용자가 좋아하는 캐릭터 음성으로 동요·구연동화를 생성하고 재생하는 서비스',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={notoSansKr.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
