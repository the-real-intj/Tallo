'use client';

import { useState } from 'react';
import { chatWithLLM } from '@/lib/api';
import { synthesizeTTS } from '@/lib/api';

interface LLMChatButtonProps {
  message: string;
  characterName?: string;
  ttsModel?: string;
  onResponse?: (text: string, audioUrl?: string) => void;
}

/**
 * LLM과 대화하고 TTS로 읽어주는 버튼 컴포넌트
 */
export function LLMChatButton({
  message,
  characterName,
  ttsModel,
  onResponse
}: LLMChatButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
  const [responseText, setResponseText] = useState<string>('');

  const handleChat = async () => {
    try {
      setIsLoading(true);

      // 방법 1: LLM 응답 + TTS 함께 받기 (character_id가 있을 때)
      let audioBlob: Blob | null = null;
      let llmResponse: { text: string; audio_url?: string };
      
      if (ttsModel) {
        // TTS와 함께 받기 - chatWithLLMAndTTS 사용
        const { chatWithLLMAndTTS } = await import('@/lib/api');
        llmResponse = await chatWithLLMAndTTS({
          message,
          character_name: characterName,
          character_id: ttsModel, // character_id 전달
          system_prompt: characterName 
            ? `당신은 ${characterName} 캐릭터입니다. 친절하고 따뜻하게 대답해주세요.`
            : '당신은 친절한 동화 작가입니다.'
        });
        
        // audio_url이 있으면 다운로드
        if (llmResponse.audio_url) {
          const audioResponse = await fetch(llmResponse.audio_url);
          audioBlob = await audioResponse.blob();
        } else if (llmResponse.text) {
          // audio_url이 없으면 별도로 TTS 생성
          audioBlob = await synthesizeTTS({
            text: llmResponse.text,
            character_id: ttsModel,
            language: 'ko',
          });
        }
      } else {
        // 텍스트만 받기
        llmResponse = await chatWithLLM({
          message,
          character_name: characterName,
          system_prompt: characterName 
            ? `당신은 ${characterName} 캐릭터입니다. 친절하고 따뜻하게 대답해주세요.`
            : '당신은 친절한 동화 작가입니다.'
        });
      }

      setResponseText(llmResponse.text);

      // 오디오 재생
      if (audioBlob) {
        const audioUrl = URL.createObjectURL(audioBlob);
        const newAudio = new Audio(audioUrl);
        
        newAudio.onended = () => {
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        };

        newAudio.onerror = () => {
          setIsPlaying(false);
          setIsLoading(false);
          alert('오디오 재생 중 오류가 발생했습니다.');
        };

        await newAudio.play();
        setAudio(newAudio);
        setIsPlaying(true);
      }

      // 콜백 호출
      if (onResponse) {
        onResponse(llmResponse.text);
      }

      setIsLoading(false);
    } catch (error) {
      console.error('LLM 채팅 에러:', error);
      setIsLoading(false);
      alert('LLM 응답 생성 중 오류가 발생했습니다.');
    }
  };

  const handleStop = () => {
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      setIsPlaying(false);
    }
  };

  return (
    <div className="space-y-2">
      <button
        onClick={isPlaying ? handleStop : handleChat}
        disabled={isLoading}
        className={`
          px-4 py-2 rounded-lg font-medium transition-all
          ${isPlaying 
            ? 'bg-red-500 hover:bg-red-600 text-white' 
            : 'bg-blue-500 hover:bg-blue-600 text-white'
          }
          ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}
          flex items-center gap-2
        `}
      >
        {isLoading ? (
          <>
            <span className="animate-spin">⏳</span>
            <span>생성 중...</span>
          </>
        ) : isPlaying ? (
          <>
            <span>⏸️</span>
            <span>정지</span>
          </>
        ) : (
          <>
            <span>🤖</span>
            <span>LLM에게 물어보기</span>
          </>
        )}
      </button>

      {responseText && (
        <div className="p-4 bg-gray-100 rounded-lg">
          <p className="text-sm text-gray-700">{responseText}</p>
        </div>
      )}
    </div>
  );
}

