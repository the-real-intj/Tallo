'use client';

import { dummyCharacters } from '@/data/characters';
import { Character } from '@/types';
import { CharacterCard } from './CharacterCard';

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
  // TODO: API 연동
  // const { data: characters, isLoading, error } = useQuery({
  //   queryKey: ['characters'],
  //   queryFn: fetchCharacters
  // });
  
  const characters = dummyCharacters;

  return (
    <div className="p-6 flex-1 overflow-auto">
      <h2 className="text-lg font-bold mb-4 text-gray-800">
        친구를 선택해주세요!
      </h2>
      
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
