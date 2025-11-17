'use client';

import { useState } from 'react';
import { synthesizeTTS } from '@/lib/api';

interface StoryTTSButtonProps {
  text: string;
  characterName?: string;
  ttsModel?: string; // TTS 모델 이름 (예: 'Ana_20sec')
  autoEmotion?: boolean;
  audioUrl?: string; // 미리 생성된 오디오 파일 URL (있으면 이걸 우선 사용)
}

/**
 * 동화 텍스트를 TTS로 읽어주는 버튼 컴포넌트
 */
export function StoryTTSButton({ 
  text, 
  characterName = '아나',
  ttsModel,
  autoEmotion = true,
  audioUrl
}: StoryTTSButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

  const handlePlayTTS = async () => {
    try {
      // 이미 재생 중이면 정지
      if (isPlaying && audio) {
        audio.pause();
        audio.currentTime = 0;
        setIsPlaying(false);
        return;
      }

      // 미리 생성된 오디오 파일이 있으면 바로 재생
      if (audioUrl) {
        // 한글 파일명을 URL 인코딩
        const encodedUrl = encodeURI(audioUrl);
        console.log('오디오 파일 재생 시도:', audioUrl, '-> 인코딩:', encodedUrl);
        const newAudio = new Audio(encodedUrl);
        
        newAudio.onended = () => {
          setIsPlaying(false);
        };

        newAudio.onerror = (e) => {
          console.error('오디오 재생 에러:', e, 'URL:', audioUrl);
          setIsPlaying(false);
          alert(`오디오 재생 중 오류가 발생했습니다. 파일을 찾을 수 없습니다: ${audioUrl}`);
        };

        newAudio.onloadstart = () => {
          console.log('오디오 로딩 시작');
        };

        newAudio.oncanplay = () => {
          console.log('오디오 재생 가능');
        };

        try {
          await newAudio.play();
          setAudio(newAudio);
          setIsPlaying(true);
          console.log('오디오 재생 성공');
        } catch (playError) {
          console.error('재생 에러:', playError);
          alert('오디오 재생에 실패했습니다. 브라우저 콘솔을 확인해주세요.');
          setIsPlaying(false);
        }
        return;
      }

      // 미리 생성된 파일이 없으면 TTS API 호출
      setIsLoading(true);

      // ttsModel이 있으면 speaker_wav로 변환 (예: 'Ana_20sec' -> 'Ana_20sec.wav')
      const speakerWav = ttsModel ? `${ttsModel}.wav` : undefined;
      
      const audioBlob = await synthesizeTTS({
        text,
        language: 'ko',
        auto_emotion: autoEmotion,
        as_file: true,
        speaker_wav: speakerWav,
      });

      // 오디오 재생
      const blobUrl = URL.createObjectURL(audioBlob);
      const newAudio = new Audio(blobUrl);
      
      newAudio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(blobUrl);
      };

      newAudio.onerror = () => {
        setIsPlaying(false);
        setIsLoading(false);
        alert('오디오 재생 중 오류가 발생했습니다.');
      };

      await newAudio.play();
      setAudio(newAudio);
      setIsPlaying(true);
      setIsLoading(false);
    } catch (error) {
      console.error('TTS 에러:', error);
      setIsLoading(false);
      alert('음성 합성 중 오류가 발생했습니다. 서버가 실행 중인지 확인해주세요.');
    }
  };

  return (
    <button
      onClick={handlePlayTTS}
      disabled={isLoading}
      className={`
        px-4 py-2 rounded-lg font-medium transition-all
        ${isPlaying 
          ? 'bg-red-500 hover:bg-red-600 text-white' 
          : 'bg-purple-500 hover:bg-purple-600 text-white'
        }
        ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}
        flex items-center gap-2
      `}
    >
      {isLoading ? (
        <>
          <span className="animate-spin">⏳</span>
          <span>음성 생성 중...</span>
        </>
      ) : isPlaying ? (
        <>
          <span>⏸️</span>
          <span>정지</span>
        </>
      ) : (
        <>
          <span>🎤</span>
          <span>{characterName} 목소리로 듣기</span>
        </>
      )}
    </button>
  );
}


