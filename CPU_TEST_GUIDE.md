# CPU 테스트 가이드

CPU로 간단히 테스트하는 방법입니다.

## 🚀 빠른 시작

### 1. 백엔드 서버 실행 (CPU 모드)

```bash
cd /home/future/Tallo/service

# CPU로 실행 (GPU 없어도 자동 감지)
python api/tts_api.py
```

**참고**: `tts_api.py`는 GPU가 없으면 자동으로 CPU를 사용합니다.
- `DEFAULT_DEVICE`가 자동으로 CPU를 선택합니다
- 첫 실행 시 모델 다운로드 (~2-3GB)로 시간이 걸릴 수 있습니다

### 2. UI 서버 실행

```bash
cd /home/future/Tallo/UI

# 환경 변수 설정 (없으면 생성)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 개발 서버 실행
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

## 📋 테스트 시나리오

### 시나리오 1: 캐릭터 목록 확인

1. UI에서 캐릭터 목록 조회
2. 백엔드 `/characters` 엔드포인트 호출 확인

**예상 결과**: 
- 캐릭터가 없으면 빈 배열 `[]` 반환
- 캐릭터가 있으면 목록 표시

### 시나리오 2: LLM 채팅 테스트 (텍스트만)

**주의**: OpenAI API 키가 필요합니다!

```bash
# 환경 변수 설정 (백엔드 서버 실행 전)
export OPENAI_API_KEY="your-api-key-here"
```

1. UI에서 LLM 채팅 버튼 클릭
2. 메시지 입력 (예: "안녕하세요")
3. `character_id` 없이 전송

**예상 결과**: 
- LLM 응답 텍스트만 표시
- 오디오 재생 없음

### 시나리오 3: LLM + TTS 통합 테스트

**필수 조건**:
1. OpenAI API 키 설정
2. 캐릭터가 하나 이상 등록되어 있어야 함

**테스트 순서**:

#### 3-1. 캐릭터 생성 (선택)

```bash
# 참조 오디오 파일 준비 (10-30초, wav 형식)
# 예: test_character.wav

# API로 캐릭터 생성
curl -X POST http://localhost:8000/characters/create \
  -F "name=테스트캐릭터" \
  -F "description=테스트용" \
  -F "language=ko" \
  -F "reference_audio=@test_character.wav"
```

응답에서 `id` 값을 복사합니다.

#### 3-2. UI에서 LLM + TTS 테스트

1. 캐릭터 목록에서 생성한 캐릭터 확인
2. LLM 채팅 버튼 클릭
3. 메시지 입력
4. `ttsModel`이 캐릭터 ID로 설정되어 있으면 자동으로 TTS 생성

**예상 결과**:
- LLM 응답 텍스트 표시
- 오디오 자동 재생 (CPU는 느려서 시간이 걸릴 수 있음)

## ⚠️ CPU 성능 참고

CPU 모드에서는 생성 속도가 매우 느립니다:

- **GPU (RTX 4090)**: 짧은 텍스트(1-2문장) → 5-10초
- **CPU**: 짧은 텍스트(1-2문장) → 30초~2분

테스트 시 짧은 텍스트로 시작하세요:
- ✅ 좋은 예: "안녕하세요"
- ✅ 좋은 예: "오늘 날씨가 좋네요"
- ❌ 나쁜 예: 긴 동화책 한 페이지 전체

## 🔍 문제 해결

### 문제 1: "OpenAI 패키지가 설치되지 않았습니다"

```bash
pip install openai
```

### 문제 2: "OpenAI API 키가 설정되지 않았습니다"

```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key"

# Windows
set OPENAI_API_KEY=your-api-key

# 또는 .env 파일 사용 (FastAPI는 자동으로 읽지 않으므로 직접 설정 필요)
```

### 문제 3: "Character not found"

캐릭터를 먼저 생성해야 합니다:
```bash
curl -X POST http://localhost:8000/characters/create \
  -F "name=테스트" \
  -F "language=ko" \
  -F "reference_audio=@your_audio.wav"
```

### 문제 4: UI에서 API 연결 실패

1. 백엔드 서버가 실행 중인지 확인 (`http://localhost:8000/health`)
2. `.env.local` 파일 확인
3. 브라우저 개발자 도구 네트워크 탭에서 오류 확인

### 문제 5: CORS 오류

백엔드의 CORS 설정은 이미 `allow_origins=["*"]`로 설정되어 있어야 합니다.
만약 오류가 나면 `tts_api.py`의 CORS 설정을 확인하세요.

## 📝 간단한 테스트 스크립트

```bash
#!/bin/bash

# 1. 백엔드 서버 상태 확인
echo "=== 백엔드 상태 확인 ==="
curl http://localhost:8000/health

echo -e "\n=== 캐릭터 목록 ==="
curl http://localhost:8000/characters

echo -e "\n=== LLM 테스트 (텍스트만) ==="
curl -X POST http://localhost:8000/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요",
    "return_audio": false
  }'
```

## 🎯 다음 단계

CPU 테스트가 성공하면:

1. GPU 환경에서 실행하여 성능 확인
2. 실제 캐릭터 음성 샘플로 TTS 품질 확인
3. 동화책 생성 기능 테스트
4. 프론트엔드 UI 완성도 향상

## 📚 관련 문서

- `COLAB_SETUP.md`: 코랩에서 실행하기
- `service/README.md`: 서비스 상세 설명
- `UI/README.md`: 프론트엔드 가이드

