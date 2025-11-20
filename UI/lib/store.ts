import { create } from 'zustand';
import { AppState, Character, Emotion } from '@/types';

/**
 * 전역 상태 관리 (Zustand)
 * 
 * 사용 예시:
 * const { selectedCharacter, setSelectedCharacter } = useAppStore();
 */
export const useAppStore = create<AppState>((set) => ({
  selectedCharacter: null,
  selectedStory: null,
  currentPage: 1,
  messages: [],
  isPlaying: false,
  currentEmotion: 'neutral',
  isVoiceEnabled: true,  // 기본값을 true로 변경 (동화 시작 시 음성 자동 활성화)

  setSelectedCharacter: (character) =>
    set({ selectedCharacter: character }),

  setSelectedStory: (story) =>
    set({ selectedStory: story }),

  setCurrentPage: (page) =>
    set({ currentPage: page }),

  addMessage: (type, text) => {
    let newId = 0;
    set((state) => {
      // 고유한 ID 생성: 마지막 메시지 ID + 1 또는 타임스탬프 + 랜덤
      const lastId = state.messages.length > 0 
        ? Math.max(...state.messages.map(m => m.id))
        : 0;
      newId = lastId + 1;
      
      return {
        messages: [
          ...state.messages,
          {
            id: newId,
            type,
            text,
            timestamp: Date.now(),
          },
        ],
      };
    });
    return newId;
  },

  clearMessages: () =>
    set({ messages: [] }),

  setIsPlaying: (playing) =>
    set({ isPlaying: playing }),

  setCurrentEmotion: (emotion) =>
    set({ currentEmotion: emotion }),

  setIsVoiceEnabled: (enabled) =>
    set({ isVoiceEnabled: enabled }),
}));
