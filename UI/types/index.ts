/**
 * 캐릭터 인터페이스
 * TODO: 백엔드 API 연동 시 실제 Character 모델과 일치시킬 것
 */
export interface Character {
  id: number;
  name: string;
  emoji: string;
  imageUrl?: string; // 캐릭터 이미지 URL (투명 배경 PNG)
  color: string; // Tailwind gradient 클래스 (예: 'from-blue-400 to-cyan-400')
  voice: string;
  bgColor: string; // Tailwind bg 클래스 (예: 'bg-blue-50')
  // TODO: 백엔드 연동 시 추가 필드
  // voiceModelPath?: string;
  // avatarModelUrl?: string;
  // approved?: boolean;
}

/**
 * 선택지 인터페이스
 */
export interface Choice {
  text: string;
  next: number; // 다음 페이지 번호
}

/**
 * 동화 페이지 인터페이스
 * TODO: 백엔드 API 연동 시 실제 StoryPage 모델과 일치시킬 것
 */
export interface StoryPage {
  page: number;
  text: string;
  image: string; // 현재는 이모지, 나중에 이미지 URL로 변경
  choices: Choice[] | null;
  audio_url?: string; // 미리 생성된 오디오 URL (MongoDB 스토리용)
  // TODO: 백엔드 연동 시 추가 필드
  // phonemes?: Phoneme[];
  // emotion?: 'happy' | 'sad' | 'excited' | 'neutral';
}

/**
 * 채팅 메시지 인터페이스
 */
export interface Message {
  id: number;
  type: 'character' | 'user';
  text: string;
  timestamp?: number;
}

/**
 * 감정 타입
 * TODO: 백엔드의 감정 분류와 일치시킬 것
 */
export type Emotion = 'happy' | 'sad' | 'excited' | 'neutral' | 'surprised';

/**
 * 스토리 페이지 인터페이스
 */
export interface StoryPageInfo {
  page: number;
  text: string;
  audio_url?: string;
}

/**
 * 스토리 인터페이스 (MongoDB)
 */
export interface Story {
  id: string;
  title: string;
  text: string;
  pages?: StoryPageInfo[];  // 페이지별로 나눈 텍스트와 오디오
  audio_url?: string;
  character_id?: string;
  created_at?: string;
}

/**
 * 애플리케이션 상태 인터페이스 (Zustand용)
 */
export interface AppState {
  selectedCharacter: Character | null;
  selectedStory: Story | null;
  currentPage: number;
  messages: Message[];
  isPlaying: boolean;
  currentEmotion: Emotion;
  isVoiceEnabled: boolean;
  isStoryCompleted: boolean;

  // Actions
  setSelectedCharacter: (character: Character | null) => void;
  setSelectedStory: (story: Story | null) => void;
  setCurrentPage: (page: number) => void;
  addMessage: (type: 'character' | 'user', text: string) => number;
  clearMessages: () => void;
  setIsPlaying: (playing: boolean) => void;
  setCurrentEmotion: (emotion: Emotion) => void;
  setIsVoiceEnabled: (enabled: boolean) => void;
  setIsStoryCompleted: (completed: boolean) => void;
}

/**
 * API 응답 타입 (백엔드 연동용)
 * TODO: FastAPI 스키마와 일치시킬 것
 */
export interface CharacterResponse {
  id: string;
  name: string;
  voiceModel: {
    status: 'processing' | 'ready' | 'failed';
    modelPath?: string;
  };
  visual: {
    avatarType: '2d' | '3d';
    modelUrl: string;
  };
  approved: boolean;
}

export interface StoryResponse {
  id: string;
  title: string;
  type: 'song' | 'tale' | 'interactive';
  script: {
    characterId: string;
    text: string;
    emotion: Emotion;
    audioUrl: string;
    timestamp: number;
  }[];
  choices?: {
    atTimestamp: number;
    options: {
      text: string;
      nextSceneId: string;
    }[];
  }[];
}
