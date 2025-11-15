import React, { useState, useEffect } from 'react';
import { ttsClient, Character } from '../lib/tts-client';

export const CharacterManager: React.FC = () => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 캐릭터 목록 로드
  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ttsClient.getCharacters();
      setCharacters(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load characters');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCharacter = async (characterId: string) => {
    if (!confirm('정말 이 캐릭터를 삭제하시겠습니까?')) return;

    try {
      await ttsClient.deleteCharacter(characterId);
      await loadCharacters();
    } catch (err) {
      alert('캐릭터 삭제 실패: ' + (err instanceof Error ? err.message : ''));
    }
  };

  if (loading) {
    return <div className="text-center p-8">로딩 중...</div>;
  }

  if (error) {
    return (
      <div className="text-red-500 p-4 border border-red-300 rounded">
        오류: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">캐릭터 관리</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          + 새 캐릭터 추가
        </button>
      </div>

      {/* 캐릭터 목록 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {characters.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-8">
            등록된 캐릭터가 없습니다. 새 캐릭터를 추가해주세요.
          </div>
        ) : (
          characters.map((character) => (
            <CharacterCard
              key={character.id}
              character={character}
              onDelete={() => handleDeleteCharacter(character.id)}
            />
          ))
        )}
      </div>

      {/* 캐릭터 생성 모달 */}
      {showCreateModal && (
        <CreateCharacterModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadCharacters();
          }}
        />
      )}
    </div>
  );
};

// ==================== 캐릭터 카드 ====================

interface CharacterCardProps {
  character: Character;
  onDelete: () => void;
}

const CharacterCard: React.FC<CharacterCardProps> = ({ character, onDelete }) => {
  return (
    <div className="border rounded-lg p-4 shadow hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold">{character.name}</h3>
        <button
          onClick={onDelete}
          className="text-red-500 hover:text-red-700"
          title="삭제"
        >
          🗑️
        </button>
      </div>

      {character.description && (
        <p className="text-sm text-gray-600 mb-2">{character.description}</p>
      )}

      <div className="text-xs text-gray-500 space-y-1">
        <div>언어: {character.language}</div>
        <div>생성일: {new Date(character.created_at).toLocaleDateString()}</div>
      </div>

      {character.reference_audio && (
        <div className="mt-3">
          <audio
            src={`http://localhost:8000/${character.reference_audio}`}
            controls
            className="w-full"
          />
        </div>
      )}
    </div>
  );
};

// ==================== 캐릭터 생성 모달 ====================

interface CreateCharacterModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const CreateCharacterModal: React.FC<CreateCharacterModalProps> = ({
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('en-us');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError('캐릭터 이름을 입력해주세요.');
      return;
    }

    if (!audioFile) {
      setError('참조 오디오 파일을 선택해주세요.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await ttsClient.createCharacter(name, audioFile, description, language);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : '캐릭터 생성 실패');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-xl font-bold mb-4">새 캐릭터 추가</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 이름 */}
          <div>
            <label className="block text-sm font-medium mb-1">
              캐릭터 이름 *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="예: 주인공, 악당, 내레이터"
            />
          </div>

          {/* 설명 */}
          <div>
            <label className="block text-sm font-medium mb-1">설명</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full border rounded px-3 py-2"
              rows={3}
              placeholder="캐릭터에 대한 설명을 입력하세요"
            />
          </div>

          {/* 언어 */}
          <div>
            <label className="block text-sm font-medium mb-1">언어 *</label>
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

          {/* 오디오 파일 */}
          <div>
            <label className="block text-sm font-medium mb-1">
              참조 오디오 * (10-30초 권장)
            </label>
            <input
              type="file"
              accept="audio/*"
              onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
              className="w-full border rounded px-3 py-2"
            />
            {audioFile && (
              <p className="text-xs text-gray-500 mt-1">
                선택된 파일: {audioFile.name}
              </p>
            )}
          </div>

          {error && (
            <div className="text-red-500 text-sm bg-red-50 p-2 rounded">
              {error}
            </div>
          )}

          {/* 버튼 */}
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={uploading}
              className="flex-1 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
            >
              {uploading ? '생성 중...' : '생성'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400 disabled:bg-gray-200"
            >
              취소
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CharacterManager;