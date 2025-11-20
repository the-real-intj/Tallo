'use client';

import { Character } from '@/types';
import { cn } from '@/lib/utils';

interface CharacterCardProps {
  character: Character;
  isSelected?: boolean;
  onClick: () => void;
}

/**
 * 캐릭터 카드 컴포넌트
 * 캐릭터 선택 화면에서 각 캐릭터를 표시
 */
export function CharacterCard({ character, isSelected, onClick }: CharacterCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'character-card p-4 rounded-2xl border-2 text-center cursor-pointer transition-all',
        'hover:scale-105 hover:shadow-lg',
        isSelected
          ? 'border-blue-500 shadow-xl ring-2 ring-blue-400'
          : 'border-gray-200',
        character.bgColor
      )}
    >
      {character.imageUrl ? (
        <div className="mb-2 flex items-center justify-center">
          <img
            src={character.imageUrl}
            alt={character.name}
            width={80}
            height={80}
            className="object-contain"
            style={{ background: 'transparent' }}
          />
        </div>
      ) : (
        <div className="text-5xl mb-2">{character.emoji}</div>
      )}
      <div className="font-bold text-gray-800">{character.name}</div>
      <div className="text-xs text-gray-600 mt-1">{character.voice}</div>
    </div>
  );
}
