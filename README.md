# Tallo TTS Service

한국어 텍스트를 음성으로 변환하는 FastAPI 기반 TTS 서비스입니다. Zonos 모델을 사용하여 고품질 음성 합성을 제공합니다.

## 시스템 요구사항

### GPU 환경 (권장)
- **GPU**: NVIDIA GPU 6GB+ VRAM (RTX 3060 이상)
- **OS**: Linux (Ubuntu 22.04/24.04 권장)
- **CUDA**: 11.8 이상
- **RAM**: 16GB 이상

### CPU 환경 (느림)
- **CPU**: 멀티코어 프로세서
- **RAM**: 32GB 이상
- **OS**: Linux, macOS
- ⚠️ 생성 속도가 매우 느립니다 (GPU 대비 50~100배)

## 설치

### 1. 시스템 의존성 설치

```bash
# Ubuntu/Debian
sudo apt install -y espeak-ng

# macOS
brew install espeak-ng
```

### 2. Python 가상환경 설정

```bash
cd /home/future/Tallo/service

# Zonos 디렉터리로 이동
cd Zonos

# 가상환경 생성 및 활성화
python3 -m venv zonos_env
source zonos_env/bin/activate

# Zonos 설치
pip install -e .

# GPU 환경: CUDA 버전에 맞는 PyTorch 설치
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# CPU 환경: CPU 전용 PyTorch 설치
# pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 3. FastAPI 의존성 설치

```bash
cd /home/future/Tallo/service
pip install fastapi uvicorn pydantic
```

## 실행

### 서버 시작

```bash
cd /home/future/Tallo/service

# 가상환경 활성화
source Zonos/zonos_env/bin/activate

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

서버가 시작되면 `http://localhost:8001`에서 접근 가능합니다.

### API 문서 확인

브라우저에서 `http://localhost:8001/docs` 접속

## 사용 방법

### 기본 TTS 요청

```bash
# 짧은 텍스트 합성
curl -X POST http://localhost:8001/tts/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text":"안녕하세요. 오늘 날씨가 참 좋네요.","language":"ko"}' \
     -o output.wav
```

### 파일 기반 TTS 요청

```bash
# Zonos/assets/ 에 텍스트 파일 업로드 후
# 기본 요청 (감정 없음)
curl -X POST http://localhost:8001/tts/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text_asset":"아기돼지삼형제.txt","language":"ko"}' \
     -o story.wav
```

### 감정 표현 추가

```bash
# 공포 감정 강조
curl -X POST http://localhost:8001/tts/synthesize \
     -H "Content-Type: application/json" \
     -d '{
       "text":"아 뜨거워! 늑대 살려!",
       "language":"ko",
       "emotion":[0.0, 0.0, 0.0, 0.7, 0.2, 0.0, 0.1, 0.0]
     }' \
     -o scared.wav
```

**감정 벡터:** `[기쁨, 슬픔, 혐오, 공포, 놀람, 분노, 기타, 중립]`

### 자동 감정 인식

```bash
# 텍스트 내용 분석해서 자동으로 감정 적용
curl -X POST http://localhost:8001/tts/synthesize \
     -H "Content-Type: application/json" \
     -d '{
       "text_asset":"아기돼지삼형제.txt",
       "language":"ko",
       "auto_emotion":true
     }' \
     -o story_emotional.wav
```

## 주요 기능

### ✅ 자동 텍스트 길이 처리
- **5문장 미만**: 한 번에 합성
- **5문장 이상**: 청크로 분할 → 병합

### ✅ 자동 환경 최적화
- **GPU 환경**: 순차 처리 (빠름, 효율적)
- **CPU 환경**: 병렬 처리 (3개 청크 동시)

### ✅ 감정 표현
- 수동 지정: `emotion` 파라미터
- 자동 인식: `auto_emotion=true`

### ✅ 음질 조정
- `speaking_rate`: 말하기 속도 (10=느림, 30=빠름)
- `pitch_std`: 억양 변화 (20-45=자연스러움)

## 예상 처리 시간

### GPU 환경 (RTX 4090)
- 짧은 텍스트 (1~2문장): **5~10초**
- 긴 텍스트 (100줄): **2~5분**

### CPU 환경
- 짧은 텍스트 (1~2문장): **5~10분**
- 긴 텍스트 (100줄): **3~10시간** (비권장)

## API 엔드포인트

### POST `/tts/synthesize`
텍스트를 음성으로 합성

**요청 본문:**
```json
{
  "text": "합성할 텍스트 (선택)",
  "text_asset": "파일명.txt (선택)",
  "language": "ko",
  "emotion": [0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.4],
  "auto_emotion": false,
  "as_file": true
}
```

**응답:** WAV 파일 (audio/wav)

### POST `/tts/synthesize-long`
긴 텍스트 전용 (명시적 청크 처리)

## 문제 해결

### GPU 메모리 부족
```bash
# max_workers 조정 (api/tts.py)
max_workers = 1  # GPU는 1로 고정
```

### espeak-ng 오류
```bash
# 재설치
sudo apt remove espeak-ng
sudo apt install -y espeak-ng
```

### 음질 개선
1. **한국어 스피커 샘플 교체**
   - `Zonos/assets/`에 한국어 원어민 음성 (10~30초, 44.1kHz)
   - `Zonos/tts.py`에서 `speaker_wav` 경로 변경

2. **파라미터 조정**
   ```python
   speaking_rate=13.0,  # 느릴수록 명확
   pitch_std=35.0,      # 자연스러운 억양
   ```

## 디렉터리 구조

```
service/
├── main.py                 # FastAPI 앱
├── api/
│   ├── tts.py             # TTS 엔드포인트 (자동 분기)
│   └── tts_long.py        # 긴 텍스트 전용
├── utils/
│   └── emotion_detector.py # 감정 자동 인식
├── Zonos/
│   ├── tts.py             # Zonos TTS 래퍼
│   ├── assets/            # 스피커 샘플, 텍스트 파일
│   └── zonos_env/         # 가상환경
└── outputs/
    └── tts/               # 생성된 WAV 파일 (자동 정리)
```

## 라이선스

Zonos: [Apache 2.0](https://github.com/Zyphra/Zonos)

## 참고

- Zonos 공식 문서: https://github.com/Zyphra/Zonos
- FastAPI 문서: https://fastapi.tiangolo.com/

