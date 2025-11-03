'use client';

import { useEffect, useRef } from 'react';
import { Character, Message } from '@/types';
import { cn } from '@/lib/utils';

interface ChatPanelProps {
  character: Character;
  messages: Message[];
  onClose: () => void;
}

/**
 * 채팅 패널 컴포넌트
 * 캐릭터와의 대화를 표시
 */
export function ChatPanel({ character, messages, onClose }: ChatPanelProps) {
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 추가되면 자동 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <>
      {/* 선택된 캐릭터 정보 */}
      <div className={cn('p-4 border-b-2 border-gray-200', character.bgColor)}>
        <div className="flex items-center gap-3">
          <div className="text-4xl">{character.emoji}</div>
          <div className="flex-1">
            <div className="font-bold text-gray-800">{character.name}</div>
            <div className="text-xs text-gray-600">{character.voice}</div>
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
                  : `bg-gradient-to-r ${character.color} text-white`
              )}
            >
              {msg.type === 'character' && (
                <div className="text-2xl mb-1">{character.emoji}</div>
              )}
              <div className="text-sm">{msg.text}</div>
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
    </>
  );
}
