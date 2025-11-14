# tts_api.py 실행을 위한 패키지 설치 가이드

## 📦 필수 패키지 목록

### 1. FastAPI 서버 관련
```bash
pip install fastapi uvicorn[standard] pydantic python-dotenv
```

### 2. PyTorch (CPU 또는 GPU 선택)

**CPU 버전** (모든 플랫폼):
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**GPU 버전** (CUDA 11.8 사용 시):
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. OpenAI (LLM 기능 사용 시 필수)
```bash
pip install openai
```

### 4. Zonos 모델 의존성
```bash
pip install numpy transformers huggingface-hub soundfile
pip install inflect kanjize phonemizer
pip install sudachipy sudachidict-full
```

### 5. Zonos 모듈 설치 (가장 중요!)
```bash
cd /home/future/Tallo/service/Zonos
pip install -e .
cd ..
```

## 🚀 한 번에 설치하기

### 방법 1: requirements.txt 사용

```bash
cd /home/future/Tallo/service

# 1. requirements.txt의 패키지 설치
pip install -r requirements.txt

# 2. PyTorch 설치 (CPU 버전)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 3. Zonos 모듈 설치 (필수!)
cd Zonos
pip install -e .
cd ..
```

### 방법 2: 한 줄로 설치

```bash
cd /home/future/Tallo/service

# 기본 패키지
pip install fastapi uvicorn[standard] pydantic python-dotenv openai \
  numpy transformers huggingface-hub soundfile \
  inflect kanjize phonemizer sudachipy sudachidict-full

# PyTorch (CPU)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Zonos 모듈
cd Zonos && pip install -e . && cd ..
```

## ✅ 설치 확인

```bash
# Python에서 확인
python -c "import fastapi; import torch; import zonos; print('✅ 모든 패키지 설치 완료!')"
```

## 📋 패키지별 설명

| 패키지 | 용도 | 필수 여부 |
|--------|------|----------|
| `fastapi` | 웹 서버 프레임워크 | ✅ 필수 |
| `uvicorn` | ASGI 서버 (FastAPI 실행용) | ✅ 필수 |
| `pydantic` | 데이터 검증 | ✅ 필수 |
| `python-dotenv` | .env 파일에서 환경 변수 로드 | ✅ 필수 |
| `torch`, `torchaudio` | PyTorch (TTS 모델 실행) | ✅ 필수 |
| `openai` | LLM 기능 (채팅) | ⚠️ LLM 사용 시 필요 |
| `numpy` | 수치 연산 | ✅ 필수 |
| `transformers` | Hugging Face 모델 로드 | ✅ 필수 |
| `huggingface-hub` | Hugging Face 모델 다운로드 | ✅ 필수 |
| `soundfile` | 오디오 파일 읽기/쓰기 | ✅ 필수 |
| `phonemizer` | 음성 합성 전처리 | ✅ 필수 |
| `inflect`, `kanjize` | 텍스트 처리 | ✅ 필수 |
| `sudachipy`, `sudachidict-full` | 일본어/한국어 형태소 분석 | ✅ 필수 |
| `zonos` | Zonos TTS 모델 (프로젝트 내부) | ✅ 필수 |

## 🔧 문제 해결

### 문제 1: "No module named 'zonos'"

**해결**: Zonos 모듈을 설치해야 합니다:
```bash
cd /home/future/Tallo/service/Zonos
pip install -e .
```

### 문제 2: PyTorch 설치 오류

**해결**: CUDA 버전을 확인하고 맞는 버전 설치:
```bash
# CUDA 버전 확인
nvidia-smi

# CUDA 11.8이면
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# CPU만 있으면
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 문제 3: "No module named 'soundfile'"

**해결**: 시스템 의존성 설치가 필요할 수 있습니다:
```bash
# Ubuntu/Debian
sudo apt install libsndfile1

# macOS
brew install libsndfile

# 그 다음 pip 설치
pip install soundfile
```

### 문제 4: phonemizer 오류

**해결**: espeak-ng 설치 필요:
```bash
# Ubuntu/Debian
sudo apt install espeak-ng

# macOS
brew install espeak-ng
```

## 🎯 최소 설치 (테스트용)

빠른 테스트만 하려면:
```bash
# 최소 필수 패키지만
pip install fastapi uvicorn pydantic python-dotenv
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
cd Zonos && pip install -e . && cd ..
```

LLM 기능은 나중에 필요하면 설치:
```bash
pip install openai
```

## 📝 다음 단계

설치 완료 후:

1. `.env` 파일 생성 (API 키 설정)
2. 서버 실행: `python api/tts_api.py`
3. `http://localhost:8000/docs`에서 API 확인

