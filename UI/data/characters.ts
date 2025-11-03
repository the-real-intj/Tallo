import { Character } from '@/types';

/**
 * 더미 캐릭터 데이터
 * TODO: 백엔드 API에서 가져오도록 변경 필요
 * 
 * 사용 예시:
 * - GET /api/characters - 사용자가 생성한 캐릭터 목록
 * - GET /api/characters/:id - 특정 캐릭터 상세 정보
 */
export const dummyCharacters: Character[] = [
  {
    id: 1,
    name: '뽀로로',
    emoji: '🐧',
    color: 'from-blue-400 to-cyan-400',
    voice: '밝고 활기찬 목소리',
    bgColor: 'bg-blue-50'
  },
  {
    id: 2,
    name: '엘사',
    emoji: '❄️',
    color: 'from-cyan-300 to-blue-300',
    voice: '차분하고 우아한 목소리',
    bgColor: 'bg-cyan-50'
  },
  {
    id: 3,
    name: '토토로',
    emoji: '🌳',
    color: 'from-green-400 to-emerald-400',
    voice: '따뜻하고 포근한 목소리',
    bgColor: 'bg-green-50'
  },
  {
    id: 4,
    name: '피카츄',
    emoji: '⚡',
    color: 'from-yellow-400 to-orange-400',
    voice: '귀엽고 장난스러운 목소리',
    bgColor: 'bg-yellow-50'
  }
];
