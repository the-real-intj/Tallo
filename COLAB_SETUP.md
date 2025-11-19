# 코랩(Colab)에서 실행하기 가이드

## 1. 실행하면 어떻게 되는가?

`tts_api.py`를 실행하면:

1. **FastAPI 서버 시작** (`0.0.0.0:8000`)
   - REST API 서버가 시작됩니다
   - GPU를 사용할 수 있으면 자동으로 감지하여 사용

2. **Zonos 모델 로드**
   - `Zyphra/Zonos-v0.1-transformer` 모델을 Hugging Face에서 자동 다운로드
   - 첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다 (~2-3GB)

3. **API 엔드포인트 제공**
   - `/docs`: API 문서 (Swagger UI)
   - `/tts/generate`: TTS 생성
   - `/characters/create`: 캐릭터 생성
   - `/llm/chat`: LLM + TTS 통합
   - 등등...

4. **ngrok을 통해 외부 접근 가능** (코랩에서 필수)

## 2. 코랩에서 실행할 때 필요한 파일

### 필수 파일들

```
Tallo/
├── service/
│   ├── api/
│   │   └── tts_api.py          ✅ 필수
│   └── Zonos/
│       ├── zonos/              ✅ 필수 (전체 디렉토리)
│       │   ├── __init__.py
│       │   ├── model.py
│       │   ├── autoencoder.py
│       │   ├── conditioning.py
│       │   ├── utils.py
│       │   ├── config.py
│       │   ├── sampling.py
│       │   ├── codebook_pattern.py
│       │   ├── speaker_cloning.py
│       │   └── backbone/
│       │       ├── __init__.py
│       │       ├── _torch.py
│       │       └── _mamba_ssm.py (선택)
│       └── pyproject.toml       ✅ 필수 (의존성 확인용)
```

### 필요한 디렉토리 구조

실행 시 자동으로 생성되지만, 미리 생성할 수도 있습니다:

```
service/
├── embeddings/       (캐릭터 임베딩 저장)
├── audios/           (참조 오디오 저장)
├── outputs/          (생성된 TTS 파일)
└── cache/            (동화책 캐시)
```

## 3. 코랩 실행 스크립트

```python
# ==========================================
# 1. 필수 패키지 설치
# ==========================================
!pip install -q fastapi uvicorn[standard] pydantic
!pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cu118
!pip install -q transformers huggingface-hub soundfile
!pip install -q phonemizer inflect kanjize sudachipy sudachidict-full
!pip install -q pyngrok  # ngrok 설치

# ==========================================
# 2. 파일 업로드 (필요한 파일들을 코랩에 업로드)
# ==========================================
# Google Drive 마운트 또는 직접 업로드
from google.colab import files
# 필요한 디렉토리 구조 생성

# ==========================================
# 3. Zonos 모듈 경로 설정
# ==========================================
import sys
sys.path.insert(0, '/content/service/Zonos')  # 경로 조정 필요

# ==========================================
# 4. 서버 실행
# ==========================================
# tts_api.py를 실행하면 됩니다
```

## 4. 코랩 완전 자동화 스크립트

```python
# ==========================================
# 코랩 셀 1: 환경 설정
# ==========================================

# GPU 확인
import torch
print(f"GPU 사용 가능: {torch.cuda.is_available()}")
print(f"GPU 이름: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")

# 필수 패키지 설치
!pip install -q fastapi uvicorn[standard] pydantic
!pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cu118
!pip install -q transformers huggingface-hub soundfile
!pip install -q phonemizer inflect kanjize sudachipy sudachidict-full
!pip install -q pyngrok motor pymongo

# espeak-ng 설치 (phonemizer에 필요)
!apt-get update -qq && apt-get install -y -qq espeak-ng

print("✅ 패키지 설치 완료")

# ==========================================
# 코랩 셀 2: 파일 업로드 또는 Drive 마운트
# ==========================================

# 방법 1: Google Drive 사용
from google.colab import drive
drive.mount('/content/drive')

# 방법 2: 직접 업로드 (수동)
# 필요한 파일들을 코랩 파일 브라우저로 업로드

# ==========================================
# 코랩 셀 3: 디렉토리 구조 생성
# ==========================================

import os
from pathlib import Path

# 기본 디렉토리 구조 생성
base_dir = Path("/content/service")
base_dir.mkdir(exist_ok=True)

dirs = ["embeddings", "audios", "outputs", "cache"]
for dir_name in dirs:
    (base_dir / dir_name).mkdir(exist_ok=True)

print("✅ 디렉토리 구조 생성 완료")

# ==========================================
# 코랩 셀 4: 서버 실행 + ngrok 터널링
# ==========================================

import subprocess
from pyngrok import ngrok

# ngrok 인증 토큰 설정 (무료 계정: https://dashboard.ngrok.com/get-started/your-authtoken)
# ngrok.set_auth_token("YOUR_NGROK_TOKEN")  # 필요시 주석 해제

# 백그라운드로 서버 실행
server_process = subprocess.Popen(
    ["python", "/content/service/api/tts_api.py"],
    cwd="/content/service"
)

# 잠시 대기 (서버 시작 시간)
import time
time.sleep(10)

# ngrok 터널 생성
public_url = ngrok.connect(8000)
print(f"🌐 Public URL: {public_url}")
print(f"📖 API Docs: {public_url}/docs")

# 서버 로그 확인
print("\n서버가 실행 중입니다. 위 URL을 사용하여 API에 접근할 수 있습니다.")
```

## 5. 파일 업로드 방법

### 방법 1: Google Drive 사용

```python
from google.colab import drive
drive.mount('/content/drive')

# Drive에서 파일 복사
!cp -r /content/drive/MyDrive/Tallo/service /content/
```

### 방법 2: Git 사용 (권장)

```python
# GitHub에 업로드 후
!git clone https://github.com/YOUR_USERNAME/Tallo.git /content/Tallo
```

### 방법 3: 수동 업로드

```python
from google.colab import files
# 파일 브라우저에서 필요한 파일들 업로드
```

## 6. 필수 파일 체크리스트

코랩에 업로드해야 할 파일:

- [ ] `service/api/tts_api.py`
- [ ] `service/Zonos/zonos/` (전체 디렉토리)
  - [ ] `zonos/__init__.py` (없으면 생성 필요)
  - [ ] `zonos/model.py`
  - [ ] `zonos/autoencoder.py`
  - [ ] `zonos/conditioning.py`
  - [ ] `zonos/utils.py`
  - [ ] `zonos/config.py`
  - [ ] `zonos/sampling.py`
  - [ ] `zonos/codebook_pattern.py`
  - [ ] `zonos/speaker_cloning.py`
  - [ ] `zonos/backbone/` (전체 디렉토리)

## 7. 주의사항

1. **모델 다운로드**: 첫 실행 시 Hugging Face에서 모델을 다운로드합니다 (~2-3GB)
2. **GPU 메모리**: Transformer 모델은 약 4-6GB VRAM 필요
3. **ngrok 토큰**: 무료 계정은 세션당 2시간 제한
4. **파일 경로**: 코드에서 경로를 `/content/service`로 조정해야 할 수 있습니다

## 8. 빠른 테스트

서버가 실행되면:

```python
import requests

# 서버 상태 확인
response = requests.get("http://localhost:8000/health")
print(response.json())

# 또는 ngrok URL 사용
# response = requests.get(f"{public_url}/health")
```

