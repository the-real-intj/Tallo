import axios from 'axios';
import { CharacterResponse, StoryResponse } from '@/types';

/**
 * API 베이스 URL
 * TODO: 환경 변수로 관리 (.env.local)
 * NEXT_PUBLIC_API_URL=http://localhost:8000
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',  // ngrok CORS 우회
  },
  // TODO: 인증 토큰 추가 (getToken 함수 구현 필요)
  // headers: {
  //   Authorization: `Bearer ${getToken()}`,
  // },
});

/**
 * ==========================================
 * 캐릭터 API
 * ==========================================
 */

/**
 * 사용자가 생성한 캐릭터 목록 조회
 * GET /characters
 */
export async function fetchCharacters(): Promise<CharacterResponse[]> {
  const response = await apiClient.get('/characters');
  return response.data;
}

/**
 * 새 캐릭터 생성 (유튜브 또는 파일 업로드)
 * TODO: 백엔드 FastAPI 엔드포인트 연동
 * POST /api/characters
 */
export async function createCharacter(data: {
  name: string;
  sourceType: 'youtube' | 'upload';
  sourceUrl?: string;
  files?: File[];
}): Promise<CharacterResponse> {
  const formData = new FormData();
  formData.append('name', data.name);
  formData.append('sourceType', data.sourceType);
  if (data.sourceUrl) formData.append('sourceUrl', data.sourceUrl);
  if (data.files) {
    data.files.forEach(file => formData.append('files', file));
  }
  const response = await apiClient.post('/api/characters', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
}

/**
 * 캐릭터 학습 상태 조회
 * TODO: 백엔드 FastAPI 엔드포인트 연동
 * GET /api/characters/:id/status
 */
export async function getCharacterStatus(characterId: string) {
  // TODO: 실제 API 호출로 변경
   const response = await apiClient.get(`/api/characters/${characterId}/status`);
   return response.data;
  
  console.warn('[API] getCharacterStatus: 더미 응답 반환. 백엔드 연동 필요');
  return Promise.resolve({
    id: characterId,
    status: 'ready',
    progress: 100,
  });
}

/**
 * ==========================================
 * 동화 API
 * ==========================================
 */

/**
 * 키워드 기반 동화 생성
 * TODO: 백엔드 FastAPI 엔드포인트 연동
 * POST /api/stories
 */
export async function createStory(data: {
  keywords: string[];
  characterIds: string[];
  ageGroup: string;
}): Promise<StoryResponse> {
  // TODO: 실제 API 호출로 변경
   const response = await apiClient.post('/api/stories', data);
   return response.data;
  
  console.warn('[API] createStory: 더미 응답 반환. 백엔드 연동 필요');
  return Promise.resolve({
    id: `story_${Date.now()}`,
    title: '마법의 모험',
    type: 'interactive',
    script: [],
    choices: [],
  });
}

/**
 * 동화 상세 조회
 * TODO: 백엔드 FastAPI 엔드포인트 연동
 * GET /api/stories/:id
 */
export async function getStory(storyId: string): Promise<StoryResponse> {
  // TODO: 실제 API 호출로 변경
  // const response = await apiClient.get(`/api/stories/${storyId}`);
  // return response.data;
  
  console.warn('[API] getStory: 더미 응답 반환. 백엔드 연동 필요');
  return Promise.resolve({
    id: storyId,
    title: '마법의 모험',
    type: 'interactive',
    script: [],
  });
}

/**
 * ==========================================
 * WebSocket (실시간 인터랙티브 재생)
 * ==========================================
 */

/**
 * WebSocket 연결 생성
 * TODO: 백엔드 WebSocket 엔드포인트 연동
 * WS /api/stories/ws/:storyId/play
 */
export function createStoryWebSocket(storyId: string): WebSocket | null {
  // TODO: 실제 WebSocket 연결로 변경
   const ws = new WebSocket(`ws://localhost:8000/api/stories/ws/${storyId}/play`);
  // 
   ws.onopen = () => {
     console.log('[WebSocket] 연결됨');
   };
  // 
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
       // 메시지 타입별 처리
       switch (data.type) {
         case 'audio':
           // 오디오 재생
           break;
         case 'choice':
           // 선택지 표시
         break;
     case 'end':
  //       // 동화 종료
         break;
     }
   };
   
   ws.onerror = (error) => {
     console.error('[WebSocket] 에러:', error);
   };
   
   ws.onclose = () => {
     console.log('[WebSocket] 연결 종료');
   };
   
   return ws;
  
  console.warn('[API] createStoryWebSocket: 백엔드 WebSocket 연동 필요');
  return null;
}

/**
 * ==========================================
 * 부모 승인 API
 * ==========================================
 */

/**
 * 캐릭터 사용 승인 (부모 권한 필요)
 * TODO: 백엔드 FastAPI 엔드포인트 연동
 * POST /api/characters/:id/approve
 */
export async function approveCharacter(characterId: string, approval: boolean) {
  const response = await apiClient.post(`/api/characters/${characterId}/approve`, {
    approval
  });
  return response.data;
}

/**
 * ==========================================
 * 동화책 TTS 미리 생성 API
 * ==========================================
 */

export interface StoryPage {
  page: number;
  text: string;
  audio_url?: string;
}

export interface PreGenerateResponse {
  character_id: string;
  total_pages: number;
  pages: StoryPage[];
}

/**
 * 동화책 전체 페이지를 미리 TTS 생성
 * POST /stories/pregenerate
 */
export async function pregenerateStoryAudio(
  characterId: string,
  pages: Array<{ page: number; text: string }>
): Promise<PreGenerateResponse> {
  const response = await apiClient.post('/stories/pregenerate', {
    character_id: characterId,
    pages: pages
  });
  return response.data;
}

/**
 * 캐릭터의 동화책 오디오 맵 조회
 * GET /stories/audio/:characterId
 */
export async function getStoryAudioMap(characterId: string): Promise<{
  character_id: string;
  pages: Record<number, string>;
}> {
  const response = await apiClient.get(`/stories/audio/${characterId}`);
  return response.data;
}

/**
 * 캐시된 오디오 파일 URL 생성
 */
export function getCachedAudioUrl(characterId: string, pageNum: number): string {
  return `${API_BASE_URL}/cache/${characterId}/page_${pageNum}.wav`;
}

export default apiClient;
