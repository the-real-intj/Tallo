'use client';

import { Character, Emotion } from '@/types';
import { cn } from '@/lib/utils';

interface CharacterViewerProps {
  character: Character | null;
  isPlaying: boolean;
  currentEmotion?: Emotion;
}

/**
 * 캐릭터 뷰어 컴포넌트
 * 중앙에 캐릭터를 표시하고 애니메이션 제공
 * 
 * TODO: Three.js로 3D 캐릭터 렌더링
 * - @react-three/fiber 사용
 * - GLTF 모델 로드
 * - 립싱크 애니메이션 (Rhubarb phoneme 데이터 기반)
 * - 표정 블렌드셰이프 제어
 */
export function CharacterViewer({ 
  character, 
  isPlaying, 
  currentEmotion = 'neutral' 
}: CharacterViewerProps) {
  const emotionEmojis: Record<Emotion, string> = {
    happy: '😊',
    sad: '😢',
    excited: '😮',
    neutral: '😐',
    surprised: '😲',
  };

  if (!character) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full h-full bg-gradient-to-br from-blue-100 to-purple-100 rounded-3xl shadow-2xl flex items-center justify-center">
          <div className="text-center text-gray-400">
            <div className="text-6xl mb-4">🎭</div>
            <p className="text-xl">캐릭터를 선택해주세요</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="w-full h-full bg-gradient-to-br from-blue-100 to-purple-100 rounded-3xl shadow-2xl flex items-center justify-center overflow-hidden relative">
        {/* 배경 장식 */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 text-6xl">✨</div>
          <div className="absolute top-20 right-20 text-5xl">🌟</div>
          <div className="absolute bottom-20 left-20 text-5xl">💫</div>
          <div className="absolute bottom-10 right-10 text-6xl">⭐</div>
        </div>

        {/* TODO: 여기에 Three.js 캔버스 추가 */}
        {/* <Canvas>
          <Suspense fallback={<Loader />}>
            <CharacterModel
              modelUrl={character.visual?.modelUrl}
              emotion={currentEmotion}
              isPlaying={isPlaying}
            />
          </Suspense>
        </Canvas> */}

        {/* 캐릭터 이미지 또는 이모지 */}
        <div className="relative z-10">
          {character.imageUrl ? (
            <div
              className={cn(
                'flex items-center justify-center',
                isPlaying ? 'animate-bounce' : 'animate-character-pulse'
              )}
            >
              <img
                src={character.imageUrl}
                alt={character.name}
                width={320}
                height={320}
                className="object-contain"
                style={{ background: 'transparent' }}
              />
            </div>
          ) : (
            <div
              className={cn(
                'text-[20rem]',
                isPlaying ? 'animate-bounce' : 'animate-character-pulse'
              )}
            >
              {character.emoji}
            </div>
          )}

          {/* 말하는 중 표시 */}
          {isPlaying && (
            <div className="absolute -bottom-10 left-1/2 transform -translate-x-1/2 bg-white px-6 py-2 rounded-full shadow-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-ping"></div>
                <span className="text-sm font-medium text-gray-700">
                  말하는 중...
                </span>
              </div>
            </div>
          )}
        </div>

        {/* 감정 표시기 */}
        <div className="absolute top-6 right-6 bg-white/90 backdrop-blur-sm rounded-2xl p-4 shadow-lg">
          <div className="text-xs text-gray-600 mb-2">현재 감정</div>
          <div className="flex gap-2">
            {(['happy', 'surprised', 'sad'] as Emotion[]).map((emotion) => (
              <div
                key={emotion}
                className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center text-xl transition-all',
                  currentEmotion === emotion
                    ? 'bg-yellow-200 scale-110'
                    : 'bg-gray-100 opacity-50'
                )}
              >
                {emotionEmojis[emotion]}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
