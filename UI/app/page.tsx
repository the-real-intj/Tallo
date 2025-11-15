'use client';

import { useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { dummyStoryPages } from '@/data/storyPages';
import { CharacterSelector } from '@/components/CharacterSelector';
import { ChatPanel } from '@/components/ChatPanel';
import { CharacterViewer } from '@/components/CharacterViewer';
import { StoryBookPanel } from '@/components/StoryBookPanel';
import { ChoiceButtons } from '@/components/ChoiceButtons';
import { delay } from '@/lib/utils';
import type { Choice } from '@/types';

/**
 * 메인 페이지
 * 프로토타입의 모든 기능을 통합
 */
export default function HomePage() {
  const {
    selectedCharacter,
    currentPage,
    messages,
    isPlaying,
    currentEmotion,
    isVoiceEnabled,
    setSelectedCharacter,
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

  // 이야기 시작
  const handleStartStory = async () => {
    setIsPlaying(true);
    setCurrentPage(1);
    setCurrentEmotion('happy');
    
    addMessage('character', '좋아! 그럼 이야기를 시작해볼까?');
    
    await delay(1000);
    addMessage('character', dummyStoryPages[0].text);
  };

  // 선택지 선택
  const handleChoice = async (choice: Choice) => {
    addMessage('user', choice.text);
    
    await delay(800);
    setCurrentPage(choice.next);
    
    const nextPage = dummyStoryPages.find((p) => p.page === choice.next);
    if (nextPage) {
      addMessage('character', nextPage.text);
      setCurrentEmotion('excited');
    }
  };

  // 다음 페이지
  const handleNextPage = async () => {
    if (currentPage < dummyStoryPages.length) {
      setCurrentPage(currentPage + 1);
      const nextPageData = dummyStoryPages.find((p) => p.page === currentPage + 1);
      
      if (nextPageData) {
        await delay(300);
        addMessage('character', nextPageData.text);
      }
    }
  };

  // 이전 페이지
  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  // 현재 동화 페이지
  const currentStoryPage = dummyStoryPages.find((p) => p.page === currentPage);

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
              onClose={() => setSelectedCharacter(null)}
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
              disabled={!selectedCharacter}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-bold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🎬 이야기 시작하기
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

      {/* 우측 패널: 동화책 뷰어 */}
      <StoryBookPanel
        currentPage={currentStoryPage || null}
        totalPages={dummyStoryPages.length}
        isPlaying={isPlaying}
        isVoiceEnabled={isVoiceEnabled}
        character={selectedCharacter}
        storyPages={dummyStoryPages}
        onNext={handleNextPage}
        onPrevious={handlePreviousPage}
      />
    </div>
  );
}
