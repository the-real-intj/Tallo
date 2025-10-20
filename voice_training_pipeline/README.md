# 🎤 음성 모델 학습 파이프라인

여러 캐릭터의 음성을 학습시켜 고품질 TTS(Text-to-Speech) 모델을 생성하는 완전 자동화 파이프라인입니다.

## ✨ 주요 기능

- 🎥 **유튜브 음성 자동 다운로드**: 유튜브 URL에서 음성 데이터 추출
- 🎵 **보컬 분리**: Spleeter/Demucs로 배경음악 제거
- 🔊 **음성 전처리**: 노이즈 제거, 정규화, 세그먼트 분할
- 🤖 **GPT-SoVITS 학습**: 1분 데이터로 고품질 음성 모델 학습
- 📦 **배치 처리**: 여러 캐릭터 동시 학습
- ✅ **품질 평가**: 자동 품질 검증 및 리포트 생성

## 📋 시스템 요구사항

### 하드웨어
- **GPU**: NVIDIA GPU (CUDA 지원) 권장
  - VRAM: 최소 8GB, 권장 12GB 이상
- **RAM**: 최소 16GB, 권장 32GB 이상
- **저장공간**: 최소 50GB 여유 공간

### 소프트웨어
- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.9 이상 (3.10 권장)
- **CUDA**: 11.8 이상 (GPU 사용 시)
- **FFmpeg**: 오디오 처리용

## 🚀 설치 가이드

### 1단계: 저장소 클론

```bash
git clone <your-repo-url>
cd voice_training_pipeline
```

### 2단계: Python 가상환경 생성

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3단계: 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4단계: FFmpeg 설치

#### Windows
```bash
# Chocolatey 사용
choco install ffmpeg

# 또는 수동 설치
# https://ffmpeg.org/download.html
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

### 5단계: Spleeter 모델 다운로드

Spleeter는 처음 실행 시 자동으로 모델을 다운로드합니다.

```bash
# 테스트 실행 (모델 자동 다운로드)
python -c "from spleeter.separator import Separator; Separator('spleeter:2stems')"
```

### 6단계: GPT-SoVITS 설정

```bash
# GPT-SoVITS 저장소 클론
git clone https://github.com/RVC-Boss/GPT-SoVITS.git

# GPT-SoVITS 의존성 설치
cd GPT-SoVITS
pip install -r requirements.txt
cd ..
```

### 7단계: 사전학습 모델 다운로드

GPT-SoVITS 사전학습 모델을 다운로드하세요:

```bash
# Hugging Face에서 다운로드
# https://huggingface.co/lj1995/GPT-SoVITS

# pretrained_models 디렉토리에 저장
mkdir -p pretrained_models
# 다운로드한 모델 파일을 pretrained_models/ 에 저장
```

### 8단계: 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 설정 조정
# 특히 GPU 설정, 경로 등을 확인하세요
```

## 📖 사용법

### 빠른 시작: 단일 캐릭터 학습

#### 1. 캐릭터 설정 파일 편집

`configs/character_config.yaml` 파일을 열고 캐릭터 정보를 입력하세요:

```yaml
characters:
  pororo:
    name: "뽀로로"
    youtube_urls:
      - "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
    personality:
      traits: ["호기심 많음", "장난기 많음"]
      speech_style: "밝고 경쾌한 말투"
    training:
      target_duration: 300
      epochs: 100
```

#### 2. 학습 실행

```bash
# 단일 캐릭터 학습
python scripts/train_multiple_characters.py --character pororo

# 모든 캐릭터 순차 학습
python scripts/train_multiple_characters.py --mode sequential

# 모든 캐릭터 병렬 학습 (2개 동시)
python scripts/train_multiple_characters.py --mode parallel --workers 2
```

### 상세 사용법

#### 1. 유튜브 음성 다운로드만 실행

```python
from tools.youtube_downloader import YouTubeAudioDownloader

downloader = YouTubeAudioDownloader(output_dir="./data/raw")

# 단일 다운로드
file_path = downloader.download_audio(
    "https://www.youtube.com/watch?v=EXAMPLE",
    character_name="pororo"
)

# 배치 다운로드
urls = [
    "https://www.youtube.com/watch?v=EXAMPLE1",
    "https://www.youtube.com/watch?v=EXAMPLE2",
]
files = downloader.download_batch("pororo", urls)
```

#### 2. 음성 전처리만 실행

```python
from tools.audio_preprocessor import AudioPreprocessor

preprocessor = AudioPreprocessor(sample_rate=22050)

output_files = preprocessor.process_audio(
    input_path="./data/raw/pororo.wav",
    output_dir="./data/processed",
    character_name="pororo",
    enable_noise_reduction=True,
    enable_normalization=True,
    segment_config={
        'min_length': 3.0,
        'max_length': 10.0,
        'overlap': 0.5
    }
)
```

#### 3. 보컬 분리만 실행

```python
from tools.vocal_separator import VocalSeparator

separator = VocalSeparator(method="spleeter")

vocals_path = separator.separate(
    "./data/raw/pororo.wav",
    stems="2stems"
)
```

#### 4. 모델 테스트

