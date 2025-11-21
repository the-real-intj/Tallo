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
  isVoiceEnabled: false,

  setSelectedCharacter: (character) =>
    set({ selectedCharacter: character }),

  setSelectedStory: (story) =>
    set({ selectedStory: story }),

  setCurrentPage: (page) =>
    set({ currentPage: page }),

  addMessage: (type, text) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: Date.now(),
          type,
          text,
          timestamp: Date.now(),
        },
      ],
    })),

  clearMessages: () =>
    set({ messages: [] }),

  setIsPlaying: (playing) =>
    set({ isPlaying: playing }),

  setCurrentEmotion: (emotion) =>
    set({ currentEmotion: emotion }),

  setIsVoiceEnabled: (enabled) =>
    set({ isVoiceEnabled: enabled }),
}));
