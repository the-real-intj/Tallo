import { Character } from '@/types';

/**
 * 더미 캐릭터 데이터
 * API에서 캐릭터를 가져올 수 없을 때 사용
 */
export const dummyCharacters: Character[] = [
  {
    id: 1,
    name: '아나',
    emoji: '🎭',
    color: 'from-purple-400 to-pink-400',
    voice: '5fbdc9b344b2', // character_id
    bgColor: 'bg-purple-50',
  },
];

