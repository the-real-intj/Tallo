'use client';

import { useEffect, useRef, useState } from 'react';
import { StoryPage, Character } from '@/types';
import { cn } from '@/lib/utils';
import { API_BASE_URL, generateQuestion, generateClosingMessage, chatWithLLMAndTTS } from '@/lib/api';

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
}: StoryBookPanelProps) {
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isPregenerating, setIsPregenerating] = useState(false);
  const [audioMap, setAudioMap] = useState<Record<number, string>>({});
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const blobUrlRef = useRef<string | null>(null);  // blob URL 추적용
  const lastReadPageRef = useRef<number>(-1);
  const hasPregeneratedRef = useRef(false);
  
  // 질문 및 사용자 입력 상태
  const [questionText, setQuestionText] = useState<string | null>(null);
  const [questionAudioUrl, setQuestionAudioUrl] = useState<string | null>(null);
  const [isWaitingForAnswer, setIsWaitingForAnswer] = useState(false);
  const [userAnswer, setUserAnswer] = useState('');
  const [isProcessingAnswer, setIsProcessingAnswer] = useState(false);
  const [closingMessage, setClosingMessage] = useState<string | null>(null);
  const [closingAudioUrl, setClosingAudioUrl] = useState<string | null>(null);
  const questionAudioRef = useRef<HTMLAudioElement | null>(null);
  const closingAudioRef = useRef<HTMLAudioElement | null>(null);

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

  // 페이지가 바뀔 때마다 미리 생성된 오디오 재생
  useEffect(() => {
    const playPageAudio = async () => {
      // 음성이 꺼져있거나, 재생 중이 아니거나, 현재 페이지가 없으면 재생 안 함
      if (!isVoiceEnabled || !isPlaying || !currentPage) return;

      // 이미 읽은 페이지면 무시 (단, audio_url이 새로 생겼으면 재실행)
      const hasAudio = currentPage.audio_url || audioMap[currentPage.page];
      if (currentPage.page === lastReadPageRef.current) {
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

        let audioUrl: string;

        // MongoDB 스토리의 audio_url이 있으면 우선 사용
        if (currentPage.audio_url) {
          // 상대 경로면 API URL 추가
          if (currentPage.audio_url.startsWith('/')) {
            audioUrl = `${API_BASE_URL}${currentPage.audio_url}`;
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
          console.log(`🔍 디버깅: currentPage.audio_url =`, currentPage.audio_url);
          console.log(`🔍 디버깅: audioMap[${currentPage.page}] =`, audioMap[currentPage.page]);
          console.log(`🔍 디버깅: audioMap 전체 =`, audioMap);
          console.log(`🔍 디버깅: storyPages =`, storyPages);
          setIsLoadingAudio(false);
          return;
        }

        console.log(`🎵 오디오 URL: ${audioUrl}`);
        console.log(`📄 currentPage:`, currentPage);
        console.log(`🗺️ audioMap:`, audioMap);
        
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
          lastReadPageRef.current = currentPage.page;

          audio.onended = async () => {
            setIsLoadingAudio(false);
            // 메모리 정리
            if (blobUrlRef.current) {
              URL.revokeObjectURL(blobUrlRef.current);
              blobUrlRef.current = null;
            }
            
            if (!currentPage || !character) return;
            
            // 마지막 페이지인 경우 마무리 멘트 생성
            if (currentPage.page === totalPages) {
              console.log(`✅ 마지막 페이지(${currentPage.page}) 재생 완료, 마무리 멘트 생성`);
              try {
                // 전체 동화 텍스트 수집
                const allText = storyPages?.map(p => p.text).join(' ') || currentPage.text;
                
                const closingResult = await generateClosingMessage({
                  story_title: storyTitle || '동화',
                  story_summary: allText,
                  character_id: character.voice,
                  character_name: character.name,
                });
                
                setClosingMessage(closingResult.text);
                if (closingResult.audio_url) {
                  const closingAudioUrl = closingResult.audio_url.startsWith('/')
                    ? `${API_BASE_URL}${closingResult.audio_url}`
                    : closingResult.audio_url;
                  setClosingAudioUrl(closingAudioUrl);
                  
                  // 마무리 멘트 오디오 재생
                  const response = await fetch(closingAudioUrl, {
                    headers: { 'ngrok-skip-browser-warning': 'true' }
                  });
                  const blob = await response.blob();
                  const blobUrl = URL.createObjectURL(blob);
                  
                  const closingAudio = new Audio(blobUrl);
                  closingAudioRef.current = closingAudio;
                  
                  closingAudio.onended = () => {
                    URL.revokeObjectURL(blobUrl);
                    closingAudioRef.current = null;
                    setClosingMessage(null);
                    setClosingAudioUrl(null);
                  };
                  
                  await closingAudio.play();
                }
              } catch (error) {
                console.error('❌ 마무리 멘트 생성 실패:', error);
              }
              return;
            }
            
            // 페이지가 2의 배수인 경우 질문 생성
            if (currentPage.page % 2 === 0 && currentPage.text) {
              console.log(`❓ 페이지 ${currentPage.page}는 2의 배수, 질문 생성`);
              try {
                const questionResult = await generateQuestion({
                  page_text: currentPage.text,
                  character_id: character.voice,
                  character_name: character.name,
                  story_title: storyTitle,
                });
                
                setQuestionText(questionResult.text);
                if (questionResult.audio_url) {
                  const qAudioUrl = questionResult.audio_url.startsWith('/')
                    ? `${API_BASE_URL}${questionResult.audio_url}`
                    : questionResult.audio_url;
                  setQuestionAudioUrl(qAudioUrl);
                  
                  // 질문 오디오 재생
                  const response = await fetch(qAudioUrl, {
                    headers: { 'ngrok-skip-browser-warning': 'true' }
                  });
                  const blob = await response.blob();
                  const blobUrl = URL.createObjectURL(blob);
                  
                  const questionAudio = new Audio(blobUrl);
                  questionAudioRef.current = questionAudio;
                  
                  questionAudio.onended = () => {
                    URL.revokeObjectURL(blobUrl);
                    questionAudioRef.current = null;
                    setIsWaitingForAnswer(true);
                  };
                  
                  await questionAudio.play();
                } else {
                  setIsWaitingForAnswer(true);
                }
              } catch (error) {
                console.error('❌ 질문 생성 실패:', error);
                // 질문 생성 실패 시 다음 페이지로 이동
                onNext();
              }
            } else {
              // 2의 배수가 아니면 바로 다음 페이지로 이동
              console.log(`⏭️ 페이지 ${currentPage.page} 재생 완료, 다음 페이지로 이동`);
              onNext();
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
          console.log(`🔊 페이지 ${currentPage.page} 재생 중`);
        } catch (fetchError) {
          console.error('❌ 오디오 fetch 실패:', fetchError);
          setIsLoadingAudio(false);
        }
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
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
      if (questionAudioRef.current) {
        questionAudioRef.current.pause();
        questionAudioRef.current = null;
      }
      if (closingAudioRef.current) {
        closingAudioRef.current.pause();
        closingAudioRef.current = null;
      }
    };
  }, [currentPage, isVoiceEnabled, isPlaying, audioMap, storyPages, character, storyTitle, currentPage?.audio_url]);

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

          {/* 질문 표시 */}
          {questionText && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
              <p className="text-sm text-blue-600 font-semibold mb-2">❓ 질문</p>
              <p className="text-lg text-blue-800">{questionText}</p>
            </div>
          )}

          {/* 사용자 답변 입력 */}
          {isWaitingForAnswer && (
            <div className="mb-6 p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
              <p className="text-sm text-yellow-700 font-semibold mb-3">💭 답변을 입력해주세요</p>
              <textarea
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="답변을 입력하세요..."
                className="w-full p-3 border border-yellow-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                rows={3}
              />
              <button
                onClick={async () => {
                  if (!userAnswer.trim() || !character) return;
                  
                  setIsProcessingAnswer(true);
                  try {
                    // LLM이 답변에 대한 응답 생성
                    const response = await chatWithLLMAndTTS({
                      message: `질문: ${questionText}\n사용자 답변: ${userAnswer}\n\n사용자의 답변에 대해 격려하고 아주 간단히 설명해주세요.`,
                      character_id: character.voice,
                      character_name: character.name,
                      return_audio: true,
                    });
                    
                    // 응답 오디오 재생
                    if (response.audio_url) {
                      const responseAudioUrl = response.audio_url.startsWith('/')
                        ? `${API_BASE_URL}${response.audio_url}`
                        : response.audio_url;
                      
                      const responseFetch = await fetch(responseAudioUrl, {
                        headers: { 'ngrok-skip-browser-warning': 'true' }
                      });
                      const blob = await responseFetch.blob();
                      const blobUrl = URL.createObjectURL(blob);
                      
                      const responseAudio = new Audio(blobUrl);
                      
                      responseAudio.onended = () => {
                        URL.revokeObjectURL(blobUrl);
                        // 상태 초기화 및 다음 페이지로 이동
                        setQuestionText(null);
                        setQuestionAudioUrl(null);
                        setIsWaitingForAnswer(false);
                        setUserAnswer('');
                        setIsProcessingAnswer(false);
                        onNext();
                      };
                      
                      await responseAudio.play();
                    } else {
                      // 오디오가 없으면 바로 다음 페이지로
                      setQuestionText(null);
                      setQuestionAudioUrl(null);
                      setIsWaitingForAnswer(false);
                      setUserAnswer('');
                      setIsProcessingAnswer(false);
                      onNext();
                    }
                  } catch (error) {
                    console.error('❌ 답변 처리 실패:', error);
                    setIsProcessingAnswer(false);
                  }
                }}
                disabled={!userAnswer.trim() || isProcessingAnswer}
                className="w-full px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isProcessingAnswer ? '처리 중...' : '답변 제출'}
              </button>
            </div>
          )}

          {/* 마무리 멘트 */}
          {closingMessage && (
            <div className="mb-6 p-4 bg-green-50 rounded-lg border-2 border-green-200">
              <p className="text-sm text-green-600 font-semibold mb-2">🎉 마무리</p>
              <p className="text-lg text-green-800">{closingMessage}</p>
            </div>
          )}

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
