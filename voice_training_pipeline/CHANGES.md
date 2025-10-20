# 📝 폴더명 변경 내역

## 변경 일시
2025-01-19

## 변경 사항

### 1. 메인 디렉토리명 변경
- **이전**: `voice-training-pipeline/`
- **변경 후**: `voice_training_pipeline/`

### 2. 하위 디렉토리명 변경
- **이전**: `models/gpt-sovits/`
- **변경 후**: `models/gpt_sovits/`

### 3. 영향받은 파일들

다음 파일들에서 경로 참조가 자동으로 업데이트되었습니다:

#### Python 파일
- `tools/gpt_sovits_trainer.py`
- `scripts/train_multiple_characters.py`
- `scripts/test_model.py`
- `scripts/check_environment.py`
- `scripts/quick_start.py`

#### 문서 파일
- `README.md`
- `USAGE_GUIDE.md`
- `PIPELINE_GUIDE.md`

#### 설정 파일
- `.env`
- `.env.example` (새로 생성됨)

### 4. 변경 이유
- Python 패키지 네이밍 컨벤션 준수 (하이픈 대신 언더스코어 사용)
- import 시 문제 방지
- 일관된 네이밍 스타일 유지

### 5. 사용자 액션 필요 사항

#### 기존 사용자
기존에 이 프로젝트를 사용하고 계셨다면:

1. **디렉토리 경로 업데이트**
   ```bash
   # 기존 작업 디렉토리가 있다면
   cd /path/to/old/voice-training-pipeline
   cd ..
   mv voice-training-pipeline voice_training_pipeline
   ```

2. **환경 변수 업데이트**
   `.env` 파일에서 다음 항목 확인:
   ```bash
   GPT_SOVITS_DIR=./models/gpt_sovits  # 변경됨
   ```

3. **스크립트 경로 업데이트**
   만약 외부에서 이 스크립트를 import하고 있다면:
   ```python
   # 이전
   from voice-training-pipeline.tools import ...

   # 변경 후
   from voice_training_pipeline.tools import ...
   ```

#### 새 사용자
새로 시작하는 경우 변경 사항 없이 바로 사용 가능합니다:

```bash
git clone <repo-url>
cd voice_training_pipeline
pip install -r requirements.txt
```

### 6. 확인 방법

변경이 올바르게 적용되었는지 확인:

```bash
# 1. 디렉토리 구조 확인
ls -la
# voice_training_pipeline/ 폴더가 있어야 함

# 2. models 하위 확인
ls -la models/
# gpt_sovits/ 폴더가 있어야 함

# 3. 환경 체크 스크립트 실행
python scripts/check_environment.py
```

### 7. 문제 발생 시

만약 경로 관련 오류가 발생한다면:

1. **Python 경로 오류**
   ```python
   # 확인
   import sys
   print(sys.path)

   # 필요시 추가
   sys.path.insert(0, '/path/to/voice_training_pipeline')
   ```

2. **파일 경로 오류**
   - 모든 스크립트는 상대 경로를 사용하므로 프로젝트 루트에서 실행
   ```bash
   cd voice_training_pipeline
   python scripts/train_multiple_characters.py
   ```

3. **import 오류**
   - 프로젝트 루트를 PYTHONPATH에 추가
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/voice_training_pipeline"
   ```

## 호환성

- ✅ Windows, Linux, macOS 모두 동일하게 작동
- ✅ Python 3.9+ 모두 호환
- ✅ 기존 학습된 모델 영향 없음 (경로만 변경)

## 추가 변경 사항

- `.env.example` 파일 새로 추가 (템플릿용)
- 모든 문서의 예제 코드 업데이트

---

**문의사항이 있으시면 이슈를 등록해주세요.**
