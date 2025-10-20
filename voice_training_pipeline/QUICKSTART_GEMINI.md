# 🚀 Gemini 2.0 Flash-Lite 빠른 시작 가이드

Gemini 2.0 Flash-Lite를 사용한 AI 음성 캐릭터 시스템 테스트 가이드입니다.

## 💰 비용 정보

| 항목 | 모델 | 비용 |
|------|------|------|
| **음성 인식** | Whisper (로컬) | **무료** |
| **대화 생성** | Gemini 2.0 Flash-Lite | **무료** (15 RPM, 500 RPD) |
| **음성 합성** | GPT-SoVITS (로컬) | **무료** |

→ **완전 무료로 하루 500회 대화 가능!**

## 📋 필수 준비사항

### 1. Python 환경
- Python 3.9 이상 설치 필요
- 가상환경 권장

### 2. Gemini API 키 발급 (무료)
1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. "Create API Key" 클릭
3. 프로젝트 선택 (또는 새로 생성)
4. API 키 복사

### 3. .env 파일 설정
`.env` 파일을 열고 API 키를 입력하세요:

```bash
# .env 파일
GEMINI_API_KEY=여기에_발급받은_API_키_붙여넣기
```

## 🎯 테스트 시나리오

### 🔰 시나리오 1: 텍스트 챗봇 (가장 쉬움)
**준비물:** API 키만 있으면 됨

```bash
# 1. 최소 패키지만 설치
pip install google-generativeai python-dotenv

# 2. 텍스트 챗봇 실행
python scripts/test_chatbot_simple.py
```

**테스트 방법:**
- 텍스트로 대화 입력
- Gemini가 뽀로로 캐릭터로 응답
- 비용: $0.00 (무료)

**예상 결과:**
```
👤 당신: 안녕! 너 이름이 뭐야?
🐧 뽀로로: 안녕! 나는 뽀로로야! 🎉 너는 누구야?
```

---

### 🎤 시나리오 2: 음성 대화 (중급)
**준비물:** 마이크 + API 키

```bash
# 1. 필수 패키지 설치 (처음 한 번만)
pip install google-generativeai python-dotenv openai-whisper sounddevice scipy

# 2. 음성 대화 테스트 실행
python scripts/test_voice_chat.py
```

**메뉴 선택:**
```
1. STT만 테스트 (음성 인식) ← 먼저 이것부터 테스트 권장
2. 챗봇만 테스트 (텍스트 대화)
3. 풀 파이프라인 (음성 대화)
```

**테스트 플로우:**
1. Enter 누르면 5초간 녹음
2. Whisper가 음성을 텍스트로 변환
3. Gemini 2.0 Flash-Lite가 응답 생성
4. 텍스트로 응답 출력 (TTS는 선택)

---

### 🎭 시나리오 3: 풀 파이프라인 (고급)
**준비물:** 마이크 + 스피커 + GPT-SoVITS 모델

```bash
# 1. 전체 패키지 설치
pip install -r requirements.txt

# 2. 캐릭터 음성 모델 학습 (기존 파이프라인)
python scripts/train_multiple_characters.py --character pororo

# 3. 풀 파이프라인 실행
python scripts/test_voice_chat.py
# → 메뉴에서 3번 선택
```

**완전한 음성 대화:**
- 마이크로 말하기
- AI가 뽀로로 목소리로 대답
- 비용: $0.00 (모두 로컬 또는 무료)

---

## 🛠️ 설치 가이드

### 방법 1: 최소 설치 (텍스트만)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# 최소 패키지
pip install google-generativeai python-dotenv

# 테스트
python scripts/test_chatbot_simple.py
```

### 방법 2: 음성 포함 (권장)
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 필수 패키지
pip install --upgrade pip
pip install google-generativeai python-dotenv
pip install openai-whisper
pip install sounddevice scipy

# 테스트
python scripts/test_voice_chat.py
```

### 방법 3: 전체 설치 (풀 파이프라인)
```bash
# 가상환경 생성
python -m venv venv
venv\Scripts\activate

# 전체 패키지 (시간 오래 걸림)
pip install --upgrade pip
pip install -r requirements.txt

# FFmpeg 설치 (오디오 처리용)
# Windows: choco install ffmpeg
# Linux: sudo apt install ffmpeg
# Mac: brew install ffmpeg
```

---

## 🧪 테스트 예제

### 예제 1: 간단한 텍스트 대화
```python
from tools.chatbot import create_chatbot

# 챗봇 생성
bot = create_chatbot(
    character_name="뽀로로",
    use_gemini=True  # Gemini 2.0 Flash-Lite
)

# 대화
response = bot.get_response("안녕! 오늘 뭐 하고 놀까?")
print(response)
# 출력: "안녕! 오늘 날씨 좋은데 밖에 나가서 놀까? 🎉"
```

