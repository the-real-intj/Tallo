# 🎤 Tallo 음성 시스템 가이드

## 📌 시스템 개요

사용자가 **음성 ON** 버튼을 누르면:
1. 동화책 전체 페이지(5페이지)를 **한 번에 미리 TTS 생성**
2. 생성된 오디오를 캐시에 저장 (`cache/heartsping/page_1.wav ~ page_5.wav`)
3. 페이지 넘길 때마다 **즉시 재생** (대기 시간 0초!)

---

## 🏗️ 아키텍처

```
[프론트엔드]                    [백엔드 API]                  [Zonos TTS]
    |                               |                             |
    | 1. 음성 ON 클릭                |                             |
    |----------------------------->|                             |
    |  POST /stories/pregenerate   |                             |
    |  {character_id, pages[]}     |                             |
    |                              | 2. 임베딩 로드               |
    |                              |    heartsping.pt            |
    |                              |                             |
    |                              | 3. 각 페이지 TTS 생성        |
    |                              |---------------------------->|
    |                              |    make_cond_dict()         |
    |                              |    model.generate()         |
    |                              |    autoencoder.decode()     |
    |                              |<----------------------------|
    |                              |                             |
    |                              | 4. WAV 파일 저장             |
    |                              |    cache/heartsping/        |
    |<-----------------------------|    page_X.wav               |
    |  {pages: [{audio_url}]}      |                             |
    |                              |                             |
    | 5. 페이지 넘김                 |                             |
    |                              |                             |
    | 6. GET /cache/.../page_X.wav |                             |
    |----------------------------->|                             |
    |<-----------------------------|                             |
    |  [WAV 오디오 스트림]            |                             |
    |                              |                             |
    | 7. Audio 객체로 즉시 재생       |                             |
```

---

## 📁 파일 구조

```
Tallo/
├── api/
│   └── tallo_api_server.py        # FastAPI 서버 (새 엔드포인트 추가됨)
│
├── embeddings/
│   ├── heartsping.pt              # 캐릭터 음성 임베딩 (재사용)
│   └── characters.json            # 캐릭터 메타데이터
│
├── cache/                         # 미리 생성된 오디오 캐시
│   └── heartsping/
│       ├── page_1.wav
│       ├── page_2.wav
│       ├── page_3.wav
│       ├── page_4.wav
│       └── page_5.wav
│
└── UI/
    ├── lib/
    │   └── api.ts                 # API 클라이언트 (새 함수 추가)
    │
    ├── components/
    │   └── StoryBookPanel.tsx     # 동화책 컴포넌트 (미리 생성 로직)
    │
    ├── app/
    │   └── page.tsx               # 메인 페이지
    │
    └── data/
        └── storyPages.ts          # 동화 더미 데이터
```

---

## 🚀 사용 방법

### 1️⃣ 서버 시작

```powershell
# PowerShell에서 실행
cd C:\Users\dell\Tallo

# venv 활성화
.\.venv\Scripts\Activate.ps1

# espeak-ng 환경 변수 설정
$env:PHONEMIZER_ESPEAK_PATH = "C:\Program Files\eSpeak NG\espeak-ng.exe"
$env:PHONEMIZER_ESPEAK_LIBRARY = "C:\Program Files\eSpeak NG\libespeak-ng.dll"

# API 서버 시작
cd api
python tallo_api_server.py
```

**출력:**
```
============================================================
🚀 Zonos Multi-Character TTS API Server Starting...
============================================================

📦 Loading Zonos model...
✅ Model loaded successfully on cpu

📚 Loading characters database...
✅ Loaded 1 characters

============================================================
✨ Server is ready!
📖 API Documentation: http://localhost:8000/docs
============================================================

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2️⃣ 프론트엔드 시작

```powershell
# 새 PowerShell 창
cd C:\Users\dell\Tallo\UI
npm run dev
```

**브라우저:** http://localhost:3000

### 3️⃣ 사용 흐름

1. **캐릭터 선택**: "하트스핑" 선택
2. **이야기 시작**: "🎬 이야기 시작하기" 버튼 클릭
3. **음성 ON**: "🔊 음성 ON" 버튼 클릭
   - 🎤 **자동으로 전체 동화 미리 생성 시작** (2분 소요)
   - ⏳ "동화 음성 준비 중..." 로딩 화면 표시
4. **생성 완료 후**: 페이지 넘기면 **즉시 재생!** ✨

---

## 🎯 API 엔드포인트

### 🆕 새로 추가된 엔드포인트

#### 1. **동화 전체 미리 생성**
```http
POST /stories/pregenerate
Content-Type: application/json

{
  "character_id": "heartsping",
  "pages": [
    {"page": 1, "text": "옛날 옛적, 푸른 바다 너머..."},
    {"page": 2, "text": "어느 날 하늘에서..."},
    {"page": 3, "text": "깊은 숲 속으로..."},
    {"page": 4, "text": "바닷가에서..."},
    {"page": 5, "text": "그리고 친구와 함께..."}
  ]
}
```

**응답:**
```json
{
  "character_id": "heartsping",
  "total_pages": 5,
  "pages": [
    {
      "page": 1,
      "text": "옛날 옛적, 푸른 바다 너머...",
      "audio_url": "/cache/heartsping/page_1.wav"
    },
    ...
  ]
}
```

#### 2. **캐시된 오디오 다운로드**
```http
GET /cache/{character_id}/page_{page_num}.wav
```

**예시:**
```bash
curl http://localhost:8000/cache/heartsping/page_1.wav --output page1.wav
```

#### 3. **오디오 맵 조회**
```http
GET /stories/audio/{character_id}
```

**응답:**
```json
{
  "character_id": "heartsping",
  "pages": {
    "1": "/cache/heartsping/page_1.wav",
    "2": "/cache/heartsping/page_2.wav",
    ...
  }
}
```

---

## 🧪 테스트 방법

### A. cURL로 테스트

```bash
# 1. 동화 미리 생성
curl -X POST http://localhost:8000/stories/pregenerate \
  -H "Content-Type: application/json" \
  -d '{
    "character_id": "heartsping",
    "pages": [
      {"page": 1, "text": "안녕하세요, 저는 하트스핑이에요!"}
    ]
  }'

