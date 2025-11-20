import axios from 'axios';
import { CharacterResponse, StoryResponse } from '@/types';

/**
 * API 베이스 URL
 * TODO: 환경 변수로 관리 (.env.local)
 * NEXT_PUBLIC_API_URL=http://localhost:8000
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
 * 새 캐릭터 생성 (오디오 파일 업로드)
 * POST /characters/create
 */
export async function createCharacter(data: {
  name: string;
  description?: string;
  language?: string;
  referenceAudio: File;
}): Promise<CharacterResponse> {
  const formData = new FormData();
  formData.append('name', data.name);
  formData.append('reference_audio', data.referenceAudio);
  if (data.description) formData.append('description', data.description);
  formData.append('language', data.language || 'ko');
  
  const response = await apiClient.post('/characters/create', formData, {
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
 * 동화 API (MongoDB)
 * ==========================================
 */

/**
 * MongoDB에서 동화 목록 조회
 * GET /stories/list?limit=5
 */
export interface StoryPageInfo {
  page: number;
  text: string;
  audio_url?: string;
}

export interface StoryInfo {
  id: string;
  title: string;
  text: string;
  pages?: StoryPageInfo[];  // 페이지별로 나눈 텍스트와 오디오
  audio_url?: string;
  character_id?: string;
  created_at?: string;
}

export interface StoryListResponse {
  stories: StoryInfo[];
  total: number;
}

export async function fetchStories(limit: number = 5): Promise<StoryListResponse> {
  try {
    const response = await apiClient.get('/stories/list', {
      params: { limit }
    });
    return response.data;
  } catch (error) {
    console.error('[API] fetchStories 에러:', error);
    throw error;
  }
}

/**
 * 특정 동화 조회 (MongoDB)
 * GET /stories/{story_id}
 */
export async function getStoryById(storyId: string): Promise<StoryInfo> {
  try {
    const response = await apiClient.get(`/stories/${storyId}`);
    return response.data;
  } catch (error) {
    console.error('[API] getStoryById 에러:', error);
    throw error;
  }
}

/**
 * 로컬 파일 존재 여부 확인 (HEAD 요청)
 */
async function checkLocalFileExists(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, {
      method: 'HEAD',
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * 로컬 오디오 파일 확인 (Next.js 정적 파일 경로)
 */
export async function checkLocalAudioFiles(
  storyId: string,
  characterId: string,
  totalPages: number
): Promise<{
  existing_audio: Array<{ page: number; audio_url: string }>;
  missing_pages: number[];
}> {
  const existing_audio: Array<{ page: number; audio_url: string }> = [];
  const missing_pages: number[] = [];

  // 로컬 파일 경로 (Next.js 정적 파일)
  const localBaseUrl = '/outputs/cache';

  // 각 페이지 확인
  for (let page = 1; page <= totalPages; page++) {
    const localUrl = `${localBaseUrl}/${storyId}/${characterId}/page_${page}.wav`;
    
    // 로컬 파일 존재 여부 확인
    const exists = await checkLocalFileExists(localUrl);
    
    if (exists) {
      existing_audio.push({
        page,
        audio_url: localUrl, // 로컬 경로 (상대 경로)
      });
    } else {
      missing_pages.push(page);
    }
  }

  return {
    existing_audio,
    missing_pages,
  };
}

/**
 * 동화 오디오 파일 확인 (Colab 서버)
 * GET /stories/{story_id}/check-audio
 */
export async function checkStoryAudioFiles(
  storyId: string,
  characterId: string
): Promise<{
  story_id: string;
  character_id: string;
  total_pages: number;
  existing_audio_count: number;
  existing_audio: Array<{
    page: number;
    text: string;
    audio_url: string;
  }>;
  all_audio_exists: boolean;
}> {
  try {
    const response = await apiClient.get(
      `/stories/${storyId}/check-audio`,
      {
        params: { character_id: characterId }
      }
    );
    return response.data;
  } catch (error) {
    console.error('[API] checkStoryAudioFiles 에러:', error);
    throw error;
  }
}

/**
 * 동화 페이지별 오디오 미리 생성
 * POST /stories/{story_id}/pregenerate-audio
 */
export async function pregenerateStoryPagesAudio(
  storyId: string,
  characterId: string
): Promise<{
  story_id: string;
  character_id: string;
  total_pages: number;
  generated_pages: Array<{
    page: number;
    text: string;
    audio_url?: string;
    error?: string;
  }>;
}> {
  try {
    const formData = new FormData();
    formData.append('character_id', characterId);
    
    const response = await apiClient.post(
      `/stories/${storyId}/pregenerate-audio`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return response.data;
  } catch (error) {
    console.error('[API] pregenerateStoryPagesAudio 에러:', error);
    throw error;
  }
}

/**
 * ==========================================
 * LLM API
 * ==========================================
 */

/**
 * LLM 채팅 (텍스트만)
 * POST /llm/chat
 */
export interface LLMChatRequest {
  message: string;
  character_id?: string;
  character_name?: string;
  system_prompt?: string;
  return_audio?: boolean;
}

export interface LLMChatResponse {
  text: string;
  audio_url?: string;
}

export async function chatWithLLM(request: LLMChatRequest): Promise<LLMChatResponse> {
  try {
    const response = await apiClient.post('/llm/chat', {
      ...request,
      return_audio: false,
    });
    return response.data;
  } catch (error) {
    console.error('[API] chatWithLLM 에러:', error);
    throw error;
  }
}

/**
 * LLM 채팅 + TTS 통합
 * POST /llm/chat
 */
export async function chatWithLLMAndTTS(request: LLMChatRequest): Promise<LLMChatResponse> {
  try {
    const response = await apiClient.post('/llm/chat', {
      ...request,
      return_audio: true,
    });
    return response.data;
  } catch (error) {
    console.error('[API] chatWithLLMAndTTS 에러:', error);
    throw error;
  }
}

/**
 * 질문 생성
 * POST /llm/generate-question
 */
export interface GenerateQuestionRequest {
  page_text: string;
  character_id: string;
  character_name?: string;
  story_title?: string;
}

export async function generateQuestion(request: GenerateQuestionRequest): Promise<LLMChatResponse> {
  try {
    const formData = new FormData();
    formData.append('page_text', request.page_text);
    formData.append('character_id', request.character_id);
    if (request.character_name) {
      formData.append('character_name', request.character_name);
    }
    if (request.story_title) {
      formData.append('story_title', request.story_title);
    }
    
    const response = await apiClient.post('/llm/generate-question', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('[API] generateQuestion 에러:', error);
    throw error;
  }
}

/**
 * 마무리 멘트 생성
 * POST /llm/generate-closing
 */
export interface GenerateClosingRequest {
  story_title: string;
  story_summary: string;
  character_id: string;
  character_name?: string;
}

export async function generateClosingMessage(request: GenerateClosingRequest): Promise<LLMChatResponse> {
  try {
    const formData = new FormData();
    formData.append('story_title', request.story_title);
    formData.append('story_summary', request.story_summary);
    formData.append('character_id', request.character_id);
    if (request.character_name) {
      formData.append('character_name', request.character_name);
    }
    
    const response = await apiClient.post('/llm/generate-closing', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('[API] generateClosingMessage 에러:', error);
    throw error;
  }
}

/**
 * ==========================================
 * TTS API
 * ==========================================
 */

/**
 * TTS 생성
 * POST /tts/generate
 */
export interface TTSRequest {
  text: string;
  character_id?: string; // 선택적 (speaker_wav 사용 시)
  language?: string;
  speaking_rate?: number;
  pitch?: number;
  emotion?: string;
  auto_emotion?: boolean; // 자동 감정 인식
  as_file?: boolean; // 파일로 반환 여부
  speaker_wav?: string; // 스피커 WAV 파일 경로 (character_id 대신 사용 가능)
}

export async function synthesizeTTS(request: TTSRequest): Promise<Blob> {
  try {
    const response = await apiClient.post('/tts/generate', request, {
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    console.error('[API] synthesizeTTS 에러:', error);
    throw error;
  }
}

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
  pages: Array<{ page: number; text: string }>,
  storyId?: string
): Promise<PreGenerateResponse> {
  const response = await apiClient.post('/stories/pregenerate', {
    character_id: characterId,
    story_id: storyId || null,
    pages: pages
  });
  return response.data;
}

export default apiClient;
