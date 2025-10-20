# -*- coding: utf-8 -*-
"""
음성 인식 모듈 (Speech-to-Text)
- OpenAI Whisper (로컬 실행)
"""

import os
import logging
import numpy as np
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class WhisperSTT:
    """
    OpenAI Whisper 음성 인식
    - 완전 무료 (로컬 실행)
    - 고품질 한국어 인식
    """

    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        """
        Args:
            model_size: 모델 크기
                - tiny: 39M, 빠름, 정확도 낮음
                - base: 74M, 균형 (추천 - 테스트용)
                - small: 244M, 느림, 정확도 높음
                - medium: 769M, 매우 느림, 정확도 매우 높음
                - large: 1550M, 최고 품질 (GPU 필수)
            device: 실행 장치 (cuda, cpu, mps)
        """
        try:
            import whisper
            import torch
        except ImportError:
            raise ImportError(
                "whisper 패키지가 필요합니다.\n"
                "설치: pip install openai-whisper torch"
            )

        self.model_size = model_size

        # 디바이스 자동 설정
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"  # Mac M1/M2
            else:
                device = "cpu"

        self.device = device

        logger.info(f"🎤 Whisper 모델 로딩 중... (크기: {model_size}, 장치: {device})")
        self.model = whisper.load_model(model_size, device=device)
        logger.info("✅ Whisper 모델 로드 완료")

    def transcribe_file(
        self,
        audio_path: str,
        language: str = "ko",
        verbose: bool = False
    ) -> dict:
        """
        오디오 파일을 텍스트로 변환

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드 (ko, en, ja, zh 등)
            verbose: 상세 로그 출력

        Returns:
            {
                "text": "변환된 텍스트",
                "language": "ko",
                "segments": [...],  # 타임스탬프별 세그먼트
            }
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        logger.info(f"🎧 음성 인식 중... ({audio_path})")

        result = self.model.transcribe(
            audio_path,
            language=language,
            verbose=verbose,
            fp16=False if self.device == "cpu" else True
        )

        logger.info(f"✅ 인식 완료: {result['text'][:50]}...")
        return result

    def transcribe_audio_data(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: str = "ko"
    ) -> str:
        """
        오디오 데이터 (numpy array)를 텍스트로 변환

        Args:
            audio_data: 오디오 데이터 (numpy array)
            sample_rate: 샘플링 레이트
            language: 언어 코드

        Returns:
            변환된 텍스트
        """
        import tempfile
        from scipy.io.wavfile import write

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name

            # 정규화 (float32 → int16)
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = np.clip(audio_data, -1.0, 1.0)
                audio_data = (audio_data * 32767).astype(np.int16)

            write(tmp_path, sample_rate, audio_data)

        try:
            result = self.transcribe_file(tmp_path, language=language)
            return result["text"]
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def record_and_transcribe(
        self,
        duration: int = 5,
        sample_rate: int = 16000,
        language: str = "ko"
    ) -> str:
        """
        마이크로 녹음하고 즉시 텍스트로 변환

        Args:
            duration: 녹음 시간 (초)
            sample_rate: 샘플링 레이트
            language: 언어 코드

        Returns:
            변환된 텍스트
        """
        try:
            import sounddevice as sd
        except ImportError:
            raise ImportError(
                "sounddevice 패키지가 필요합니다.\n"
                "설치: pip install sounddevice"
            )

        print(f"🎤 {duration}초간 녹음 시작...")

        # 녹음
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()

        print("✅ 녹음 완료! 텍스트 변환 중...")

        # 변환
        text = self.transcribe_audio_data(
            audio_data.flatten(),
            sample_rate=sample_rate,
            language=language
        )

        return text


class GeminiSTT:
    """
    Gemini 음성 인식 (대안)
    - Gemini 1.5 Flash는 오디오 입력 지원
    - 유료지만 품질 평가 등 부가 기능 가능
    """

    def __init__(self):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai 패키지가 필요합니다.\n"
                "설치: pip install google-generativeai"
            )

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        genai.configure(api_key=api_key)
        self.genai = genai

        # Gemini 1.5 Flash (오디오 지원)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        logger.info("✅ Gemini STT 초기화 완료")

    def transcribe_file(self, audio_path: str, language: str = "ko") -> str:
        """
        오디오 파일을 텍스트로 변환 (+ 품질 평가)

        Args:
            audio_path: 오디오 파일 경로
            language: 언어

        Returns:
            변환된 텍스트
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        # 파일 업로드
        audio_file = self.genai.upload_file(audio_path)

        # 프롬프트
        prompt = f"""
        이 오디오 파일을 텍스트로 변환해주세요.

        언어: {language}

        다음 형식으로 응답해주세요:
        [텍스트]
        변환된 텍스트 내용

        [품질]
        - 음질: (좋음/보통/나쁨)
        - 배경 노이즈: (있음/없음)
        - 감정: (기쁨/슬픔/중립 등)
        """

        response = self.model.generate_content([audio_file, prompt])

        return response.text


# 팩토리 함수
def create_stt(method: str = "whisper", **kwargs):
    """
    STT 엔진 생성

    Args:
        method: "whisper" 또는 "gemini"
        **kwargs: 추가 설정

    Returns:
        STT 인스턴스
    """
    if method == "whisper":
        return WhisperSTT(**kwargs)
    elif method == "gemini":
        return GeminiSTT(**kwargs)
    else:
        raise ValueError(f"지원하지 않는 STT 방식: {method}")


# 테스트 코드
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🎤 Whisper STT 테스트\n")

    # Whisper 초기화
    stt = create_stt(method="whisper", model_size="base")

    # 녹음 테스트
    print("\n녹음을 시작하려면 Enter를 누르세요...")
    input()

    text = stt.record_and_transcribe(duration=5)
    print(f"\n✅ 인식 결과: {text}")
