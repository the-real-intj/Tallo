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
    voice: '5fbdc9b344b2',
    bgColor: 'bg-purple-50',
  },
  {
    id: 2,
    name: '하츄핑',
    emoji: '🎀',
    color: 'from-pink-400 to-purple-400',
    voice: '4c84ef36f400',
    bgColor: 'bg-pink-50',
  },
];