### 예제 2: 음성 인식
```python
from tools.speech_to_text import create_stt

# Whisper 초기화
stt = create_stt(method="whisper", model_size="base")

# 5초 녹음 후 텍스트 변환
text = stt.record_and_transcribe(duration=5)
print(f"인식 결과: {text}")
```

### 예제 3: 통합 사용
```python
from tools.speech_to_text import create_stt
from tools.chatbot import create_chatbot

# 초기화
stt = create_stt(method="whisper", model_size="base")
bot = create_chatbot(character_name="뽀로로")

# 음성 입력
user_text = stt.record_and_transcribe(duration=5)
print(f"사용자: {user_text}")

# AI 응답
response = bot.get_response(user_text)
print(f"뽀로로: {response}")
```

---

## ⚙️ 설정 커스터마이징

### Whisper 모델 크기 조정
`.env` 파일 또는 코드에서:

```python
# 빠른 테스트용 (저사양)
stt = create_stt(model_size="tiny")   # 가장 빠름, 정확도 낮음

# 균형 (권장)
stt = create_stt(model_size="base")   # 속도/정확도 균형

# 고품질 (GPU 권장)
stt = create_stt(model_size="small")  # 정확도 높음
```

### 캐릭터 성격 변경
```python
bot = create_chatbot(
    character_name="크롱",
    personality_traits=[
        "장난꾸러기",
        "말이 적음",
        "귀여움"
    ],
    speech_style="짧고 단순한 말투, '크롱크롱' 자주 사용"
)
```

### GPU 사용 설정
`.env` 파일:
```bash
USE_GPU=true
DEVICE=cuda  # NVIDIA GPU

# Mac M1/M2
DEVICE=mps

# CPU만 사용
USE_GPU=false
DEVICE=cpu
```

---

## ❓ 문제 해결

### 1. API 키 오류
```
❌ ValueError: GEMINI_API_KEY가 설정되지 않았습니다.
```

**해결:**
- `.env` 파일에 API 키 추가
- API 키 확인: https://aistudio.google.com/app/apikey

### 2. 무료 한도 초과
```
❌ Quota exceeded: 15 RPM
```

**해결:**
- 1분에 15회 제한 → 잠시 대기
- 하루 500회 제한 → 내일 사용
- 또는 유료 플랜 전환

### 3. Whisper 로딩 느림
```
⏳ Whisper 모델 로딩 중... (오래 걸림)
```

**해결:**
- 처음 실행 시 모델 다운로드 (1-2분)
- 더 작은 모델 사용: `model_size="tiny"`
- GPU 사용 시 빠름

### 4. 마이크 인식 안 됨
```
⚠️ 음성이 인식되지 않았습니다.
```

**해결:**
- 마이크 권한 확인
- 마이크 연결 확인
- 다른 앱에서 마이크 사용 중인지 확인
- 녹음 시간 늘리기: `duration=10`

### 5. 패키지 설치 오류 (Windows)
```
❌ ERROR: Failed building wheel for xyz
```

**해결:**
- Visual Studio Build Tools 설치
- 또는 사전 빌드 버전 사용:
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```

---

## 📊 성능 벤치마크

| 항목 | 시간 | 비용 |
|------|------|------|
| Whisper (base, CPU) | ~3-5초 | $0.00 |
| Whisper (base, GPU) | ~1-2초 | $0.00 |
| Gemini 2.0 Flash-Lite | ~0.5-1초 | $0.00 (무료) |
| **전체 응답 시간** | **~4-6초** | **$0.00** |

**100회 대화 예상 비용:**
- Whisper (로컬): $0.00
- Gemini (무료): $0.00
- **총 비용: $0.00**

---

## 🎯 다음 단계

### 1. 캐릭터 추가
`configs/character_config.yaml`에 새 캐릭터 추가

### 2. 음성 모델 학습
기존 파이프라인으로 GPT-SoVITS 모델 학습

### 3. 웹 인터페이스
FastAPI로 웹 서비스 구축

### 4. 실시간 대화
스트리밍 응답 구현

---

## 📚 참고 자료

- [Gemini API 문서](https://ai.google.dev/docs)
- [Whisper GitHub](https://github.com/openai/whisper)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)

---

## 💡 팁

1. **처음에는 시나리오 1부터** 시작하세요 (텍스트만)
2. **API 키 발급은 30초** 만에 가능합니다
3. **무료 티어로 충분히** 테스트할 수 있습니다
4. **GPU 없어도** CPU로 실행 가능 (조금 느림)
5. **문제 발생 시** GitHub Issues에 문의

---

**Made with ❤️ using Gemini 2.0 Flash-Lite**
