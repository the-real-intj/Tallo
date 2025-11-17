'use client';

import { useState } from 'react';
import { dummyCharacters } from '@/data/characters';
import { pigStoryPages } from '@/data/storyPages';
import { StoryTTSButton } from '@/components/StoryTTSButton';

/**
 * TTS 테스트 페이지
 * 아나 캐릭터로 아기돼지삼형제 일부를 읽을 수 있음
 */
export default function TestTTSPage() {
  const anaCharacter = dummyCharacters.find(c => c.name === '아나');
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const currentStoryPage = pigStoryPages[currentPageIndex];

  const handleNext = () => {
    if (currentPageIndex < pigStoryPages.length - 1) {
      setCurrentPageIndex(currentPageIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentPageIndex > 0) {
      setCurrentPageIndex(currentPageIndex - 1);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">
            🎤 TTS 테스트
          </h1>
          <p className="text-gray-600">
            아나 목소리로 아기돼지삼형제 동화 듣기
          </p>
        </div>

        {/* 캐릭터 정보 */}
        {anaCharacter && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex items-center gap-4">
              <div className={`text-6xl bg-gradient-to-r ${anaCharacter.color} bg-clip-text text-transparent`}>
                {anaCharacter.emoji}
              </div>
              <div>
                <h2 className="text-2xl font-bold">{anaCharacter.name}</h2>
                <p className="text-gray-600">{anaCharacter.voice}</p>
                {anaCharacter.ttsModel && (
                  <p className="text-sm text-purple-600 mt-1">
                    TTS 모델: {anaCharacter.ttsModel}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 동화 페이지 */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          {/* 페이지 번호 */}
          <div className="flex items-center justify-between mb-6">
            <span className="text-sm text-gray-500">
              페이지 {currentPageIndex + 1} / {pigStoryPages.length}
            </span>
            <span className="text-4xl">{currentStoryPage.image}</span>
          </div>

          {/* 텍스트 */}
          <div className="text-lg leading-relaxed mb-8 min-h-[120px]">
            {currentStoryPage.text}
          </div>

          {/* TTS 버튼 */}
          <div className="flex justify-center mb-6">
            <StoryTTSButton 
              text={currentStoryPage.text}
              characterName={anaCharacter?.name}
              ttsModel={anaCharacter?.ttsModel}
              autoEmotion={true}
            />
          </div>

          {/* 선택지 (있는 경우) */}
          {currentStoryPage.choices && (
            <div className="border-t pt-6">
              <p className="text-sm text-gray-600 mb-3">어떻게 할까요?</p>
              <div className="flex gap-3">
                {currentStoryPage.choices.map((choice, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentPageIndex(choice.next - 1)}
                    className="flex-1 bg-gradient-to-r from-blue-500 to-purple-500 text-white py-3 px-4 rounded-lg hover:scale-105 transition-transform"
                  >
                    {choice.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 페이지 네비게이션 */}
          <div className="flex gap-3 mt-6 pt-6 border-t">
            <button
              onClick={handlePrevious}
              disabled={currentPageIndex === 0}
              className="flex-1 bg-gray-200 hover:bg-gray-300 disabled:opacity-30 disabled:cursor-not-allowed py-3 px-6 rounded-lg font-medium transition-all"
            >
              ← 이전
            </button>
            <button
              onClick={handleNext}
              disabled={currentPageIndex === pigStoryPages.length - 1}
              className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-30 disabled:cursor-not-allowed text-white py-3 px-6 rounded-lg font-medium transition-all"
            >
              다음 →
            </button>
          </div>
        </div>

        {/* 설명 */}
        <div className="bg-blue-50 rounded-lg p-6 text-sm text-gray-700">
          <h3 className="font-bold mb-2">💡 사용 방법</h3>
          <ul className="space-y-1 list-disc list-inside">
            <li>버튼을 클릭하면 아나 목소리로 텍스트를 읽어줍니다</li>
            <li>감정은 텍스트 내용에 따라 자동으로 적용됩니다</li>
            <li>이전/다음 버튼으로 페이지를 넘길 수 있습니다</li>
            <li>선택지가 있는 페이지에서는 원하는 선택을 할 수 있습니다</li>
          </ul>
          <p className="mt-3 text-xs text-gray-500">
            ⚠️ TTS 서버가 실행 중이어야 합니다: <code>http://localhost:8001</code>
          </p>
        </div>
      </div>
    </div>
  );
}


