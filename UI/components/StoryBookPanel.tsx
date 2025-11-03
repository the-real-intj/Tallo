'use client';

import { StoryPage } from '@/types';
import { cn } from '@/lib/utils';

interface StoryBookPanelProps {
  currentPage: StoryPage | null;
  totalPages: number;
  isPlaying: boolean;
  onNext: () => void;
  onPrevious: () => void;
}

/**
 * 동화책 패널 컴포넌트
 * 우측에 동화 페이지를 책 형식으로 표시
 */
export function StoryBookPanel({
  currentPage,
  totalPages,
  isPlaying,
  onNext,
  onPrevious,
}: StoryBookPanelProps) {
  if (!currentPage) {
    return (
      <div className="w-[500px] bg-white shadow-2xl flex flex-col">
        {/* 헤더 */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-6 text-white">
          <h2 className="text-xl font-bold mb-1">📖 동화책</h2>
          <p className="text-sm opacity-90">이야기를 시작해보세요</p>
        </div>

        {/* 빈 상태 */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center text-gray-400">
            <div className="text-6xl mb-4">📚</div>
            <p className="text-lg">
              이야기를 시작하면
              <br />
              여기에 동화가 나타나요
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 모든 페이지 배열 생성 (진행 표시용)
  const pageNumbers = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="w-[500px] bg-white shadow-2xl flex flex-col">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-6 text-white">
        <h2 className="text-xl font-bold mb-1">📖 동화책</h2>
        <p className="text-sm opacity-90">
          페이지 {currentPage.page} / {totalPages}
        </p>
      </div>

      {/* 동화책 페이지 */}
      <div className="flex-1 overflow-auto p-8">
        <div className="storybook-page bg-gradient-to-b from-white to-gray-50 rounded-2xl p-8 h-full shadow-inner">
          {/* 페이지 번호 */}
          <div className="text-right text-sm text-gray-400 mb-4">
            {currentPage.page}
          </div>

          {/* 일러스트 */}
          <div className="text-center mb-8">
            <div className="text-9xl mb-4 page-turn transition-transform hover:scale-105">
              {currentPage.image}
            </div>
          </div>

          {/* 텍스트 */}
          <div className="text-xl leading-relaxed text-gray-800 text-center mb-8">
            {currentPage.text}
          </div>

          {/* 페이지 진행 표시 */}
          <div className="flex justify-center gap-2 mt-8">
            {pageNumbers.map((num) => (
              <div
                key={num}
                className={cn(
                  'h-2 rounded-full transition-all',
                  num === currentPage.page
                    ? 'bg-orange-500 w-6'
                    : num < currentPage.page
                    ? 'bg-orange-300 w-2'
                    : 'bg-gray-300 w-2'
                )}
              />
            ))}
          </div>
        </div>
      </div>

      {/* 하단 네비게이션 */}
      {isPlaying && (
        <div className="p-4 border-t-2 border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <button
              onClick={onPrevious}
              disabled={currentPage.page === 1}
              className="px-6 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              ← 이전
            </button>

            {/* 선택지가 없을 때만 다음 버튼 표시 */}
            {!currentPage.choices && (
              <button
                onClick={onNext}
                disabled={currentPage.page === totalPages}
                className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                다음 →
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
