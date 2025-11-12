'use client';

import { Choice } from '@/types';

interface ChoiceButtonsProps {
  choices: Choice[];
  onChoice: (choice: Choice) => void;
}

/**
 * 선택지 버튼 컴포넌트
 * 동화 중간에 사용자가 선택할 수 있는 옵션들 표시
 */
export function ChoiceButtons({ choices, onChoice }: ChoiceButtonsProps) {
  return (
    <div className="space-y-2 pt-2 animate-slide-in">
      {choices.map((choice, idx) => (
        <button
          key={idx}
          onClick={() => onChoice(choice)}
          className="choice-button w-full p-3 bg-white border-2 border-purple-300 rounded-xl text-gray-800 font-medium hover:bg-purple-50 hover:shadow-md transition-all"
        >
          {choice.text}
        </button>
      ))}
    </div>
  );
}
