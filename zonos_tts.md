# 🎭 Zonos Multi-Character TTS 완벽 가이드

## 📚 목차
1. [핵심 개념 이해](#핵심-개념-이해)
2. [캐릭터 학습 방법](#캐릭터-학습-방법)
3. [임베딩 파일 관리](#임베딩-파일-관리)
4. [FastAPI 서버 설정](#fastapi-서버-설정)
5. [React UI 연결](#react-ui-연결)
6. [실전 예제](#실전-예제)

---

## 🧠 핵심 개념 이해

### ⚠️ 중요: Zonos는 Fine-tuning이 아닙니다!

```
❌ 잘못된 이해: "각 캐릭터마다 모델을 학습시켜야 한다"
✅ 올바른 이해: "각 캐릭터의 Speaker Embedding만 추출하면 된다"
```

**Zonos 작동 방식:**

1. **사전 학습된 모델** (Zonos-v0.1-transformer 또는 hybrid)
   - 이미 200,000시간의 다국어 음성으로 학습됨
   - 추가 학습 불필요!

2. **Zero-shot Voice Cloning**
   - 10-30초 참조 오디오만 있으면 됨
   - Speaker Embedding 추출 → 저장 → 재사용

3. **워크플로우:**
```
참조 오디오 (10-30초)
    ↓
Speaker Embedding 추출 (.pt 파일)
    ↓
저장 (embeddings/char1.pt)
    ↓
TTS 생성시 로드해서 사용
```

---

## 🎤 캐릭터 학습 방법

### Step 1: 참조 오디오 준비

**요구사항:**
- **길이**: 10-30초 권장 (최소 5초, 최대 60초)
- **품질**: 고음질 (16kHz 이상, 44.1kHz 권장)
- **내용**: 
  - ✅ 깨끗한 음성 (노이즈 최소화)
  - ✅ 다양한 억양/감정 포함
  - ✅ 자연스러운 말투
  - ❌ 배경음악 포함 X
  - ❌ 여러 사람 목소리 X

**예시:**
```bash
reference_audios/
├── character1_voice.wav    # 주인공 (밝고 경쾌한 톤)
├── character2_voice.wav    # 악당 (낮고 위협적인 톤)
├── character3_voice.wav    # 내레이터 (중립적인 톤)
└── character4_voice.wav    # 아이 (높고 귀여운 톤)
```

### Step 2: Speaker Embedding 추출

#### 방법 A: Python 스크립트로 추출

```python
# extract_embedding.py
import torch
import torchaudio
from pathlib import Path
from zonos.model import Zonos
from zonos.utils import DEFAULT_DEVICE as device

# 모델 로드
print("Loading Zonos model...")
model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-transformer", device=device)

def extract_speaker_embedding(audio_path: str, output_path: str):
    """참조 오디오에서 Speaker Embedding 추출"""
    # 오디오 로드
    wav, sampling_rate = torchaudio.load(audio_path)
    print(f"Loaded audio: {audio_path}")
    print(f"  - Duration: {wav.shape[1] / sampling_rate:.2f} seconds")
    print(f"  - Sampling rate: {sampling_rate} Hz")
    
    # Speaker Embedding 추출
    print("Extracting speaker embedding...")
    speaker_embedding = model.make_speaker_embedding(wav, sampling_rate)
    
    # 저장
    torch.save(speaker_embedding, output_path)
    print(f"✅ Saved embedding: {output_path}")
    print(f"  - Shape: {speaker_embedding.shape}")
    print(f"  - Device: {speaker_embedding.device}")

if __name__ == "__main__":
    # 캐릭터별로 임베딩 추출
    characters = [
        ("reference_audios/char1_voice.wav", "embeddings/char1.pt", "주인공"),
        ("reference_audios/char2_voice.wav", "embeddings/char2.pt", "악당"),
        ("reference_audios/char3_voice.wav", "embeddings/char3.pt", "내레이터"),
    ]
    
    for audio_path, embedding_path, name in characters:
        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"{'='*60}")
        
        try:
            extract_speaker_embedding(audio_path, embedding_path)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ All embeddings extracted!")
    print(f"{'='*60}")
```

**실행:**
```bash
cd Tallo
source venv/bin/activate  # 가상환경 활성화
python extract_embedding.py
```

#### 방법 B: FastAPI를 통한 자동 추출

FastAPI 서버가 실행 중이면 자동으로 추출됩니다:

```bash
# 서버 실행
cd api
python tallo_api_server.py

# 새 터미널에서 캐릭터 생성 (자동으로 임베딩 추출)
curl -X POST "http://localhost:8000/characters/create" \
  -F "name=주인공" \
  -F "description=밝고 경쾌한 목소리" \
  -F "language=en-us" \
  -F "reference_audio=@../reference_audios/char1_voice.wav"
```

#### 방법 C: React UI를 통한 생성

1. React 앱 실행
2. "캐릭터 관리" 페이지로 이동
3. "+ 새 캐릭터 추가" 버튼 클릭
4. 정보 입력 및 오디오 파일 업로드
5. 자동으로 임베딩 추출 및 저장!

### Step 3: 임베딩 검증

```python
# verify_embedding.py
import torch
from pathlib import Path

def verify_embedding(embedding_path: str):
    """임베딩 파일 검증"""
    embedding = torch.load(embedding_path)
    
    print(f"Embedding: {embedding_path}")
    print(f"  - Shape: {embedding.shape}")
    print(f"  - Dtype: {embedding.dtype}")
    print(f"  - Device: {embedding.device}")
    print(f"  - Min/Max: {embedding.min():.4f} / {embedding.max():.4f}")
    print(f"  - Mean/Std: {embedding.mean():.4f} / {embedding.std():.4f}")
    
    # 정상 범위 체크
    if embedding.shape[0] == 192:  # Zonos embedding dimension
        print("✅ Valid embedding!")
    else:
        print("❌ Invalid embedding dimension!")

if __name__ == "__main__":
    embeddings_dir = Path("embeddings")
    for pt_file in embeddings_dir.glob("*.pt"):
        if pt_file.name != "characters.json":
            verify_embedding(str(pt_file))
            print()
```

---

## 📦 임베딩 파일 관리

### 디렉토리 구조

```
Tallo/
├── embeddings/                    # 🎯 Speaker Embeddings 저장소
│   ├── char1.pt                   # 캐릭터 1 임베딩
│   ├── char2.pt                   # 캐릭터 2 임베딩
│   ├── char3.pt                   # 캐릭터 3 임베딩
│   ├── ...
│   └── characters.json            # 캐릭터 메타데이터
│
├── reference_audios/              # 원본 참조 오디오
│   ├── char1.wav
│   ├── char2.wav
│   └── char3.wav
│
├── outputs/                       # 생성된 TTS 오디오
│   ├── 주인공_20241112_143022.wav
│   └── 악당_20241112_143045.wav
│
└── cache/                         # 캐시 (선택적)
```

### characters.json 형식

```json
{
  "char1": {
    "id": "char1",
    "name": "주인공",
    "description": "밝고 경쾌한 목소리의 여성 캐릭터",
    "language": "en-us",
    "created_at": "2024-11-12T14:30:22.123456",
    "reference_audio": "reference_audios/char1.wav"
  },
  "char2": {
    "id": "char2",
    "name": "악당",
    "description": "낮고 위협적인 목소리의 남성 캐릭터",
    "language": "en-us",
    "created_at": "2024-11-12T14:31:15.654321",
    "reference_audio": "reference_audios/char2.wav"
  }
}
```

### 임베딩 파일 특징

1. **파일 크기**: 약 3-5KB (매우 작음!)
2. **형식**: PyTorch .pt 파일
3. **내용**: 192차원 벡터 (Zonos 기본)
4. **재사용**: 무한 재사용 가능
5. **버전**: 모델 버전과 호환

### 백업 및 관리

```bash
# 임베딩 백업
tar -czf embeddings_backup_$(date +%Y%m%d).tar.gz embeddings/

# 임베딩 복원
tar -xzf embeddings_backup_20241112.tar.gz

# 임베딩 목록 확인
ls -lh embeddings/*.pt

# 특정 캐릭터 삭제
rm embeddings/char3.pt
# characters.json에서도 제거 필요!
```

---

## 🚀 FastAPI 서버 설정

### 1. 서버 파일 배치

```bash
Tallo/
├── api/
│   └── tallo_api_server.py    # ← FastAPI 서버
├── embeddings/                 # 임베딩 자동 관리
├── reference_audios/           # 참조 오디오 자동 관리
├── outputs/                    # 출력 자동 관리
└── Zonos/                      # Zonos 라이브러리
```

### 2. 서버 실행

```bash
# 가상환경 활성화
cd Tallo
source venv/bin/activate

# 서버 실행
cd api
python tallo_api_server.py

# 또는 개발 모드 (자동 재시작)
uvicorn tallo_api_server:app --reload --host 0.0.0.0 --port 8000
```

### 3. API 테스트

```bash
# 서버 상태 확인
curl http://localhost:8000/

# 헬스 체크
curl http://localhost:8000/health

# 캐릭터 목록 조회
curl http://localhost:8000/characters

# 캐릭터 생성
curl -X POST "http://localhost:8000/characters/create" \
  -F "name=테스트 캐릭터" \
  -F "language=en-us" \
  -F "reference_audio=@../reference_audios/test.wav"

# TTS 생성
curl -X POST "http://localhost:8000/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "character_id": "char1",
    "language": "en-us"
  }' \
  --output test.wav
```

---

## 🎨 React UI 연결

### 1. 파일 배치

```bash
Tallo/
└── UI/
    ├── lib/
    │   └── tts-client.ts           # ← API 클라이언트
    ├── components/
    │   ├── CharacterManager.tsx    # ← 캐릭터 관리
    │   └── TTSGenerator.tsx        # ← TTS 생성
    └── app/
        └── page.tsx                # 메인 페이지
```

### 2. API 클라이언트 설정

```typescript
// Tallo/UI/lib/tts-client.ts
const API_BASE_URL = 'http://localhost:8000';  // FastAPI 서버 주소

export const ttsClient = new ZonosTTSClient(API_BASE_URL);
```

### 3. 메인 페이지 통합

```typescript
// Tallo/UI/app/page.tsx
import { CharacterManager } from '@/components/CharacterManager';
import { TTSGenerator } from '@/components/TTSGenerator';

export default function Home() {
  const [activeTab, setActiveTab] = useState('tts');

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Zonos TTS Studio</h1>
      
      {/* 탭 네비게이션 */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('tts')}
          className={`px-4 py-2 rounded ${
            activeTab === 'tts' ? 'bg-blue-500 text-white' : 'bg-gray-200'
          }`}
        >
          TTS 생성
        </button>
        <button
          onClick={() => setActiveTab('characters')}
          className={`px-4 py-2 rounded ${
            activeTab === 'characters' ? 'bg-blue-500 text-white' : 'bg-gray-200'
          }`}
        >
          캐릭터 관리
        </button>
      </div>

      {/* 컨텐츠 */}
      {activeTab === 'tts' && <TTSGenerator />}
      {activeTab === 'characters' && <CharacterManager />}
    </div>
  );
}
```

### 4. React 앱 실행

```bash
# UI 디렉토리로 이동
cd Tallo/UI

# 패키지 설치 (최초 1회)
npm install

# 개발 서버 실행
npm run dev

# 브라우저에서 접속
# http://localhost:3000
```

---

## 🎬 실전 예제

### 시나리오: 3개 캐릭터로 대화 생성

#### 1. 캐릭터 준비

```bash
# 참조 오디오 준비
reference_audios/
├── hero.wav         # 주인공 (밝은 목소리, 20초)
├── villain.wav      # 악당 (낮은 목소리, 25초)
└── narrator.wav     # 내레이터 (중립적, 15초)
```

#### 2. 캐릭터 등록 (React UI 사용)

1. "캐릭터 관리" 탭 클릭
2. "+ 새 캐릭터 추가" 클릭
3. 각 캐릭터 정보 입력:
   - 이름: "주인공", "악당", "내레이터"
   - 참조 오디오 업로드
   - 언어: "en-us"

#### 3. 대화 생성 (Python 스크립트)

```python
# generate_dialogue.py
import requests
from pathlib import Path

API_URL = "http://localhost:8000"

def generate_line(character_id: str, text: str, emotion: str = None):
    """대사 한 줄 생성"""
    response = requests.post(f"{API_URL}/tts/generate", json={
        "text": text,
        "character_id": character_id,
        "language": "en-us",
        "emotion": emotion
    })
    
    if response.ok:
        filename = f"outputs/{character_id}_{len(text[:20])}.wav"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ Generated: {filename}")
        return filename
    else:
        print(f"❌ Failed: {response.text}")
        return None

# 대화 시나리오
dialogue = [
    ("narrator", "In a dark castle, the hero confronts the villain.", None),
    ("hero", "Your reign of terror ends today!", "angry"),
    ("villain", "Fool! You cannot defeat me!", "angry"),
    ("hero", "We'll see about that!", "happy"),
    ("narrator", "And so, the epic battle began.", None),
]

print("🎬 Generating dialogue...")
for character, text, emotion in dialogue:
    print(f"\n[{character.upper()}]: {text}")
    generate_line(character, text, emotion)

print("\n✅ All dialogue generated!")
```

#### 4. 배치 생성 (FastAPI 사용)

```python
# batch_generate.py
import requests

API_URL = "http://localhost:8000"

# 여러 대사를 한 번에 생성
texts = [
    "Hello, how are you?",
    "I'm fine, thank you!",
    "Let's go on an adventure!",
]

response = requests.post(f"{API_URL}/tts/batch", data={
    "character_id": "hero",
    "language": "en-us",
    "texts": texts
})

results = response.json()
for result in results["results"]:
    print(f"[{result['index']}] {result['text']}")
    print(f"    File: {result.get('file', 'N/A')}")
```

---

## 🔧 고급 기능

### 1. 감정 제어

```python
# 감정별 TTS 생성
emotions = ["happy", "sad", "angry", "fear"]

for emotion in emotions:
    response = requests.post(f"{API_URL}/tts/generate", json={
        "text": "This is a test.",
        "character_id": "hero",
        "emotion": emotion
    })
    # 저장...
```

### 2. 말하기 속도/음높이 조절

```python
# 다양한 설정으로 생성
configs = [
    {"speaking_rate": 0.8, "pitch": 0.9},  # 느리고 낮은 목소리
    {"speaking_rate": 1.0, "pitch": 1.0},  # 보통
    {"speaking_rate": 1.5, "pitch": 1.2},  # 빠르고 높은 목소리
]

for config in configs:
    response = requests.post(f"{API_URL}/tts/generate", json={
        "text": "Testing different configurations.",
        "character_id": "hero",
        **config
    })
    # 저장...
```

### 3. 다국어 지원

```python
# 여러 언어로 생성
languages = [
    ("en-us", "Hello world!"),
    ("ja", "こんにちは世界！"),
    ("zh", "你好世界！"),
    ("fr", "Bonjour le monde!"),
    ("de", "Hallo Welt!"),
]

for lang, text in languages:
    response = requests.post(f"{API_URL}/tts/generate", json={
        "text": text,
        "character_id": "multilingual_char",
        "language": lang
    })
    # 저장...
```

---

## 📊 성능 최적화

### GPU 메모리 관리

```python
# tallo_api_server.py에서
import torch

# GPU 메모리 부족시
device = "cpu"  # CPU 사용

# 또는 특정 GPU 선택
device = "cuda:1"  # 두 번째 GPU 사용

# 메모리 정리
torch.cuda.empty_cache()
```

### 캐싱 시스템

```python
# 캐시 활용 (고급)
from functools import lru_cache

@lru_cache(maxsize=100)
def load_cached_embedding(character_id: str):
    """임베딩 캐싱으로 로드 속도 향상"""
    return load_character_embedding(character_id)
```

---

## ✅ 체크리스트

### 초기 설정
- [ ] Zonos 설치 완료
- [ ] FastAPI 서버 실행 성공
- [ ] React UI 실행 성공
- [ ] 서버-UI 통신 확인

### 캐릭터 관리
- [ ] 참조 오디오 준비 (10-30초)
- [ ] 캐릭터 생성 성공
- [ ] embeddings/ 폴더에 .pt 파일 생성 확인
- [ ] characters.json 업데이트 확인

### TTS 생성
- [ ] 기본 TTS 생성 성공
- [ ] 감정 제어 테스트
- [ ] 말하기 속도/음높이 조절 테스트
- [ ] 다국어 생성 테스트

### 프로덕션
- [ ] 임베딩 백업
- [ ] 로그 설정
- [ ] 에러 핸들링 확인
- [ ] 성능 모니터링

---

## 🆘 문제 해결

### Q1: 임베딩 파일이 생성되지 않음
```bash
# 권한 확인
ls -la embeddings/

# 디렉토리 생성 확인
mkdir -p embeddings reference_audios outputs

# 서버 로그 확인
python tallo_api_server.py
```

### Q2: React와 FastAPI 통신 안됨
```typescript
// CORS 오류 → FastAPI에서 CORS 설정 확인
// tallo_api_server.py에서:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  // React 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Q3: GPU 메모리 부족
```python
# CPU 사용으로 전환
device = "cpu"

# 또는 배치 크기 줄이기
# 또는 Transformer 모델 사용 (Hybrid보다 가벼움)
```

---

이제 완벽한 Multi-Character TTS 시스템이 준비되었습니다! 🎉