# 2. 생성된 오디오 다운로드
curl http://localhost:8000/cache/heartsping/page_1.wav --output test.wav

# 3. 오디오 재생 (Windows)
start test.wav
```

### B. Swagger UI로 테스트

1. 브라우저: http://localhost:8000/docs
2. `POST /stories/pregenerate` 클릭
3. "Try it out" → JSON 입력 → "Execute"
4. 응답에서 `audio_url` 확인
5. 브라우저에서 오디오 URL 열기 (자동 다운로드)

---

## ⚡ 성능 비교

### 기존 방식 (실시간 생성)
```
페이지 넘김
  ↓ ⏱️ 30초 대기 (매번!)
TTS 생성
  ↓
오디오 재생
```

### 새 방식 (미리 생성)
```
음성 ON 버튼 클릭
  ↓ ⏱️ 2분 대기 (최초 1회만)
전체 페이지 미리 생성
  ↓
페이지 넘김 → ⚡ 즉시 재생 (0.1초)
```

**장점:**
- ✅ 페이지 전환 즉시 재생 (사용자 경험 향상)
- ✅ 한 번 생성하면 캐시에 저장 → 재사용
- ✅ 서버 부하 분산 (시작 시 한 번만 생성)
- ✅ 네트워크 효율적 (작은 WAV 파일만 전송)

---

## 🎤 기존 음성 파일 사용하기

### 방법 1: `.pt` 임베딩 파일 직접 추가

1. `embeddings/` 폴더에 `.pt` 파일 복사
   ```
   embeddings/
     my_character.pt
   ```

2. `embeddings/characters.json` 수정
   ```json
   {
     "my_character": {
       "id": "my_character",
       "name": "내 캐릭터",
       "language": "ko",
       "created_at": "2025-11-13T10:00:00",
       "reference_audio": "audios/my_character.wav"
     }
   }
   ```

3. API 호출
   ```bash
   curl -X POST http://localhost:8000/stories/pregenerate \
     -H "Content-Type: application/json" \
     -d '{
       "character_id": "my_character",
       "pages": [{"page": 1, "text": "테스트 음성입니다."}]
     }'
   ```

### 방법 2: WAV/MP3 파일로 새 캐릭터 생성

```bash
curl -X POST http://localhost:8000/characters/create \
  -F "name=새캐릭터" \
  -F "language=ko" \
  -F "reference_audio=@my_voice.wav"
```

**응답:**
```json
{
  "id": "abc123def456",
  "name": "새캐릭터",
  "language": "ko",
  "created_at": "2025-11-13T12:00:00"
}
```

---

## 🔧 트러블슈팅

### 문제 1: `ModuleNotFoundError: No module named 'zonos'`
**해결:**
```powershell
# venv 활성화 후 실행
.\.venv\Scripts\Activate.ps1
cd api
python tallo_api_server.py
```

### 문제 2: `espeak not installed`
**해결:**
```powershell
# 환경 변수 설정
$env:PHONEMIZER_ESPEAK_PATH = "C:\Program Files\eSpeak NG\espeak-ng.exe"
$env:PHONEMIZER_ESPEAK_LIBRARY = "C:\Program Files\eSpeak NG\libespeak-ng.dll"
```

### 문제 3: 포트 8000 이미 사용 중
**해결:**
```powershell
# 8000 포트 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료
taskkill /PID <PID번호> /F
```

### 문제 4: 음성 생성이 느림 (CPU)
**해결:**
- GPU가 있다면 `device="cuda"` 사용 (5~10배 빠름)
- 또는 미리 생성 방식 사용 (이미 적용됨!)

---

## 📊 프론트엔드 변경 사항

### `UI/lib/api.ts`
- ✅ `pregenerateStoryAudio()` 추가
- ✅ `getStoryAudioMap()` 추가
- ✅ `getCachedAudioUrl()` 추가

### `UI/components/StoryBookPanel.tsx`
- ✅ 음성 ON 시 전체 페이지 미리 생성
- ✅ 로딩 UI 추가 ("동화 음성 준비 중...")
- ✅ 페이지 전환 시 캐시된 오디오 즉시 재생
- ✅ 더 이상 `tts-client.ts` 사용 안 함 (실시간 생성 X)

### `UI/app/page.tsx`
- ✅ `storyPages` prop 전달

---

## 🎉 완성!

이제 음성 시스템이 완전히 작동합니다:

1. ✅ **빠른 재생**: 페이지 넘길 때 즉시 음성 재생
2. ✅ **캐싱**: 한 번 생성하면 재사용
3. ✅ **유연성**: 기존 `.pt` 파일 활용 가능
4. ✅ **사용자 경험**: 로딩 상태 표시

**다음 단계:**
- 3D 모델 통합 (Three.js, React Three Fiber)
- LLM 챗봇 연동 (실시간 대화)
- 감정 분석 & 표정 애니메이션
- 부모 승인 시스템

---

## 📞 문의

문제가 발생하면:
1. 서버 로그 확인 (`api/tallo_api_server.py` 콘솔)
2. 브라우저 개발자 도구 (F12) 확인
3. Swagger UI 테스트: http://localhost:8000/docs
