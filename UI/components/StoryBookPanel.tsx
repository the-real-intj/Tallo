'use client';

import { useEffect, useRef, useState } from 'react';
import { StoryPage, Character } from '@/types';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '@/lib/api';

interface StoryBookPanelProps {
  currentPage: StoryPage | null;
  totalPages: number;
  isPlaying: boolean;
  isVoiceEnabled?: boolean;
  character?: Character | null;
  storyPages?: StoryPage[];  // 전체 동화 페이지 추가
  storyId?: string;  // 스토리 ID (GridFS 캐싱용)
  storyTitle?: string;  // 동화 제목 (마무리 멘트용)
  selectedStoryPages?: Array<{ page: number; text: string; audio_url?: string | null }>;  // selectedStory.pages 직접 전달
  onNext: () => void;
  onPrevious: () => void;
  onAudioPregenerated?: (audioMap: Record<number, string>) => void;  // 미리 생성 완료 콜백
  onPageAudioEnded?: (page: number) => void;  // 페이지 오디오 재생 완료 콜백
  onPageAudioStart?: (page: number) => void;  // 페이지 오디오 재생 시작 콜백
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
  storyId,
  storyTitle,
  selectedStoryPages,
  onNext,
  onPrevious,
  onAudioPregenerated,
  onPageAudioEnded,
  onPageAudioStart,
}: StoryBookPanelProps) {
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isPregenerating, setIsPregenerating] = useState(false);
  const [audioMap, setAudioMap] = useState<Record<number, string>>({});
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const blobUrlRef = useRef<string | null>(null);  // blob URL 추적용
  const lastReadPageRef = useRef<number>(-1);
  const hasPregeneratedRef = useRef(false);
  
  // 질문/답변 UI는 제거됨 (채팅창으로 이동)

  // 음성 ON 시 전체 동화 미리 생성 비활성화
  // handleStartStory에서 이미 오디오를 생성하므로 중복 방지
  // useEffect(() => {
  //   const pregenerateAllPages = async () => {
  //     if (!isVoiceEnabled || !character || !storyPages.length) return;
  //     if (hasPregeneratedRef.current || isPregenerating) return;

  //     hasPregeneratedRef.current = true;
  //     setIsPregenerating(true);

  //     try {
  //       console.log('🎤 동화책 전체 페이지 TTS 미리 생성 중...');
        
  //       // 백엔드에 전체 페이지 미리 생성 요청
  //       const result: PreGenerateResponse = await pregenerateStoryAudio(
  //         character.voice,  // character_id
  //         storyPages.map(page => ({
  //           page: page.page,
  //           text: page.text
  //         })),
  //         storyId  // story_id (선택)
  //       );

  //       // 오디오 URL 맵핑 생성
  //       const urls: Record<number, string> = {};
  //       result.pages.forEach(page => {
  //         if (page.audio_url) {
  //           // 상대 경로면 API URL 추가
  //           if (page.audio_url.startsWith('/')) {
  //             urls[page.page] = `${API_BASE_URL}${page.audio_url}`;
  //           } else {
  //             urls[page.page] = page.audio_url;
  //           }
  //         }
  //       });

  //       setAudioMap(urls);
  //       onAudioPregenerated?.(urls);
        
  //       console.log(`✅ ${result.total_pages}개 페이지 TTS 생성 완료!`);
  //     } catch (error) {
  //       console.error('❌ 동화 TTS 미리 생성 실패:', error);
  //       hasPregeneratedRef.current = false;  // 실패 시 재시도 가능하도록
  //     } finally {
  //       setIsPregenerating(false);
  //     }
  //   };

  //   pregenerateAllPages();
  // }, [isVoiceEnabled, character, storyPages, isPregenerating, onAudioPregenerated]);
  
  // handleStartStory에서 생성된 오디오 URL을 audioMap에 설정
  // selectedStoryPages를 우선 사용 (더 최신 상태)
  useEffect(() => {
    const pagesToUse = selectedStoryPages || storyPages;
    console.log(`🔍 StoryBookPanel useEffect 트리거:`, {
      hasSelectedStoryPages: !!selectedStoryPages,
      selectedStoryPagesLength: selectedStoryPages?.length,
      hasStoryPages: !!storyPages,
      storyPagesLength: storyPages?.length,
      pagesToUseLength: pagesToUse?.length
    });
    
    if (pagesToUse && pagesToUse.length > 0) {
      const urls: Record<number, string> = {};
      const audioUrlDetails: Array<{page: number, audio_url: string | null | undefined}> = [];
      
      pagesToUse.forEach(page => {
        audioUrlDetails.push({ page: page.page, audio_url: page.audio_url });
        // audio_url이 null이 아니고 undefined가 아니고 빈 문자열이 아닐 때만 추가
        if (page.audio_url && page.audio_url !== null && page.audio_url !== '') {
          // 상대 경로면 API URL 추가
          if (page.audio_url.startsWith('/')) {
            urls[page.page] = `${API_BASE_URL}${page.audio_url}`;
          } else if (page.audio_url.startsWith('http')) {
            urls[page.page] = page.audio_url;
          } else {
            urls[page.page] = `${API_BASE_URL}/${page.audio_url}`;
          }
        }
      });
      
      console.log(`🗺️ audioMap 업데이트 시도:`, {
        urls,
        audioUrlDetails,
        urlsCount: Object.keys(urls).length
      });
      console.log(`🗺️ pagesToUse 전체:`, pagesToUse);
      
      if (Object.keys(urls).length > 0) {
        setAudioMap(urls);
        onAudioPregenerated?.(urls);
        // 오디오 URL이 새로 추가되면 lastReadPageRef 초기화하여 재실행 가능하게
        if (currentPage && urls[currentPage.page]) {
          console.log(`🔄 lastReadPageRef 초기화 (페이지 ${currentPage.page} 오디오 새로 추가)`);
          lastReadPageRef.current = -1;
        }
      } else {
        console.log(`⚠️ audioMap이 비어있음 - pagesToUse에 audio_url이 없음`);
        console.log(`⚠️ audioUrlDetails:`, audioUrlDetails);
      }
    } else {
      console.log(`⚠️ pagesToUse가 비어있음`);
    }
  }, [selectedStoryPages, storyPages, currentPage, API_BASE_URL]);

  // 페이지 오디오 재생 함수 (외부에서 호출 가능)
  const playPageAudio = async (pageNum?: number) => {
    const targetPage = pageNum || currentPage?.page;
    if (!targetPage) return;
    
    // 해당 페이지 정보 찾기
    const targetPageData = selectedStoryPages?.find(p => p.page === targetPage) || 
                          storyPages.find(p => p.page === targetPage);
    
    if (!targetPageData) {
      console.warn(`⚠️ 페이지 ${targetPage} 정보를 찾을 수 없음`);
      return;
    }

    // 음성이 꺼져있거나, 재생 중이 아니면 재생 안 함
    if (!isVoiceEnabled || !isPlaying) {
      console.log(`⏸️ 재생 조건 불만족: isVoiceEnabled=${isVoiceEnabled}, isPlaying=${isPlaying}`);
      return;
    }

    // 이미 읽은 페이지면 무시 (단, audio_url이 새로 생겼으면 재실행)
    const hasAudio = targetPageData.audio_url || audioMap[targetPage];
    if (targetPage === lastReadPageRef.current) {
      // 오디오가 새로 생겼으면 재실행
      if (hasAudio) {
        lastReadPageRef.current = -1;
      } else {
        return;
      }
    }

      // 이전 오디오 정리
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      // 이전 blob URL 정리
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }

      try {
        setIsLoadingAudio(true);

        let audioUrl: string | null = null;

        // 1. targetPageData.audio_url 우선 확인
        if (targetPageData.audio_url) {
          if (targetPageData.audio_url.startsWith('http')) {
            // 이미 절대 URL
            audioUrl = targetPageData.audio_url;
          } else if (targetPageData.audio_url.startsWith('/')) {
            // 상대 경로면 API URL 추가
            audioUrl = `${API_BASE_URL}${targetPageData.audio_url}`;
          } else {
            // 경로만 있으면 API URL 추가
            audioUrl = `${API_BASE_URL}/${targetPageData.audio_url}`;
          }
        }
        
        // 2. audioMap에서 찾기 (이미 API_BASE_URL이 붙어있음)
        if (!audioUrl && audioMap[targetPage]) {
          audioUrl = audioMap[targetPage];
        }
        
        // 3. 둘 다 없으면 대기
        if (!audioUrl) {
          console.log(`⏳ 페이지 ${targetPage} 오디오 생성 중...`);
          setIsLoadingAudio(false);
          return;
        }

        console.log(`🎵 페이지 ${targetPage} 오디오 URL: ${audioUrl}`);
        
        // 재생 시작 콜백
        if (onPageAudioStart) {
          onPageAudioStart(targetPage);
        }
        
        // fetch로 오디오를 blob으로 가져온 후 Object URL 생성 (CORS/형식 문제 해결)
        try {
          const response = await fetch(audioUrl, {
            method: 'GET',
            headers: {
              'ngrok-skip-browser-warning': 'true'
            }
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const blob = await response.blob();
          console.log(`📦 오디오 blob 생성: ${blob.size} bytes, type: ${blob.type}`);
          
          // blob URL 생성
          const blobUrl = URL.createObjectURL(blob);
          blobUrlRef.current = blobUrl;  // ref에 저장
          console.log(`🔗 Blob URL 생성: ${blobUrl}`);
          
          const audio = new Audio(blobUrl);
          audioRef.current = audio;
          
          // 오디오 재생 시작 시 lastReadPageRef 설정
          lastReadPageRef.current = targetPage;

          audio.onended = async () => {
            setIsLoadingAudio(false);
            // 메모리 정리
            if (blobUrlRef.current) {
              URL.revokeObjectURL(blobUrlRef.current);
              blobUrlRef.current = null;
            }
            
            // 페이지 오디오 재생 완료 콜백 호출
            if (onPageAudioEnded) {
              onPageAudioEnded(targetPage);
            } else {
              // 콜백이 없으면 기본 동작: 다음 페이지로 이동
              if (targetPage < totalPages) {
                onNext();
              }
            }
          };

          audio.onerror = (error) => {
            console.error('❌ 오디오 재생 실패:', error);
            console.error('❌ 오디오 요소 src:', audio.src);
            console.error('❌ 오디오 요소 readyState:', audio.readyState);
            console.error('❌ 오디오 요소 networkState:', audio.networkState);
            console.error('❌ 오디오 요소 error:', audio.error);
            setIsLoadingAudio(false);
            // 메모리 정리
            if (blobUrlRef.current) {
              URL.revokeObjectURL(blobUrlRef.current);
              blobUrlRef.current = null;
            }
          };

          await audio.play();
          console.log(`🔊 페이지 ${targetPage} 재생 중`);
        } catch (fetchError) {
          console.error('❌ 오디오 fetch 실패:', fetchError);
          setIsLoadingAudio(false);
        }
      } catch (error) {
        console.error('오디오 재생 실패:', error);
        setIsLoadingAudio(false);
      }
    };

  // 오디오 정지 함수 (외부에서 호출 가능하도록)
  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
      setIsLoadingAudio(false);
    }
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
  };

  // 전역 함수로 등록 (page.tsx에서 호출 가능하도록)
  useEffect(() => {
    (window as any).playPageAudio = playPageAudio;
    (window as any).stopStoryAudio = stopAudio;
    
    return () => {
      delete (window as any).playPageAudio;
      delete (window as any).stopStoryAudio;
    };
  }, [isVoiceEnabled, isPlaying, selectedStoryPages, storyPages, audioMap, totalPages, onNext, onPageAudioEnded, onPageAudioStart]);

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

          {/* 질문/답변 UI는 채팅창으로 이동됨 */}

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
