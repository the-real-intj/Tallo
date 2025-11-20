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
  onSendMessage?: (text: string) => void; // 메시지 전송 핸들러
  onTTSComplete?: (messageId: number) => void; // 특정 메시지의 TTS 재생 완료 콜백
}

/**
 * 채팅 패널 컴포넌트
 * 캐릭터와의 대화를 표시
 */
export function ChatPanel({ character, messages, isVoiceEnabled, onClose, onSendMessage, onTTSComplete }: ChatPanelProps) {
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [inputText, setInputText] = useState('');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastProcessedMessageIdRef = useRef<number>(-1);
  const ttsQueueRef = useRef<Array<{ id: number; text: string }>>([]);
  const isProcessingQueueRef = useRef<boolean>(false);

  // 새 메시지가 추가되면 자동 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // TTS 큐 처리 함수 (직렬로 하나씩 처리)
  const processTTSQueue = async () => {
    // 이미 처리 중이면 대기
    if (isProcessingQueueRef.current) return;
    
    // 큐가 비어있으면 종료
    if (ttsQueueRef.current.length === 0) {
      setIsLoadingAudio(false);
      return;
    }

    isProcessingQueueRef.current = true;
    setIsLoadingAudio(true);

    // 큐에서 첫 번째 메시지 가져오기
    const messageToProcess = ttsQueueRef.current.shift();
    if (!messageToProcess) {
      isProcessingQueueRef.current = false;
      setIsLoadingAudio(false);
      return;
    }

    try {
      // TTS API 호출
      const audioBlob = await ttsClient.generateTTS({
        text: messageToProcess.text,
        character_id: character.voice,
        language: 'ko',
        speaking_rate: 1.0,
        pitch: 1.0,
        emotion: null,
      });

      // 오디오 URL 생성 및 재생
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      // 재생 완료 후 다음 메시지 처리
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
        const completedMessageId = messageToProcess.id;
        lastProcessedMessageIdRef.current = completedMessageId;
        isProcessingQueueRef.current = false;
        
        // TTS 재생 완료 콜백 호출
        if (onTTSComplete) {
          onTTSComplete(completedMessageId);
        }
        
        // 다음 메시지 처리
        processTTSQueue();
      };

      await audio.play();
    } catch (error) {
      console.error('TTS 생성 실패:', error);
      lastProcessedMessageIdRef.current = messageToProcess.id;
      isProcessingQueueRef.current = false;
      // 에러가 나도 다음 메시지 처리
      processTTSQueue();
    }
  };

  // 새로운 캐릭터 메시지가 추가되면 TTS 큐에 추가
  useEffect(() => {
    if (!isVoiceEnabled || messages.length === 0) return;

    // 처리되지 않은 캐릭터 메시지들을 큐에 추가
    const unprocessedMessages = messages.filter(
      (msg) => msg.type === 'character' && msg.id > lastProcessedMessageIdRef.current
    );

    if (unprocessedMessages.length > 0) {
      // 큐에 추가
      unprocessedMessages.forEach((msg) => {
        // 이미 큐에 있는 메시지는 추가하지 않음
        if (!ttsQueueRef.current.some((q) => q.id === msg.id)) {
          ttsQueueRef.current.push({ id: msg.id, text: msg.text });
        }
      });

      // 큐 처리 시작
      processTTSQueue();
    }
  }, [messages, character.voice, isVoiceEnabled]);

  // 컴포넌트 언마운트 시 오디오 정리
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      ttsQueueRef.current = [];
      isProcessingQueueRef.current = false;
    };
  }, []);

  return (
    <>
      {/* 선택된 캐릭터 정보 */}
      <div className={cn('p-4 border-b-2 border-gray-200', character.bgColor)}>
        <div className="flex items-center gap-3">
          {character.imageUrl ? (
            <img
              src={character.imageUrl}
              alt={character.name}
              width={48}
              height={48}
              className="object-contain"
              style={{ background: 'transparent' }}
            />
          ) : (
            <div className="text-4xl">{character.emoji}</div>
          )}
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
                character.imageUrl ? (
                  <div className="mb-1 flex justify-center">
                    <img
                      src={character.imageUrl}
                      alt={character.name}
                      width={32}
                      height={32}
                      className="object-contain"
                      style={{ background: 'transparent' }}
                    />
                  </div>
                ) : (
                  <div className="text-2xl mb-1">{character.emoji}</div>
                )
              )}
              <div className="text-sm text-gray-900">{msg.text}</div>
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* 입력 필드 */}
      {onSendMessage && (
        <div className="p-4 border-t-2 border-gray-200 bg-gray-50">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (inputText.trim()) {
                // 스토리 오디오 정지
                if ((window as any).stopStoryAudio) {
                  (window as any).stopStoryAudio();
                }
                onSendMessage(inputText.trim());
                setInputText('');
              }
            }}
            className="flex gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="메시지를 입력하세요..."
              className="flex-1 px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
            />
            <button
              type="submit"
              disabled={!inputText.trim()}
              className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              전송
            </button>
          </form>
        </div>
      )}
    </>
  );
}
