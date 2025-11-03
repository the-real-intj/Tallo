import { StoryPage } from '@/types';

/**
 * 더미 동화 페이지 데이터
 * TODO: 백엔드 API에서 생성된 동화를 가져오도록 변경 필요
 * 
 * 사용 예시:
 * - POST /api/stories - 키워드로 새 동화 생성
 * - GET /api/stories/:id - 특정 동화 가져오기
 * - WebSocket /api/stories/ws/:id/play - 실시간 인터랙티브 재생
 */
export const dummyStoryPages: StoryPage[] = [
  {
    page: 1,
    text: "옛날 옛적, 푸른 바다 너머 작은 섬에 용감한 탐험가 친구가 살고 있었어요.",
    image: "🏝️",
    choices: null
  },
  {
    page: 2,
    text: "어느 날 하늘에서 반짝이는 별똥별이 떨어지는 것을 보았어요. 어디로 떨어졌을까요?",
    image: "⭐",
    choices: [
      { text: "숲 속으로 떨어졌어요", next: 3 },
      { text: "바닷가로 떨어졌어요", next: 4 }
    ]
  },
  {
    page: 3,
    text: "깊은 숲 속으로 들어가니 신비로운 빛이 나는 크리스탈을 발견했어요!",
    image: "💎",
    choices: null
  },
  {
    page: 4,
    text: "바닷가에서 반짝이는 조개껍질 속에 마법의 진주를 찾았어요!",
    image: "🐚",
    choices: null
  },
  {
    page: 5,
    text: "그리고 친구와 함께 영원히 행복하게 살았답니다. 끝!",
    image: "🌈",
    choices: null
  }
];

/**
 * 동화 생성 키워드 예시
 * TODO: 사용자 입력 받아서 LLM으로 동화 생성
 */
export const exampleKeywords = [
  '우정', '모험', '용기', '바다', '마법',
  '숲', '별', '친구', '꿈', '보물'
];
