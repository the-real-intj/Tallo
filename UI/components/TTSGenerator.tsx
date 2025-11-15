import React, { useState, useEffect } from 'react';
import { ttsClient, Character, TTSRequest } from '../lib/tts-client';

export const TTSGenerator: React.FC = () => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacterId, setSelectedCharacterId] = useState<string>('');
  const [text, setText] = useState('');
  const [language, setLanguage] = useState('en-us');
  const [speakingRate, setSpeakingRate] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [emotion, setEmotion] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [audioURL, setAudioURL] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 캐릭터 목록 로드
  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = async () => {
    try {
      const data = await ttsClient.getCharacters();
      setCharacters(data);
      if (data.length > 0 && !selectedCharacterId) {
        setSelectedCharacterId(data[0].id);
        setLanguage(data[0].language);
      }
    } catch (err) {
      console.error('Failed to load characters:', err);
    }
  };

  const handleCharacterChange = (characterId: string) => {
    setSelectedCharacterId(characterId);
    const character = characters.find((c) => c.id === characterId);
    if (character) {
      setLanguage(character.language);
    }
  };

  const handleGenerate = async () => {
    if (!text.trim()) {
      setError('텍스트를 입력해주세요.');
      return;
    }

    if (!selectedCharacterId) {
      setError('캐릭터를 선택해주세요.');
      return;
    }

    setGenerating(true);
    setError(null);

    // 이전 오디오 URL 정리
    if (audioURL) {
      URL.revokeObjectURL(audioURL);
      setAudioURL(null);
    }

    try {
      const request: TTSRequest = {
        text,
        character_id: selectedCharacterId,
        language,
        speaking_rate: speakingRate,
        pitch,
        emotion: emotion as any,
      };

      const audioBlob = await ttsClient.generateTTS(request);
      const url = ttsClient.createAudioURL(audioBlob);
      setAudioURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'TTS 생성 실패');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!audioURL) return;

    const character = characters.find((c) => c.id === selectedCharacterId);
    const filename = `${character?.name || 'audio'}_${Date.now()}.wav`;

    const a = document.createElement('a');
    a.href = audioURL;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (characters.length === 0) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-600 mb-4">
          먼저 캐릭터를 추가해주세요.
        </p>
        <a
          href="/characters"
          className="text-blue-500 hover:underline"
        >
          캐릭터 관리로 이동 →
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">TTS 생성</h2>

      {/* 캐릭터 선택 */}
      <div>
        <label className="block text-sm font-medium mb-2">
          캐릭터 선택
        </label>
        <select
          value={selectedCharacterId}
          onChange={(e) => handleCharacterChange(e.target.value)}
          className="w-full border rounded px-3 py-2"
        >
          {characters.map((char) => (
            <option key={char.id} value={char.id}>
              {char.name} ({char.language})
            </option>
          ))}
        </select>
      </div>

      {/* 텍스트 입력 */}
      <div>
        <label className="block text-sm font-medium mb-2">
          텍스트 *
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="w-full border rounded px-3 py-2"
          rows={5}
          placeholder="변환할 텍스트를 입력하세요..."
        />
      </div>

      {/* 고급 설정 */}
      <details className="border rounded p-4">
        <summary className="cursor-pointer font-medium">
          고급 설정
        </summary>

        <div className="mt-4 space-y-4">
          {/* 언어 */}
          <div>
            <label className="block text-sm font-medium mb-1">언어</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="en-us">English (US)</option>
              <option value="ja">Japanese</option>
              <option value="zh">Chinese</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </div>

          {/* 말하기 속도 */}
          <div>
            <label className="block text-sm font-medium mb-1">
              말하기 속도: {speakingRate.toFixed(2)}x
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={speakingRate}
              onChange={(e) => setSpeakingRate(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>느리게 (0.5x)</span>
              <span>보통 (1.0x)</span>
              <span>빠르게 (2.0x)</span>
            </div>
          </div>

          {/* 음높이 */}
          <div>
            <label className="block text-sm font-medium mb-1">
              음높이: {pitch.toFixed(2)}
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>낮게 (0.5)</span>
              <span>보통 (1.0)</span>
              <span>높게 (2.0)</span>
            </div>
          </div>

          {/* 감정 */}
          <div>
            <label className="block text-sm font-medium mb-1">감정</label>
            <select
              value={emotion || ''}
              onChange={(e) => setEmotion(e.target.value || null)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">없음</option>
              <option value="happy">행복 (Happy)</option>
              <option value="sad">슬픔 (Sad)</option>
              <option value="angry">화남 (Angry)</option>
              <option value="fear">공포 (Fear)</option>
            </select>
          </div>
        </div>
      </details>

      {/* 오류 메시지 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded">
          {error}
        </div>
      )}

      {/* 생성 버튼 */}
      <div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 font-medium"
        >
          {generating ? '생성 중...' : '🎤 음성 생성'}
        </button>
      </div>

      {/* 오디오 플레이어 */}
      {audioURL && (
        <div className="border rounded-lg p-4 bg-gray-50">
          <h3 className="font-medium mb-3">생성된 오디오</h3>
          <audio
            src={audioURL}
            controls
            autoPlay
            className="w-full mb-3"
          />
          <button
            onClick={handleDownload}
            className="w-full bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            💾 다운로드
          </button>
        </div>
      )}
    </div>
  );
};

export default TTSGenerator;