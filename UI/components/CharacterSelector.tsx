'use client';

import { dummyCharacters } from '@/data/characters';
import { Character } from '@/types';
import { CharacterCard } from './CharacterCard';
import { useQuery } from '@tanstack/react-query';
import { fetchCharacters } from '@/lib/api';

interface CharacterSelectorProps {
  onSelect: (character: Character) => void;
}

/**
 * 캐릭터 선택 컴포넌트
 * 캐릭터가 선택되기 전에 표시되는 그리드 뷰
 * 
 * TODO: 백엔드 API에서 사용자의 캐릭터 목록을 가져오도록 변경
 * - fetchCharacters() 호출
 * - 로딩 상태 처리
 * - 에러 처리
 * - 캐릭터가 없을 때 "새 캐릭터 만들기" 버튼 표시
 */
export function CharacterSelector({ onSelect }: CharacterSelectorProps) {
  // API 연동 - 실패 시 더미 데이터 사용
  const { data: apiCharacters, isLoading, error } = useQuery({
    queryKey: ['characters'],
    queryFn: fetchCharacters,
    retry: false, // 실패 시 재시도 안 함
    staleTime: 60 * 1000, // 1분
    refetchOnWindowFocus: false,
  });

  // 디버깅 로그
  console.log('[CharacterSelector] isLoading:', isLoading);
  console.log('[CharacterSelector] error:', error);
  console.log('[CharacterSelector] apiCharacters:', apiCharacters);

  // API 데이터를 UI Character 타입으로 변환
  const characters: Character[] = apiCharacters && Array.isArray(apiCharacters)
    ? apiCharacters.map((apiChar) => ({
        id: parseInt(apiChar.id) || 0,
        name: apiChar.name,
        emoji: '🎭', // TODO: API에서 emoji 정보 추가 필요
        color: 'from-purple-400 to-pink-400', // TODO: API에서 color 정보 추가 필요
        voice: apiChar.id, // TTS API에서 사용할 character_id
        bgColor: 'bg-purple-50', // TODO: API에서 bgColor 정보 추가 필요
      }))
    : dummyCharacters;

  console.log('[CharacterSelector] characters:', characters);

  // 로딩 중
  if (isLoading) {
    return (
      <div className="p-6 flex-1 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <div className="text-gray-600">캐릭터를 불러오는 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 flex-1 overflow-auto">
      <h2 className="text-lg font-bold mb-4 text-gray-800">
        친구를 선택해주세요!
      </h2>

      {/* 에러 메시지 */}
      {error && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          API 연결 실패. 더미 데이터를 사용합니다.
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {characters.map((char) => (
          <CharacterCard
            key={char.id}
            character={char}
            onClick={() => onSelect(char)}
          />
        ))}
      </div>
      
      {/* TODO: 새 캐릭터 추가 버튼 */}
      <button
        className="w-full mt-4 p-4 border-2 border-dashed border-gray-300 rounded-2xl text-gray-500 hover:border-purple-400 hover:text-purple-500 transition-all"
        onClick={() => {
          // TODO: 캐릭터 생성 모달 열기
          console.log('캐릭터 생성 모달 열기 (미구현)');
        }}
      >
        <div className="text-3xl mb-1">➕</div>
        <div className="text-sm font-medium">새 캐릭터 만들기</div>
      </button>
    </div>
  );
}
