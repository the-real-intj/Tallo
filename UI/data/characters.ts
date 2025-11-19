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
    imageUrl: '/characters/ana.png',
    color: 'from-purple-400 to-pink-400',
    voice: '5fbdc9b344b2',
    bgColor: 'bg-purple-50',
  },
  {
    id: 2,
    name: '하츄핑',
    emoji: '🎀',
    imageUrl: '/characters/sijinping.png',
    color: 'from-pink-400 to-purple-400',
    voice: '4c84ef36f400',
    bgColor: 'bg-pink-50',
  },
  {
    id: 3,
    name: '바레사',
    emoji: '🐮',
    imageUrl: '/characters/varesa.png',
    color: 'from-orange-400 to-yellow-400',
    voice: '6a3fb5695d7c',
    bgColor: 'bg-orange-50',
  },
];

