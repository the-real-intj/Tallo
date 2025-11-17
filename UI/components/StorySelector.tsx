'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchStories } from '@/lib/api';

interface Story {
  id: string;
  title: string;
  text: string;
  audio_url?: string;
  character_id?: string;
}

interface StorySelectorProps {
  onSelect: (story: Story) => void;
}

/**
 * 스토리 선택 컴포넌트
 * MongoDB에서 동화 목록을 가져와서 선택할 수 있게 함
 */
export function StorySelector({ onSelect }: StorySelectorProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stories'],
    queryFn: () => fetchStories(5), // 최대 5개
    retry: false,
    staleTime: 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const stories: Story[] = data?.stories || [];

  // 로딩 중
  if (isLoading) {
    return (
      <div className="p-6 flex-1 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <div className="text-gray-600">동화를 불러오는 중...</div>
        </div>
      </div>
    );
  }

  // 에러 또는 스토리가 없을 때
  if (error || stories.length === 0) {
    return (
      <div className="p-6 flex-1 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">📚</div>
          <div className="text-gray-600 mb-2">
            {error ? '동화를 불러올 수 없습니다.' : '등록된 동화가 없습니다.'}
          </div>
          {error && (
            <div className="text-sm text-gray-500 mt-2">
              {error instanceof Error ? error.message : '알 수 없는 오류'}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 flex-1 overflow-auto">
      <h2 className="text-lg font-bold mb-4 text-gray-800">
        동화를 선택해주세요!
      </h2>

      <div className="space-y-3">
        {stories.map((story) => (
          <button
            key={story.id}
            onClick={() => onSelect(story)}
            className="w-full p-4 bg-white border-2 border-gray-200 rounded-xl hover:border-purple-400 hover:shadow-md transition-all text-left"
          >
            <div className="flex items-start gap-3">
              <div className="text-3xl">📖</div>
              <div className="flex-1">
                <div className="font-bold text-gray-800 mb-1">
                  {story.title}
                </div>
                <div className="text-sm text-gray-600 line-clamp-2">
                  {story.text.substring(0, 100)}
                  {story.text.length > 100 ? '...' : ''}
                </div>
                {story.audio_url && (
                  <div className="mt-2 text-xs text-purple-600">
                    🎵 오디오 준비됨
                  </div>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

