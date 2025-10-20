# 🚀 퉁퉁이 AI 캐릭터 만들기 - 실행 가이드

**처음부터 끝까지 따라하는 완벽 가이드**

---

## 📋 전체 흐름 (한눈에 보기)

```
┌─────────────────────────────────────────────┐
│ Phase 1: 준비 단계 (10분)                   │
│  - 환경 설정                                │
│  - API 키 발급                              │
│  - 유튜브 URL 찾기                          │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Phase 2: 음성 학습 (1-12시간)               │
│  - 유튜브 다운로드                          │
│  - 배경음 제거                              │
│  - 전처리                                   │
│  - 모델 학습                                │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Phase 3: 대화 시스템 (10분)                 │
│  - 챗봇 테스트                              │
│  - 음성 대화 테스트                         │
│  - 완성!                                    │
└─────────────────────────────────────────────┘
```

---

## 🎯 Phase 1: 준비 단계 (필수!)

### ✅ Step 1-1: Python 환경 확인 (2분)

```bash
# 현재 디렉토리 확인
cd d:\2025\Tallo\voice-training-pipeline

# Python 버전 확인 (3.9 이상 필요)
python --version
```

**예상 출력:**
```
Python 3.10.x
```

---

### ✅ Step 1-2: 가상환경 생성 및 활성화 (3분)

```bash
# 가상환경 생성 (처음 한 번만)
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

**성공하면:**
```
(venv) D:\2025\Tallo\voice-training-pipeline>
```

---

### ✅ Step 1-3: 기본 패키지 설치 (5분)

```bash
# pip 업그레이드
pip install --upgrade pip

# 필수 패키지만 먼저
pip install python-dotenv pyyaml google-generativeai
```

---

### ✅ Step 1-4: Gemini API 키 발급 (3분)

1. **https://aistudio.google.com/app/apikey** 접속
2. "Create API Key" 클릭
3. API 키 복사

4. `.env` 파일 열어서 수정:
```bash
GEMINI_API_KEY=복사한_API_키_여기에_붙여넣기
```

---

### ✅ Step 1-5: 유튜브 URL 찾기 (5분)

1. 유튜브 검색: **"뽀로로 퉁퉁이 모음"**
2. 영상 5-10개 선택
3. URL 복사

4. `configs/character_config.yaml` 파일 수정:
```yaml
tongtong:
  youtube_urls:
    - "https://www.youtube.com/watch?v=복사한URL1"
    - "https://www.youtube.com/watch?v=복사한URL2"
    - "https://www.youtube.com/watch?v=복사한URL3"
```

---

### ✅ Step 1-6: 준비 확인

```bash
python -c "
import os
from dotenv import load_dotenv
import yaml

load_dotenv()

print('=== 준비 상태 확인 ===\n')

# API 키 확인
api_key = os.getenv('GEMINI_API_KEY')
if api_key and 'your_gemini' not in api_key:
    print('✅ Gemini API 키: 설정됨')
else:
    print('❌ Gemini API 키: 설정 필요')

# URL 확인
with open('configs/character_config.yaml', encoding='utf-8') as f:
    config = yaml.safe_load(f)
    urls = config['characters']['tongtong']['youtube_urls']
    if not any('EXAMPLE' in url for url in urls):
        print(f'✅ 유튜브 URL: {len(urls)}개 설정됨')
    else:
        print('❌ 유튜브 URL: 설정 필요')
"
```

**모두 ✅ 면 다음 단계로!**

---

## 🎯 Phase 2: 음성 학습

### 🟢 방법 A: 대화형 스크립트 (추천)

```bash
python scripts/quick_start_tongtong.py
```

**메뉴:**
```
1. 유튜브 다운로드
2. 보컬 분리
3. 전처리
4. 대본 생성 (선택)
5. 모델 학습
6. 모델 테스트

