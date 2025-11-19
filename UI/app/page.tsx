'use client';

import { useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { CharacterSelector } from '@/components/CharacterSelector';
import { StorySelector } from '@/components/StorySelector';
import { ChatPanel } from '@/components/ChatPanel';
import { CharacterViewer } from '@/components/CharacterViewer';
import { StoryBookPanel } from '@/components/StoryBookPanel';
import { ChoiceButtons } from '@/components/ChoiceButtons';
import { delay } from '@/lib/utils';
import type { Choice, Story } from '@/types';
import { chatWithLLMAndTTS, pregenerateStoryPagesAudio, checkStoryAudioFiles } from '@/lib/api';

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
    
    // 스토리 선택 시 인사 메시지
    if (selectedCharacter) {
      addMessage(
        'character',
        `${story.title} 이야기를 시작할까?`
      );
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

    // MongoDB 스토리 재생
    setIsPlaying(true);
    setCurrentPage(1);
    setCurrentEmotion('happy');
    
    addMessage('character', `${selectedStory.title} 이야기를 시작할게!`);
    
    // 페이지별 오디오가 없으면 미리 생성
    if (selectedStory.pages && selectedStory.pages.length > 0 && isVoiceEnabled) {
      try {
        // 먼저 이미 생성된 오디오 파일이 있는지 확인
        const audioCheck = await checkStoryAudioFiles(selectedStory.id, selectedCharacter.voice);
        
        if (audioCheck.all_audio_exists && audioCheck.existing_audio.length > 0) {
          // 이미 모든 오디오가 있으면 그대로 사용
          console.log('✅ 이미 생성된 오디오 파일 사용:', audioCheck.existing_audio_count);
          const updatedPages = selectedStory.pages.map(page => {
            const existing = audioCheck.existing_audio.find(ea => ea.page === page.page);
            return existing?.audio_url 
              ? { ...page, audio_url: existing.audio_url }
              : page;
          });
          setSelectedStory({ ...selectedStory, pages: updatedPages });
        } else {
          // 일부만 있거나 없으면 생성
          addMessage('character', '오디오를 준비하고 있어요...');
          const result = await pregenerateStoryPagesAudio(selectedStory.id, selectedCharacter.voice);
          addMessage('character', '준비 완료! 이제 들려드릴게요.');
          
          // 생성된 오디오 URL을 pages에 반영
          if (selectedStory.pages) {
            const updatedPages = selectedStory.pages.map(page => {
              const generated = result.generated_pages.find(gp => gp.page === page.page);
              return generated?.audio_url 
                ? { ...page, audio_url: generated.audio_url }
                : page;
            });
            setSelectedStory({ ...selectedStory, pages: updatedPages });
          }
        }
      } catch (error) {
        console.error('오디오 확인/생성 실패:', error);
        addMessage('character', '오디오 생성에 실패했어요. 텍스트로 읽어드릴게요.');
      }
    }
  };

  // 선택지 선택 (MongoDB 스토리는 단일 페이지이므로 사용 안 함)
  const handleChoice = async (choice: Choice) => {
    addMessage('user', choice.text);
    
    await delay(800);
    // MongoDB 스토리는 선택지가 없으므로 처리하지 않음
    addMessage('character', '좋은 선택이에요!');
    setCurrentEmotion('excited');
  };

  // 다음 페이지
  const handleNextPage = async () => {
    if (!selectedStory || !selectedStory.pages) return;
    
    if (currentPage < selectedStory.pages.length) {
      setCurrentPage(currentPage + 1);
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
              onSendMessage={async (text) => {
                // 사용자 메시지 추가
                addMessage('user', text);
                
                // 스토리 오디오 정지 (이미 ChatPanel에서 처리됨)
                
                // LLM 응답 받기
                try {
                  const response = await chatWithLLMAndTTS({
                    message: text,
                    character_id: selectedCharacter.voice,
                    character_name: selectedCharacter.name,
                    return_audio: true,
                  });
                  
                  // LLM 응답 메시지 추가
                  addMessage('character', response.text);
                  
                  // 오디오 재생 (audio_url이 있으면)
                  if (response.audio_url) {
                    try {
                      // 상대 경로면 API URL 추가
                      let audioUrl: string;
                      if (response.audio_url.startsWith('/')) {
                        audioUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${response.audio_url}`;
                      } else if (response.audio_url.startsWith('http')) {
                        audioUrl = response.audio_url;
                      } else {
                        audioUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/${response.audio_url}`;
                      }
                      
                      const audio = new Audio(audioUrl);
                      
                      // 오디오 로드 및 재생
                      audio.onerror = (e) => {
                        console.error('오디오 재생 실패:', e, audioUrl);
                      };
                      
                      await audio.play();
                      console.log('🔊 LLM TTS 재생 중:', audioUrl);
                    } catch (audioError) {
                      console.error('오디오 재생 중 오류:', audioError);
                    }
                  }
                } catch (error) {
                  console.error('LLM 채팅 에러:', error);
                  addMessage('character', '죄송해요, 답변을 생성하는데 문제가 생겼어요.');
                }
              }}
            />

            {/* 선택지 버튼 (채팅 영역 바로 아래) */}
            {currentStoryPage?.choices && (
              <div className="px-4">
                <ChoiceButtons
                  choices={currentStoryPage.choices}
                  onChoice={handleChoice}
                />
              </div>
            )}
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
          storyId={selectedStory?.id}  // 스토리 ID 전달
          storyTitle={selectedStory?.title}  // 동화 제목 전달
          onNext={handleNextPage}
          onPrevious={handlePreviousPage}
        />
      )}
    </div>
  );
}
