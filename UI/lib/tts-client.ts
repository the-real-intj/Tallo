// API 베이스 URL (환경 변수 사용)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== 타입 정의 ====================

export interface Character {
  id: string;
  name: string;
  description?: string;
  language: string;
  created_at: string;
  reference_audio?: string;
}

export interface TTSRequest {
  text: string;
  character_id: string;
  language?: string;
  speaking_rate?: number;
  pitch?: number;
  emotion?: 'happy' | 'sad' | 'angry' | 'fear' | null;
}

export interface BatchTTSRequest {
  texts: string[];
  character_id: string;
  language?: string;
}

export interface ServerStatus {
  status: string;
  model: string;
  device: string;
  total_characters: number;
}

export interface HealthCheck {
  status: string;
  model_loaded: boolean;
  device: string;
  characters_count: number;
}

// ==================== API 클라이언트 ====================

class ZonosTTSClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    // URL 끝의 슬래시 제거
    this.baseURL = baseURL.replace(/\/$/, '');
  }

  /**
   * 서버 상태 확인
   */
  async getStatus(): Promise<ServerStatus> {
    const response = await fetch(`${this.baseURL}/`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
    });
    if (!response.ok) throw new Error('Failed to get server status');
    return response.json();
  }

  /**
   * 헬스 체크
   */
  async healthCheck(): Promise<HealthCheck> {
    const response = await fetch(`${this.baseURL}/health`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
    });
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }

  /**
   * 모든 캐릭터 목록 조회
   */
  async getCharacters(): Promise<Character[]> {
    const response = await fetch(`${this.baseURL}/characters`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
    });
    if (!response.ok) throw new Error('Failed to fetch characters');
    return response.json();
  }

  /**
   * 특정 캐릭터 정보 조회
   */
  async getCharacter(characterId: string): Promise<Character> {
    const response = await fetch(`${this.baseURL}/characters/${characterId}`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
    });
    if (!response.ok) throw new Error('Failed to fetch character');
    return response.json();
  }

  /**
   * 새 캐릭터 생성
   */
  async createCharacter(
    name: string,
    referenceAudio: File,
    description?: string,
    language: string = 'en-us'
  ): Promise<Character> {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('reference_audio', referenceAudio);
    if (description) formData.append('description', description);
    formData.append('language', language);

    const response = await fetch(`${this.baseURL}/characters/create`, {
      method: 'POST',
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create character');
    }

    return response.json();
  }

  /**
   * 캐릭터 삭제
   */
  async deleteCharacter(characterId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseURL}/characters/${characterId}`, {
      method: 'DELETE',
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
    });

    if (!response.ok) throw new Error('Failed to delete character');
    return response.json();
  }

  /**
   * TTS 생성
   */
  async generateTTS(request: TTSRequest): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/tts/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate TTS');
    }

    return response.blob();
  }

  /**
   * 배치 TTS 생성
   */
  async generateBatchTTS(request: BatchTTSRequest): Promise<any> {
    const formData = new FormData();
    request.texts.forEach(text => formData.append('texts', text));
    formData.append('character_id', request.character_id);
    if (request.language) formData.append('language', request.language);

    const response = await fetch(`${this.baseURL}/tts/batch`, {
      method: 'POST',
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
      body: formData,
    });

    if (!response.ok) throw new Error('Failed to generate batch TTS');
    return response.json();
  }

  /**
   * 오디오 파일 다운로드
   */
  async downloadOutput(filename: string): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/outputs/${filename}`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
    });
    if (!response.ok) throw new Error('Failed to download file');
    return response.blob();
  }

  /**
   * Blob을 오디오 URL로 변환
   */
  createAudioURL(blob: Blob): string {
    return URL.createObjectURL(blob);
  }

  /**
   * 오디오 다운로드 (파일로 저장)
   */
  downloadAudioFile(blob: Blob, filename: string = 'audio.wav'): void {
    const url = this.createAudioURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// 싱글톤 인스턴스 export
export const ttsClient = new ZonosTTSClient();

export default ZonosTTSClient;