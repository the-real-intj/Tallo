'use client';

import { useEffect, useRef } from 'react';
import { useAppStore } from '@/lib/store';
import { CharacterSelector } from '@/components/CharacterSelector';
import { StorySelector } from '@/components/StorySelector';
import { ChatPanel } from '@/components/ChatPanel';
import { CharacterViewer } from '@/components/CharacterViewer';
import { StoryBookPanel } from '@/components/StoryBookPanel';
import { delay } from '@/lib/utils';
import type { Story } from '@/types';
import { chatWithLLMAndTTS, pregenerateStoryPagesAudio, checkStoryAudioFiles, checkLocalAudioFiles, API_BASE_URL, generateQuestion, generateClosingMessage } from '@/lib/api';

/**
 * 메인 페이지
 * 프로토타입의 모든 기능을 통합
 */
export default function HomePage() {
  const {
    selectedCharacter,
    selectedStory,
    currentPage,
    messages,
    isPlaying,
    currentEmotion,
    isVoiceEnabled,
    setSelectedCharacter,
    setSelectedStory,
    setCurrentPage,
    addMessage,
    clearMessages,
    setIsPlaying,
    setCurrentEmotion,
    setIsVoiceEnabled,
  } = useAppStore();
  
  // 2마디 대화 카운터 (페이지별로 관리)
  const conversationCountRef = useRef<Record<number, number>>({});
  const currentQuestionRef = useRef<Record<number, string>>({});
  const startMessageIdRef = useRef<number | null>(null); // 시작 메시지 ID 추적
  const closingMessageIdRef = useRef<number | null>(null); // 마무리 메시지 ID 추적 (2번째 대화 완료 후)
  
  // 중앙 오디오 재생 제어
  const isPlayingAudioRef = useRef<boolean>(false); // 현재 오디오 재생 중인지
  const pendingPageAudioRef = useRef<number | null>(null); // 대기 중인 페이지 번호

  // 캐릭터 선택 시 인사 메시지
  useEffect(() => {
    if (selectedCharacter && messages.length === 0) {
      delay(500).then(() => {
        addMessage(
          'character',
          `안녕! 나는 ${selectedCharacter.name}야! 오늘은 어떤 이야기를 들려줄까?`
        );
      });
    }
  }, [selectedCharacter, messages.length, addMessage]);

  // 캐릭터 선택 핸들러
  const handleCharacterSelect = (character: typeof selectedCharacter) => {
    setSelectedCharacter(character);
    clearMessages();
    setCurrentPage(1);
    setIsPlaying(false);
  };

  // 스토리 선택 핸들러
  const handleStorySelect = async (story: Story) => {
    setSelectedStory(story);
    setCurrentPage(1);
    setIsPlaying(false);
    
    // 동화책 선택 시 시작 메시지 추가 (TTS 자동 재생)
    if (selectedCharacter) {
      addMessage('character', `${story.title} 이야기를 시작할게!`);
    }
  };

  // 이야기 시작
  const handleStartStory = async () => {
    if (!selectedStory) {
      addMessage('character', '먼저 동화를 선택해주세요!');
      return;
    }

    if (!selectedCharacter) {
      addMessage('character', '먼저 캐릭터를 선택해주세요!');
      return;
    }

    setCurrentEmotion('happy');
    
    // 시작 메시지는 나중에 추가 (오디오 준비 후)
    
    // 페이지별 오디오가 없으면 미리 생성 (오디오 준비 완료 후 재생 시작)
    let updatedStoryPages = selectedStory.pages;
    if (selectedStory.pages && selectedStory.pages.length > 0 && isVoiceEnabled) {
      try {
        // 1단계: 로컬 파일 먼저 확인
        console.log('🔍 로컬 오디오 파일 확인 시작:', selectedStory.id, selectedCharacter.voice);
        const localCheck = await checkLocalAudioFiles(
          selectedStory.id,
          selectedCharacter.voice,
          selectedStory.pages.length
        );
        console.log('📊 로컬 오디오 확인 결과:', {
          existing: localCheck.existing_audio.length,
          missing: localCheck.missing_pages.length
        });

        // 로컬 파일이 있으면 먼저 매핑
        if (localCheck.existing_audio.length > 0) {
          console.log('✅ 로컬 오디오 파일 매핑:', localCheck.existing_audio.length);
          updatedStoryPages = selectedStory.pages.map(page => {
            const existing = localCheck.existing_audio.find(ea => ea.page === page.page);
            if (existing?.audio_url) {
              console.log(`✅ 로컬 페이지 ${page.page} 오디오 URL:`, existing.audio_url);
              return { ...page, audio_url: existing.audio_url };
            }
            return page;
          });
        }

        // 2단계: 로컬에 없는 파일만 Colab 서버에서 확인
        const missingPages = localCheck.missing_pages;
        if (missingPages.length > 0) {
          console.log(`⚠️ ${missingPages.length}개 페이지 로컬에 없음, Colab 서버 확인...`);
          const audioCheck = await checkStoryAudioFiles(selectedStory.id, selectedCharacter.voice);
          console.log('📊 Colab 서버 확인 결과:', {
          total: audioCheck.total_pages,
          existing: audioCheck.existing_audio_count,
          all_exists: audioCheck.all_audio_exists,
          existing_audio: audioCheck.existing_audio
        });
        
          // 서버에 있는 오디오 매핑 (로컬에 없는 것만)
          if (audioCheck.existing_audio.length > 0 && updatedStoryPages) {
            updatedStoryPages = updatedStoryPages.map(page => {
              // 이미 로컬 오디오가 있으면 유지
              if (page.audio_url) {
                return page;
              }
              // 서버 오디오 찾기
              const serverAudio = audioCheck.existing_audio.find(ea => ea.page === page.page);
              if (serverAudio?.audio_url) {
                let audioUrl = serverAudio.audio_url;
                if (audioUrl.startsWith('/')) {
                  audioUrl = `${API_BASE_URL}${audioUrl}`;
                } else if (!audioUrl.startsWith('http')) {
                  audioUrl = `${API_BASE_URL}/${audioUrl}`;
                }
                console.log(`✅ 서버 페이지 ${page.page} 오디오 URL:`, audioUrl);
                return { ...page, audio_url: audioUrl };
              }
              return page;
            });
          }

          // 3단계: 서버에도 없으면 생성 요청
          const stillMissing = updatedStoryPages?.filter(page => !page.audio_url) || [];
          if (stillMissing.length > 0) {
            console.log(`⚠️ ${stillMissing.length}개 페이지 오디오 없음, 생성 시작...`);
            addMessage('character', '오디오를 준비하고 있어요...');
            const result = await pregenerateStoryPagesAudio(selectedStory.id, selectedCharacter.voice);
            console.log('🎵 pregenerateStoryPagesAudio 결과:', result);
            addMessage('character', '준비 완료! 이제 들려드릴게요.');
            
            // 생성된 오디오 URL을 pages에 반영 (기존 오디오와 병합)
            if (selectedStory.pages && updatedStoryPages) {
              updatedStoryPages = updatedStoryPages.map(page => {
                // 이미 audio_url이 있으면 유지
                if (page.audio_url) {
                  return page;
                }
                // 생성된 오디오 찾기
                const generated = result.generated_pages?.find(gp => gp.page === page.page);
                if (generated?.audio_url) {
                  // audio_url이 상대 경로면 API_BASE_URL 추가
                  let audioUrl = generated.audio_url;
                  if (audioUrl.startsWith('/')) {
                    audioUrl = `${API_BASE_URL}${audioUrl}`;
                  } else if (!audioUrl.startsWith('http')) {
                    audioUrl = `${API_BASE_URL}/${audioUrl}`;
                  }
                  console.log(`✅ 생성된 페이지 ${page.page} 오디오 URL:`, audioUrl);
                  return { ...page, audio_url: audioUrl };
                }
                return page;
              });
            }
          }
        }
        
        // 최종 결과 확인
        if (updatedStoryPages) {
          const finalAudioCount = updatedStoryPages.filter(p => p.audio_url && p.audio_url !== null).length;
          console.log('📝 최종 업데이트된 pages:', {
            total: updatedStoryPages.length,
            with_audio: finalAudioCount,
            pages: updatedStoryPages.map(p => ({ 
              page: p.page, 
              has_audio: !!p.audio_url && p.audio_url !== null,
              audio_url: p.audio_url 
            }))
          });
          
          // 오디오 URL이 업데이트된 pages로 selectedStory 업데이트
          // 새로운 객체를 생성하여 참조 변경 (React가 변경을 감지하도록)
          const updatedStory = { 
            ...selectedStory, 
            pages: updatedStoryPages.map(p => ({ ...p })) // 깊은 복사
          };
          console.log('🔄 selectedStory 업데이트:', {
            storyId: updatedStory.id,
            pagesCount: updatedStory.pages?.length,
            pagesWithAudio: updatedStory.pages?.filter(p => p.audio_url && p.audio_url !== null).length
          });
          setSelectedStory(updatedStory);
        } else {
          console.warn('⚠️ updatedStoryPages가 undefined입니다');
        }
      } catch (error) {
        console.error('❌ 오디오 확인/생성 실패:', error);
        addMessage('character', '오디오 생성에 실패했어요. 텍스트로 읽어드릴게요.');
      }
    }
    
    // 오디오 준비 완료 후 상태 업데이트
    await delay(100);
    setCurrentPage(1);
    
    // 버튼 클릭 시 바로 1페이지부터 재생 시작
    setIsPlaying(true);
    isPlayingAudioRef.current = false; // 페이지 오디오 재생 가능
    
    setTimeout(() => {
      if (selectedStory?.pages && selectedStory.pages.length > 0) {
        console.log('🎵 동화 재생하기 버튼 클릭, 1페이지 오디오 재생 시작');
        if ((window as any).playPageAudio) {
          (window as any).playPageAudio(1);
        } else {
          console.warn('⚠️ playPageAudio 함수를 찾을 수 없음');
        }
      }
    }, 300);
  };


  // 다음 페이지
  const handleNextPage = async () => {
    if (!selectedStory || !selectedStory.pages) return;
    
    if (currentPage < selectedStory.pages.length) {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);  // 1. 페이지 상태 업데이트
      
      // 2. 오디오 재생
      if ((window as any).playPageAudio) {
        (window as any).playPageAudio(nextPage);
      } else {
        console.warn('⚠️ playPageAudio 함수를 찾을 수 없음');
      }
    }
  };

  // 이전 페이지
  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  // 현재 동화 페이지 (선택된 스토리의 pages 배열에서 가져오기)
  const currentStoryPage = selectedStory
    ? (() => {
        // pages 배열이 있으면 사용, 없으면 전체 텍스트를 단일 페이지로
        if (selectedStory.pages && selectedStory.pages.length > 0) {
          const pageInfo = selectedStory.pages.find(p => p.page === currentPage);
          if (pageInfo) {
            return {
              page: currentPage,
              text: pageInfo.text,
              image: '📖',
              choices: null,
              audio_url: pageInfo.audio_url,
            };
          }
        }
        // pages가 없으면 전체 텍스트 사용 (하위 호환)
        return {
          page: 1,
          text: selectedStory.text,
          image: '📖',
          choices: null,
          audio_url: selectedStory.audio_url,
        };
      })()
    : null;

  return (
    <div className="h-screen flex bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 overflow-hidden">
      {/* 좌측 패널: 캐릭터 선택 + 채팅 */}
      <div className="w-96 bg-white shadow-2xl flex flex-col">
        {/* 헤더 */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-6 text-white">
          <h1 className="text-2xl font-bold mb-2">✨ 마법 동화나라</h1>
          <p className="text-sm opacity-90">친구와 함께하는 신나는 모험</p>
        </div>

        {/* 캐릭터 선택 또는 채팅 */}
        {!selectedCharacter ? (
          <CharacterSelector onSelect={handleCharacterSelect} />
        ) : (
          <>
            <ChatPanel
              character={selectedCharacter}
              messages={messages}
              isVoiceEnabled={isVoiceEnabled}
              onClose={() => {
                setSelectedCharacter(null);
                setSelectedStory(null);
              }}
              onTTSComplete={(messageId) => {
                // 마무리 메시지(2번째 대화 완료) TTS 완료 → 다음 페이지로 이동
                if (closingMessageIdRef.current === messageId) {
                  console.log('✅ 마무리 메시지 TTS 완료, 다음 페이지로 이동');
                  closingMessageIdRef.current = null; // 초기화
                  isPlayingAudioRef.current = false; // TTS 완료, 페이지 오디오 재생 가능
                  setTimeout(() => {
                    handleNextPage();
                  }, 300);
                }
                
                // 일반 TTS 완료 후 대기 중인 페이지 오디오 재생
                if (isPlayingAudioRef.current === false && pendingPageAudioRef.current !== null) {
                  const pageToPlay = pendingPageAudioRef.current;
                  pendingPageAudioRef.current = null;
                  if ((window as any).playPageAudio) {
                    (window as any).playPageAudio(pageToPlay);
                  }
                }
              }}
              onSendMessage={async (text) => {
                // 사용자 메시지 추가
                addMessage('user', text);
                
                // 스토리 오디오 정지
                if ((window as any).stopStoryAudio) {
                  (window as any).stopStoryAudio();
                }
                
                // 현재 페이지 확인
                const currentPageNum = currentPage || 1;
                const isQuestionPage = currentPageNum % 2 === 0;
                const questionText = currentQuestionRef.current[currentPageNum];
                
                // 질문 페이지인 경우 2마디 대화 처리
                if (isQuestionPage && questionText) {
                  const conversationCount = conversationCountRef.current[currentPageNum] || 0;
                  const isFirstConversation = conversationCount === 0;
                  
                  // 대화 횟수에 따라 다른 프롬프트 사용
                  let prompt: string;
                  if (isFirstConversation) {
                    // 첫 번째 대화: 공감 + 추가 질문
                    prompt = `질문: ${questionText}\n사용자 답변: ${text}\n\n사용자의 답변에 대해 간단히 공감하고(1문장), 동화 내용과 관련된 질문을 하나 더 해주세요(1문장). 총 1-2문장으로만 답변해주세요.`;
                  } else {
                    // 두 번째 대화: 공감 + 마무리 + 다음 페이지 재생 안내
                    prompt = `이전 질문: ${questionText}\n사용자가 방금 말한 내용: ${text}\n\n사용자의 답변에 대해 간단히 공감하고(1문장), 이제 이야기를 이어서 읽어주겠다는 식으로 마무리해주세요(1문장). 총 1-2문장으로만 답변해주세요. 예: "그렇구나! 그럼 이제 이야기를 이어서 들려줄게!"`;
                  }
                  
                  try {
                    const response = await chatWithLLMAndTTS({
                      message: prompt,
                      character_id: selectedCharacter.voice,
                      character_name: selectedCharacter.name,
                      return_audio: true,
                    });
                    
                    // LLM 응답 메시지 추가
                    const messageId = addMessage('character', response.text);
                    
                    // 대화 카운터 증가
                    const newCount = conversationCount + 1;
                    conversationCountRef.current[currentPageNum] = newCount;
                    
                    // 2마디 대화 완료 여부 확인
                    if (newCount >= 2) {
                      console.log(`✅ 2마디 대화 완료, 마무리 메시지 TTS 재생 대기`);
                      // 마무리 메시지 ID 추적 (TTS 완료 후 다음 페이지로 이동)
                      closingMessageIdRef.current = messageId; // addMessage가 반환한 실제 메시지 ID 사용
                      
                      // 대화 카운터 초기화
                      conversationCountRef.current[currentPageNum] = 0;
                      delete currentQuestionRef.current[currentPageNum];
                      // 다음 페이지 이동은 onTTSComplete에서 처리
                    }
                    
                    // 오디오 재생 (TTS는 ChatPanel에서 자동 처리)
                  } catch (error) {
                    console.error('❌ 답변 처리 실패:', error);
                    addMessage('character', '죄송해요, 답변을 생성하는데 문제가 생겼어요.');
                  }
                } else {
                  // 일반 채팅 (질문 페이지가 아닌 경우)
                  try {
                    const response = await chatWithLLMAndTTS({
                      message: text,
                      character_id: selectedCharacter.voice,
                      character_name: selectedCharacter.name,
                      return_audio: true,
                    });
                    
                    // LLM 응답 메시지 추가
                    addMessage('character', response.text);
                    
                    // 오디오 재생 (TTS는 ChatPanel에서 자동 처리)
                  } catch (error) {
                    console.error('LLM 채팅 에러:', error);
                    addMessage('character', '죄송해요, 답변을 생성하는데 문제가 생겼어요.');
                  }
                }
              }}
            />

          </>
        )}

        {/* 하단 컨트롤 */}
        <div className="p-4 border-t-2 border-gray-200 bg-gray-50">
          {!isPlaying ? (
            <button
              onClick={handleStartStory}
              disabled={!selectedCharacter || !selectedStory}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {selectedStory ? '🎬 동화 재생하기' : '📚 동화를 선택해주세요'}
            </button>
          ) : (
            <div className="flex gap-2">
              <button className="flex-1 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition-all">
                ⏸️ 일시정지
              </button>
              <button
                onClick={() => setIsVoiceEnabled(!isVoiceEnabled)}
                className={`flex-1 py-2 rounded-lg transition-all ${
                  isVoiceEnabled
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
                }`}
              >
                {isVoiceEnabled ? '🔊 음성 ON' : '🔇 음성 OFF'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 중앙 패널: 3D 캐릭터 뷰어 */}
      <CharacterViewer
        character={selectedCharacter}
        isPlaying={isPlaying}
        currentEmotion={currentEmotion}
      />

      {/* 우측 패널: 스토리 선택 또는 동화책 뷰어 */}
      {!selectedStory ? (
        <div className="w-96 bg-white shadow-2xl flex flex-col">
          <div className="bg-gradient-to-r from-blue-500 to-cyan-500 p-6 text-white">
            <h2 className="text-xl font-bold mb-1">📚 동화 선택</h2>
            <p className="text-sm opacity-90">읽고 싶은 동화를 선택하세요</p>
          </div>
          <StorySelector onSelect={handleStorySelect} />
        </div>
      ) : (
        <StoryBookPanel
          currentPage={currentStoryPage || null}
          totalPages={selectedStory?.pages?.length || 1}
          isPlaying={isPlaying}
          isVoiceEnabled={isVoiceEnabled}
          character={selectedCharacter}
          storyPages={selectedStory?.pages?.map(p => ({
            page: p.page,
            text: p.text,
            image: '📖',
            choices: null,
            audio_url: p.audio_url,
          })) || []}
          selectedStoryPages={selectedStory?.pages}  // selectedStory.pages 직접 전달
          storyId={selectedStory?.id}  // 스토리 ID 전달
          storyTitle={selectedStory?.title}  // 동화 제목 전달
          onNext={handleNextPage}
          onPrevious={handlePreviousPage}
          onPageAudioStart={(page: number) => {
            // 페이지 오디오 재생 시작
            isPlayingAudioRef.current = true;
          }}
          onPageAudioEnded={async (page: number) => {
            // 페이지 오디오 재생 완료
            isPlayingAudioRef.current = false;
            
            if (!selectedStory || !selectedCharacter) return;
            
            // 마지막 페이지인 경우 마무리 멘트 생성
            if (page === (selectedStory.pages?.length || 1)) {
              console.log(`✅ 마지막 페이지(${page}) 재생 완료, 마무리 멘트 생성`);
              try {
                const allText = selectedStory.pages?.map(p => p.text).join(' ') || selectedStory.text;
                const closingResult = await generateClosingMessage({
                  story_title: selectedStory.title || '동화',
                  story_summary: allText,
                  character_id: selectedCharacter.voice,
                  character_name: selectedCharacter.name,
                });
                
                // 마무리 멘트를 채팅창에 메시지로 추가 (TTS 자동 재생)
                addMessage('character', closingResult.text);
              } catch (error) {
                console.error('❌ 마무리 멘트 생성 실패:', error);
              }
              return;
            }
            
            // 페이지가 2의 배수인 경우 질문 생성
            if (page % 2 === 0 && selectedStory.pages) {
              const pageData = selectedStory.pages.find(p => p.page === page);
              if (pageData?.text) {
                console.log(`❓ 페이지 ${page}는 2의 배수, 질문 생성`);
                // 대화 카운터 초기화 (새 질문 시작)
                conversationCountRef.current[page] = 0;
                
                try {
                  // 전체 동화책 텍스트 합치기
                  const fullStoryText = selectedStory.pages
                    .map(p => p.text)
                    .join(' ')
                    .trim();
                  
                  // 등장인물 정보 추출 (텍스트에서 등장인물 이름 추출하거나, 백엔드에서 처리)
                  // 현재는 빈 배열로 전달하고 백엔드에서 텍스트 분석하여 추출하도록 함
                  const characters: string[] = [];
                  
                  const questionResult = await generateQuestion({
                    page_text: pageData.text,
                    full_story_text: fullStoryText,
                    characters: characters,
                    character_id: selectedCharacter.voice,
                    character_name: selectedCharacter.name,
                    story_title: selectedStory.title,
                  });
                  
                  // 질문을 채팅창에 메시지로 추가 (TTS 자동 재생)
                  addMessage('character', questionResult.text);
                  currentQuestionRef.current[page] = questionResult.text;
                  
                  // TTS 재생 중이므로 페이지 오디오는 대기 (TTS 완료 후 자동으로 다음 페이지 재생)
                  isPlayingAudioRef.current = true;
                } catch (error) {
                  console.error('❌ 질문 생성 실패:', error);
                  // 질문 생성 실패 시 다음 페이지로 이동
                  handleNextPage();
                }
              }
            } else {
              // 2의 배수가 아니면 바로 다음 페이지로 이동
              console.log(`⏭️ 페이지 ${page} 재생 완료, 다음 페이지로 이동`);
              const nextPage = page + 1;
              if (nextPage <= (selectedStory.pages?.length || 1)) {
                // handleNextPage()가 페이지 상태 변경 + 오디오 재생 둘 다 처리
                handleNextPage();
              }
            }
          }}
        />
      )}
    </div>
  );
}
