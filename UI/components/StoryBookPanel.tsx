'use client';

import { useEffect, useRef, useState } from 'react';
import { StoryPage, Character } from '@/types';
import { cn } from '@/lib/utils';
import { pregenerateStoryAudio, type PreGenerateResponse } from '@/lib/api';

interface StoryBookPanelProps {
  currentPage: StoryPage | null;
  totalPages: number;
  isPlaying: boolean;
  isVoiceEnabled?: boolean;
  character?: Character | null;
  storyPages?: StoryPage[];  // 전체 동화 페이지 추가
  onNext: () => void;
  onPrevious: () => void;
  onAudioPregenerated?: (audioMap: Record<number, string>) => void;  // 미리 생성 완료 콜백
}

/**
 * 동화책 패널 컴포넌트
 * 우측에 동화 페이지를 책 형식으로 표시
 * 음성 ON 시 미리 생성된 오디오 파일 사용
 */
export function StoryBookPanel({
  currentPage,
  totalPages,
  isPlaying,
  isVoiceEnabled = false,
  character = null,
  storyPages = [],
  onNext,
  onPrevious,
  onAudioPregenerated,
}: StoryBookPanelProps) {
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isPregenerating, setIsPregenerating] = useState(false);
  const [audioMap, setAudioMap] = useState<Record<number, string>>({});
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastReadPageRef = useRef<number>(-1);
  const hasPregeneratedRef = useRef(false);

  // 음성 ON 시 전체 동화 미리 생성 (최초 1회만)
  useEffect(() => {
    const pregenerateAllPages = async () => {
      if (!isVoiceEnabled || !character || !storyPages.length) return;
      if (hasPregeneratedRef.current || isPregenerating) return;

      hasPregeneratedRef.current = true;
      setIsPregenerating(true);

      try {
        console.log('🎤 동화책 전체 페이지 TTS 미리 생성 중...');
        
        // 백엔드에 전체 페이지 미리 생성 요청
        const result: PreGenerateResponse = await pregenerateStoryAudio(
          character.voice,  // character_id
          storyPages.map(page => ({
            page: page.page,
            text: page.text
          }))
        );

        // 오디오 URL 맵핑 생성
        const urls: Record<number, string> = {};
        result.pages.forEach(page => {
          if (page.audio_url) {
            urls[page.page] = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${page.audio_url}`;
          }
        });

        setAudioMap(urls);
        onAudioPregenerated?.(urls);
        
        console.log(`✅ ${result.total_pages}개 페이지 TTS 생성 완료!`);
      } catch (error) {
        console.error('❌ 동화 TTS 미리 생성 실패:', error);
        hasPregeneratedRef.current = false;  // 실패 시 재시도 가능하도록
      } finally {
        setIsPregenerating(false);
      }
    };

    pregenerateAllPages();
  }, [isVoiceEnabled, character, storyPages, isPregenerating, onAudioPregenerated]);

  // 페이지가 바뀔 때마다 미리 생성된 오디오 재생
  useEffect(() => {
    const playPageAudio = async () => {
      // 음성이 꺼져있거나, 재생 중이 아니거나, 현재 페이지가 없으면 재생 안 함
      if (!isVoiceEnabled || !isPlaying || !currentPage) return;

      // 이미 읽은 페이지면 무시
      if (currentPage.page === lastReadPageRef.current) return;

      // 이전 오디오 정리
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      try {
        setIsLoadingAudio(true);
        lastReadPageRef.current = currentPage.page;

        let audioUrl: string;

        // MongoDB 스토리의 audio_url이 있으면 우선 사용
        if (currentPage.audio_url) {
          // 상대 경로면 API URL 추가
          if (currentPage.audio_url.startsWith('/')) {
            audioUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${currentPage.audio_url}`;
          } else {
            audioUrl = currentPage.audio_url;
          }
        } 
        // 미리 생성된 오디오 맵에서 찾기
        else if (audioMap[currentPage.page]) {
          audioUrl = audioMap[currentPage.page];
        } 
        // 둘 다 없으면 대기
        else {
          console.log(`⏳ 페이지 ${currentPage.page} 오디오 생성 중...`);
          setIsLoadingAudio(false);
          return;
        }

        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        audio.onended = () => {
          setIsLoadingAudio(false);
        };

        audio.onerror = (error) => {
          console.error('오디오 재생 실패:', error);
          setIsLoadingAudio(false);
        };

        await audio.play();
        console.log(`🔊 페이지 ${currentPage.page} 재생 중`);
      } catch (error) {
        console.error('오디오 재생 실패:', error);
        setIsLoadingAudio(false);
      }
    };

    playPageAudio();

    // 컴포넌트 언마운트 시 오디오 정리
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [currentPage, isVoiceEnabled, isPlaying, audioMap]);

  // 오디오 정지 함수 (외부에서 호출 가능하도록)
  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
      setIsLoadingAudio(false);
    }
  };

  // 전역으로 오디오 정지 함수 노출 (ChatPanel에서 사용)
  useEffect(() => {
    (window as any).stopStoryAudio = stopAudio;
    return () => {
      delete (window as any).stopStoryAudio;
    };
  }, []);

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
          {isPregenerating ? (
            <div className="text-center">
              <div className="text-6xl mb-4 animate-pulse">🎤</div>
              <p className="text-lg font-semibold text-amber-600 mb-2">
                동화 음성 준비 중...
              </p>
              <p className="text-sm text-gray-500">
                {character?.name}의 목소리로<br />
                동화를 미리 생성하고 있어요
              </p>
              <div className="mt-4 flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400">
              <div className="text-6xl mb-4">📚</div>
              <p className="text-lg">
                이야기를 시작하면
                <br />
                여기에 동화가 나타나요
              </p>
            </div>
          )}
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
          {isLoadingAudio && <span className="ml-2">🎤 음성 생성 중...</span>}
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