```bash
# 단일 텍스트 테스트
python scripts/test_model.py \
    --character pororo \
    --text "안녕하세요! 저는 뽀로로예요!"

# 전체 샘플 테스트 (품질 리포트 생성)
python scripts/test_model.py \
    --character pororo \
    --full-test
```

## 📁 프로젝트 구조

```
voice_training_pipeline/
├── configs/
│   └── character_config.yaml      # 캐릭터 설정 파일
├── data/
│   ├── raw/                        # 원본 오디오
│   ├── vocals/                     # 보컬 분리된 오디오
│   ├── processed/                  # 전처리된 오디오
│   ├── segments/                   # 세그먼트
│   └── datasets/                   # 학습용 데이터셋
├── models/
│   ├── gpt_sovits/                 # 학습된 GPT-SoVITS 모델
│   ├── rvc/                        # RVC 모델 (선택)
│   └── checkpoints/                # 체크포인트
├── tools/
│   ├── youtube_downloader.py       # 유튜브 다운로더
│   ├── audio_preprocessor.py       # 음성 전처리
│   ├── vocal_separator.py          # 보컬 분리
│   └── gpt_sovits_trainer.py       # GPT-SoVITS 학습
├── scripts/
│   ├── train_multiple_characters.py # 배치 학습
│   └── test_model.py               # 모델 테스트
├── output/
│   ├── audio/                      # 생성된 음성
│   └── reports/                    # 학습/테스트 리포트
├── logs/                           # 로그 파일
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 설정 커스터마이징

### 캐릭터별 설정

`configs/character_config.yaml`에서 각 캐릭터마다 다음을 설정할 수 있습니다:

```yaml
characters:
  your_character:
    # 기본 정보
    name: "캐릭터 이름"
    description: "캐릭터 설명"

    # 음성 소스
    youtube_urls:
      - "URL1"
      - "URL2"

    # 학습 설정
    training:
      target_duration: 300        # 목표 학습 데이터 길이 (초)
      min_segment_length: 3       # 최소 세그먼트 길이
      max_segment_length: 10      # 최대 세그먼트 길이

      gpt_sovits:
        epochs: 100               # 학습 에포크
        batch_size: 4             # 배치 크기
        learning_rate: 0.0001     # 학습률
        save_interval: 10         # 저장 간격

    # 음성 처리 설정
    audio_processing:
      noise_reduction: true       # 노이즈 제거
      normalization: true         # 정규화
      trim_silence: true          # 무음 제거
      target_loudness: -20        # 목표 음량 (dB)
```

### GPU/CPU 설정

`.env` 파일에서:

```bash
# GPU 사용
USE_GPU=true
DEVICE=cuda

# CPU만 사용
USE_GPU=false
DEVICE=cpu

# Mac M1/M2
DEVICE=mps
```

## 📊 학습 진행 상황 모니터링

### 로그 파일 확인

```bash
# 실시간 로그 확인
tail -f logs/training.log
```

### 학습 리포트 확인

학습 완료 후 `output/reports/` 디렉토리에서 JSON 리포트를 확인하세요:

```json
{
  "pororo": {
    "status": "success",
    "duration_seconds": 3600,
    "model_dir": "./models/gpt_sovits/pororo",
    "steps": {
      "download": {"status": "success", "files_count": 5},
      "vocal_separation": {"status": "success"},
      "preprocessing": {"segments_count": 150},
      "training": {"status": "success"}
    }
  }
}
```

## ⚠️ 문제 해결

### GPU 메모리 부족

```yaml
# character_config.yaml에서 배치 크기 줄이기
training:
  gpt_sovits:
    batch_size: 2  # 기본값 4에서 줄임
```

### Spleeter 설치 오류

```bash
# Spleeter 수동 설치
pip uninstall spleeter
pip install spleeter==2.4.0

# 또는 Demucs 사용
# configs/character_config.yaml에서:
# vocal_separator: "demucs"
```

### FFmpeg 오류

```bash
# FFmpeg 경로 확인
ffmpeg -version

# Windows에서 PATH에 추가
# 시스템 환경 변수 > Path에 ffmpeg bin 디렉토리 추가
```

### 유튜브 다운로드 오류

```bash
# yt-dlp 업데이트
pip install --upgrade yt-dlp

# 또는 pytube 사용
# youtube_downloader.py에서 backend 변경
```

## 🎯 성능 최적화 팁

### 1. 데이터 품질
- 깨끗한 음성 (배경음악/노이즈 적음)
- 다양한 감정/억양 포함
- 총 5-10분 분량 권장

### 2. 학습 설정
- **빠른 테스트**: epochs=50, batch_size=8
- **고품질**: epochs=100-200, batch_size=4
- **프로덕션**: epochs=200+, 데이터 증강 활성화

### 3. 하드웨어
- GPU 사용 시 학습 속도 10-20배 향상
- VRAM이 부족하면 batch_size 줄이기
- 병렬 학습 시 GPU당 1개 캐릭터 권장

## 📚 참고 자료

- [GPT-SoVITS 공식 문서](https://github.com/RVC-Boss/GPT-SoVITS)
- [Spleeter 가이드](https://github.com/deezer/spleeter)
- [Whisper 문서](https://github.com/openai/whisper)

## 🤝 기여

이슈와 PR을 환영합니다!

## 📄 라이선스

MIT License

---

**Made with ❤️ for voice cloning enthusiasts**