0. 전체 실행
```

**처음이면:**
- `1` 입력 → 다운로드 테스트
- 문제 없으면 `0` 입력 → 전체 실행

---

### 🟡 방법 B: 한 번에 실행

```bash
python scripts/train_multiple_characters.py --character tongtong
```

**예상 시간:**
- GPU: 1-3시간
- CPU: 6-12시간

---

### 📊 각 단계 상세

#### 2-1: 유튜브 다운로드 (10분)

```bash
# 방법 A 사용 시
python scripts/quick_start_tongtong.py
# → 1 선택
```

**결과 확인:**
```bash
ls data/raw/tongtong*
```

---

#### 2-2: 배경음 제거 (10-20분)

**패키지 설치:**
```bash
pip install spleeter
```

**실행:**
```bash
python scripts/quick_start_tongtong.py
# → 2 선택
```

**결과:**
```
data/vocals/tongtong/video1/vocals.wav
data/vocals/tongtong/video2/vocals.wav
...
```

---

#### 2-3: 전처리 (5-10분)

**패키지:**
```bash
pip install librosa soundfile noisereduce
```

**실행:**
```bash
python scripts/quick_start_tongtong.py
# → 3 선택
```

**결과:**
```
총 237개 세그먼트
예상 데이터: 약 19분 47초
```

---

#### 2-4: 대본 생성 (선택, 20-40분)

**패키지:**
```bash
pip install openai-whisper torch
```

**실행:**
```bash
python scripts/quick_start_tongtong.py
# → 4 선택
```

**건너뛰어도 됨!**

---

#### 2-5: 모델 학습 (1-12시간) ⭐

**전체 패키지 설치:**
```bash
pip install -r requirements.txt
```

**GPU 사용 시:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**GPT-SoVITS 설치:**
```bash
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
pip install -r requirements.txt
cd ..
```

**사전학습 모델 다운로드:**
- https://huggingface.co/lj1995/GPT-SoVITS
- `pretrained_models/` 에 저장

**실행:**
```bash
python scripts/quick_start_tongtong.py
# → 5 선택
```

**⏱️ 예상 시간:**
| 환경 | 시간 |
|------|------|
| RTX 3090 | 1-2시간 |
| RTX 3060 | 2-3시간 |
| CPU | 6-12시간 |

---

#### 2-6: 모델 테스트 (5분)

```bash
python scripts/quick_start_tongtong.py
# → 6 선택
```

**🎉 퉁퉁이 목소리 들림!**

---

## 🎯 Phase 3: 대화 시스템

### Step 3-1: 텍스트 챗봇 (1분)

```bash
python scripts/test_chatbot_simple.py
```

**대화 예시:**
```
👤 퉁퉁아, 안녕?
🐻 안녕! 나는 퉁퉁이야!

👤 오늘 뭐하고 놀까?
🐻 음... 축구하고 싶어!
```

---

### Step 3-2: 음성 대화 (최종)

**패키지:**
```bash
pip install sounddevice scipy
```

**실행:**
```bash
python scripts/test_voice_chat.py
# → 3 선택
```

**사용:**
```
Enter 누름 → 5초 녹음 → AI 응답 (퉁퉁이 목소리)
```

**🎉🎉🎉 완성!!!**

---

## 📊 체크리스트

### Phase 1: 준비
- [ ] Python 설치
- [ ] 가상환경 생성
- [ ] Gemini API 키
- [ ] 유튜브 URL 수집
- [ ] 설정 파일 수정

### Phase 2: 학습
- [ ] 다운로드 (10분)
- [ ] 배경음 제거 (20분)
- [ ] 전처리 (10분)
- [ ] 모델 학습 (1-12시간)
- [ ] 테스트

### Phase 3: 완성
- [ ] 텍스트 챗봇
- [ ] 음성 대화
- [ ] 🎉 완성!

---

## 🚨 문제 해결

### API 키 오류
```bash
# .env 파일 확인
cat .env | grep GEMINI
```

### 유튜브 다운로드 실패
```bash
pip install --upgrade yt-dlp
choco install ffmpeg  # Windows
```

### GPU 메모리 부족
```yaml
# character_config.yaml
batch_size: 2  # 4→2로 줄임
```

---

## 💡 빠른 명령어

```bash
# 전체 실행
python scripts/quick_start_tongtong.py

# 텍스트 챗봇
python scripts/test_chatbot_simple.py

# 음성 대화
python scripts/test_voice_chat.py
```

---

## 🎯 지금 시작!

```bash
# 첫 번째 명령어
python scripts/quick_start_tongtong.py
```

**🎉 행운을 빕니다!**
