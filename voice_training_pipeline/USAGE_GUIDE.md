# 📘 상세 사용 가이드

## 목차

1. [시작하기 전에](#시작하기-전에)
2. [첫 캐릭터 학습하기](#첫-캐릭터-학습하기)
3. [고급 설정](#고급-설정)
4. [여러 캐릭터 학습](#여러-캐릭터-학습)
5. [문제 해결](#문제-해결)
6. [성능 최적화](#성능-최적화)

---

## 시작하기 전에

### 1. 환경 체크

먼저 시스템 환경이 올바르게 설정되었는지 확인하세요:

```bash
python scripts/check_environment.py
```

모든 항목이 ✅로 표시되면 준비 완료입니다.

### 2. 필요한 데이터 준비

캐릭터 음성 학습을 위해 필요한 것:

- ✅ **유튜브 영상 URL**: 캐릭터 음성이 포함된 영상 (3-5개 권장)
- ✅ **총 음성 길이**: 최소 5분, 권장 10-15분
- ✅ **음성 품질**: 깨끗한 음성 (배경음악이 있어도 OK, 자동 분리됨)

---

## 첫 캐릭터 학습하기

### 방법 1: 빠른 시작 (추천)

대화형 인터페이스로 쉽게 시작:

```bash
python scripts/quick_start.py
```

질문에 따라 답변하면 자동으로 설정 파일이 생성됩니다.

#### 예시 대화

```
캐릭터 ID (영문, 예: pororo): pororo
캐릭터 이름 (예: 뽀로로): 뽀로로
캐릭터 설명 (선택, Enter로 건너뛰기): 호기심 많은 꼬마 펭귄

유튜브 URL #1: https://www.youtube.com/watch?v=xxxxx
유튜브 URL #2: https://www.youtube.com/watch?v=yyyyy
유튜브 URL #3: (Enter로 완료)

학습 품질을 선택하세요:
  1. 빠른 테스트 (50 epochs) - 약 30분
  2. 일반 품질 (100 epochs) - 약 1-2시간
  3. 고품질 (200 epochs) - 약 3-4시간
선택 (1-3, 기본값: 2): 2
```

### 방법 2: 수동 설정

#### 1) 설정 파일 편집

`configs/character_config.yaml` 파일을 열고 캐릭터 정보를 입력:

```yaml
characters:
  pororo:
    name: "뽀로로"
    description: "호기심 많은 꼬마 펭귄"

    youtube_urls:
      - "https://www.youtube.com/watch?v=example1"
      - "https://www.youtube.com/watch?v=example2"
      - "https://www.youtube.com/watch?v=example3"

    personality:
      traits:
        - "호기심 많음"
        - "장난기 많음"
        - "친구들을 좋아함"
      speech_style: "밝고 경쾌한 말투, 높은 톤"
      age_group: "3-5세"

    training:
      target_duration: 300
      min_segment_length: 3
      max_segment_length: 10
      sample_rate: 22050

      gpt_sovits:
        epochs: 100
        batch_size: 4
        learning_rate: 0.0001
        save_interval: 10

    audio_processing:
      noise_reduction: true
      normalization: true
      trim_silence: true
      target_loudness: -20
```

#### 2) 학습 시작

```bash
python scripts/train_multiple_characters.py --character pororo
```

### 학습 과정

학습은 다음 5단계로 진행됩니다:

1. **유튜브 다운로드** (5-10분)
   - 영상에서 오디오 추출
   - 자동으로 WAV 형식으로 변환

2. **보컬 분리** (10-20분)
   - Spleeter로 배경음악/효과음 제거
   - 깨끗한 음성만 추출

3. **음성 전처리** (5-10분)
   - 노이즈 제거
   - 무음 구간 제거
   - 3-10초 세그먼트로 분할

4. **품질 필터링** (1-2분)
   - 품질이 낮은 세그먼트 자동 제거

5. **GPT-SoVITS 학습** (1-4시간)
   - 실제 음성 모델 학습
   - GPU 사용 시 빠름

### 학습 진행 상황 확인

```bash
# 로그 실시간 확인
tail -f logs/training.log

# 또는 별도 터미널에서
watch -n 1 "tail -20 logs/training.log"
```

---

## 고급 설정

### 음성 품질 조정

#### 노이즈가 심한 경우

```yaml
audio_processing:
  noise_reduction: true
  noise_reduction_strength: 1.0  # 기본값: 0.8, 범위: 0-1
```

#### 음량이 일정하지 않은 경우

```yaml
audio_processing:
  normalization: true
  target_loudness: -20  # dB, 낮을수록 조용함
```

#### 무음이 많은 경우

```yaml
audio_processing:
  trim_silence: true
  silence_threshold: -40  # dB, 높을수록 더 많이 제거
```

### 학습 설정 최적화

#### GPU 메모리 부족 시

```yaml
training:
  gpt_sovits:
    batch_size: 2  # 기본값 4에서 줄임
    gradient_accumulation: 2  # 성능 유지
```

#### 빠른 테스트 (저품질)

```yaml
training:
  gpt_sovits:
    epochs: 30
    batch_size: 8
    learning_rate: 0.0002
```

#### 프로덕션 고품질

```yaml
training:
  gpt_sovits:
    epochs: 200
    batch_size: 4
    learning_rate: 0.00005
    warmup_steps: 1000
```

### 데이터 증강 (선택)

더 많은 학습 데이터를 위해:

```yaml
global_settings:
  data_augmentation:
    enabled: true
    pitch_shift: [-2, -1, 0, 1, 2]  # 반음 단위
    speed_change: [0.9, 1.0, 1.1]
    add_noise: false  # 권장하지 않음
```

---

## 여러 캐릭터 학습

### 순차 학습 (안정적)

모든 캐릭터를 하나씩 학습:

```bash
python scripts/train_multiple_characters.py --mode sequential
```

### 병렬 학습 (빠름)

GPU가 여러 개이거나 VRAM이 충분한 경우:

```bash
# 2개 캐릭터 동시 학습
python scripts/train_multiple_characters.py --mode parallel --workers 2

# 3개 캐릭터 동시 학습 (24GB+ VRAM 권장)
python scripts/train_multiple_characters.py --mode parallel --workers 3
```

### 특정 캐릭터만 학습

```bash
python scripts/train_multiple_characters.py --character pororo
```

---

## 모델 테스트

학습 완료 후 모델을 테스트하세요:

### 단일 텍스트 테스트

```bash
python scripts/test_model.py \
    --character pororo \
    --text "안녕하세요! 저는 뽀로로예요!"
```

### 전체 샘플 테스트 (품질 리포트 생성)

```bash
python scripts/test_model.py \
    --character pororo \
    --full-test
```

리포트는 `output/reports/` 디렉토리에 저장됩니다.

### 참조 음성 지정

```bash
python scripts/test_model.py \
    --character pororo \
    --text "오늘은 날씨가 참 좋네요!" \
    --reference ./data/datasets/pororo/audio/pororo_0001.wav
```

---

## 문제 해결

### 자주 발생하는 문제

#### 1. 유튜브 다운로드 실패

**증상**: `ERROR: unable to download video data`

**해결**:
```bash
# yt-dlp 업데이트
pip install --upgrade yt-dlp

# 또는 pytube 사용
# youtube_downloader.py에서 backend 변경
```

#### 2. GPU 메모리 부족

**증상**: `CUDA out of memory`

**해결**:
```yaml
# configs/character_config.yaml
training:
  gpt_sovits:
    batch_size: 2  # 또는 1
```

#### 3. Spleeter 설치 오류

**증상**: `ModuleNotFoundError: No module named 'spleeter'`

**해결**:
```bash
# Spleeter 재설치
pip uninstall spleeter
pip install spleeter==2.4.0

# 또는 Demucs 사용
pip install demucs
```

`configs/character_config.yaml`에서:
```yaml
vocal_separator: "demucs"  # spleeter 대신
```

#### 4. FFmpeg 오류

**증상**: `FileNotFoundError: ffmpeg`

**해결**:

**Windows**:
```bash
# Chocolatey 사용
choco install ffmpeg

# 수동 설치
# 1. https://ffmpeg.org/download.html 에서 다운로드
# 2. 압축 해제
# 3. bin 폴더를 PATH에 추가
```

**Linux**:
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS**:
```bash
brew install ffmpeg
```

#### 5. Whisper 전사 오류

**증상**: 한국어 전사가 정확하지 않음

**해결**:
```python
# gpt_sovits_trainer.py에서 모델 크기 변경
model_size = "large"  # medium 대신
```

또는 수동 라벨링:
```
# data/datasets/pororo/transcriptions.txt
pororo_0001.wav|안녕하세요 저는 뽀로로예요
pororo_0002.wav|오늘은 날씨가 참 좋네요
...
```

---

## 성능 최적화

### 하드웨어별 권장 설정

#### RTX 3060 (12GB VRAM)
```yaml
training:
  gpt_sovits:
    batch_size: 4
    epochs: 100

global_settings:
  parallel_training: false
  max_parallel_jobs: 1
```

#### RTX 3090 / 4090 (24GB VRAM)
```yaml
training:
  gpt_sovits:
    batch_size: 8
    epochs: 150

global_settings:
  parallel_training: true
  max_parallel_jobs: 2
```

#### CPU만 사용
```yaml
training:
  gpt_sovits:
    batch_size: 1
    epochs: 50  # 시간이 오래 걸리므로 줄임
```

`.env`:
```bash
USE_GPU=false
DEVICE=cpu
```

### 학습 시간 단축

1. **GPU 사용**: CPU 대비 10-20배 빠름
2. **배치 크기 증가**: VRAM이 허용하는 한 최대로
3. **에포크 감소**: 테스트는 50 epochs로
4. **병렬 학습**: 여러 캐릭터 동시 학습

### 품질 향상

1. **더 많은 데이터**: 10-15분 권장
2. **깨끗한 음성**: 보컬 분리 품질 중요
3. **다양한 샘플**: 다양한 감정/억양
4. **더 많은 에포크**: 150-200 epochs
5. **데이터 증강**: pitch shift, speed change

---

## 다음 단계

학습이 완료되면:

1. ✅ **모델 테스트**: `scripts/test_model.py`로 품질 확인
2. ✅ **API 통합**: FastAPI 백엔드에 모델 통합
3. ✅ **프론트엔드 연동**: Next.js에서 TTS 서비스 구현
4. ✅ **스토리텔링**: LLM과 연동하여 인터랙티브 동화 생성

자세한 내용은 메인 프로젝트 문서를 참조하세요!

---

**문의사항이 있으시면 이슈를 등록해주세요!**
