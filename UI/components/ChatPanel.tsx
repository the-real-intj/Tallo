'use client';

import { useEffect, useRef, useState } from 'react';
import { Character, Message } from '@/types';
import { cn } from '@/lib/utils';
import { ttsClient } from '@/lib/tts-client';

interface ChatPanelProps {
  character: Character;
  messages: Message[];
  isVoiceEnabled: boolean;
  onClose: () => void;
}

/**
 * 채팅 패널 컴포넌트
 * 캐릭터와의 대화를 표시
 */
export function ChatPanel({ character, messages, isVoiceEnabled, onClose }: ChatPanelProps) {
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastProcessedMessageIdRef = useRef<number>(-1);

  // 새 메시지가 추가되면 자동 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 새로운 캐릭터 메시지가 추가되면 TTS 음성 재생
  useEffect(() => {
    const playTTS = async () => {
      // 음성이 꺼져있으면 재생하지 않음
      if (!isVoiceEnabled) return;

      // 마지막 메시지가 캐릭터 메시지인지 확인
      if (messages.length === 0) return;

      const lastMessage = messages[messages.length - 1];

      // 이미 처리한 메시지거나 사용자 메시지면 무시
      if (lastMessage.id <= lastProcessedMessageIdRef.current || lastMessage.type !== 'character') {
        return;
      }

      // 이전 오디오 정리
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      try {
        setIsLoadingAudio(true);
        lastProcessedMessageIdRef.current = lastMessage.id;

        // TTS API 호출
        const audioBlob = await ttsClient.generateTTS({
          text: lastMessage.text,
          character_id: character.voice, // 'heartsping', 'female-child-01', etc.
          language: 'ko', // 한국어 (Zonos는 'ko' 지원)
          speaking_rate: 1.0,
          pitch: 1.0,
          emotion: null,
        });

        // 오디오 URL 생성 및 재생
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
        };

        await audio.play();
      } catch (error) {
        console.error('TTS 생성 실패:', error);
      } finally {
        setIsLoadingAudio(false);
      }
    };

    playTTS();

    // 컴포넌트 언마운트 시 오디오 정리
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [messages, character.voice, isVoiceEnabled]);

  return (
    <>
      {/* 선택된 캐릭터 정보 */}
      <div className={cn('p-4 border-b-2 border-gray-200', character.bgColor)}>
        <div className="flex items-center gap-3">
          <div className="text-4xl">{character.emoji}</div>
          <div className="flex-1">
            <div className="font-bold text-gray-800">{character.name}</div>
            <div className="text-xs text-gray-600">
              {character.voice}
              {isLoadingAudio && <span className="ml-2 text-purple-600">🎤 생성 중...</span>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
            aria-label="캐릭터 변경"
          >
            ✕
          </button>
        </div>
      </div>

      {/* 채팅 영역 */}
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              'chat-message flex animate-slide-in',
              msg.type === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                'max-w-[80%] rounded-2xl p-3',
                msg.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : `bg-gradient-to-r ${character.color} text-gray-800`
              )}
            >
              {msg.type === 'character' && (
                <div className="text-2xl mb-1">{character.emoji}</div>
              )}
              <div className="text-sm text-gray-900">{msg.text}</div>
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
    </>
  );
}
