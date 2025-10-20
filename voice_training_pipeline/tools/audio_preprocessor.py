"""
음성 전처리 파이프라인

주요 기능:
1. 노이즈 제거
2. 보컬 분리 (배경음악 제거)
3. 무음 구간 제거
4. 정규화
5. 세그먼트 분할
6. 품질 평가
"""

import os
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging
from pydub import AudioSegment
from pydub.silence import split_on_silence
import noisereduce as nr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """음성 전처리 클래스"""

    def __init__(
        self,
        sample_rate: int = 22050,
        target_db: float = -20.0,
        min_silence_len: int = 500,
        silence_thresh: int = -40,
    ):
        """
        Args:
            sample_rate: 타겟 샘플링 레이트
            target_db: 타겟 음량 (dB)
            min_silence_len: 무음으로 간주할 최소 길이 (ms)
            silence_thresh: 무음 임계값 (dB)
        """
        self.sample_rate = sample_rate
        self.target_db = target_db
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh

    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        오디오 파일 로드

        Args:
            audio_path: 오디오 파일 경로

        Returns:
            (오디오 데이터, 샘플레이트)
        """
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            logger.info(f"오디오 로드 완료: {audio_path} ({len(y)/sr:.2f}초)")
            return y, sr
        except Exception as e:
            logger.error(f"오디오 로드 실패: {e}")
            raise

    def reduce_noise(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """
        노이즈 감소

        Args:
            audio_data: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            노이즈가 제거된 오디오
        """
        try:
            logger.info("노이즈 제거 중...")

            # noisereduce 사용
            reduced_noise = nr.reduce_noise(
                y=audio_data,
                sr=sr,
                stationary=True,
                prop_decrease=0.8
            )

            logger.info("✓ 노이즈 제거 완료")
            return reduced_noise

        except Exception as e:
            logger.error(f"노이즈 제거 실패: {e}")
            return audio_data

    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        오디오 정규화

        Args:
            audio_data: 오디오 데이터

        Returns:
            정규화된 오디오
        """
        try:
            logger.info("오디오 정규화 중...")

            # Peak normalization
            normalized = librosa.util.normalize(audio_data)

            logger.info("✓ 정규화 완료")
            return normalized

        except Exception as e:
            logger.error(f"정규화 실패: {e}")
            return audio_data

    def trim_silence(
        self,
        audio_data: np.ndarray,
        sr: int,
        top_db: int = 20
    ) -> np.ndarray:
        """
        무음 구간 제거

        Args:
            audio_data: 오디오 데이터
            sr: 샘플링 레이트
            top_db: 무음 임계값 (dB)

        Returns:
            무음이 제거된 오디오
        """
        try:
            logger.info("무음 구간 제거 중...")

            # librosa를 사용한 무음 구간 탐지 및 제거
            intervals = librosa.effects.split(audio_data, top_db=top_db)

            # 무음 구간 제거
            trimmed_parts = []
            for start, end in intervals:
                trimmed_parts.append(audio_data[start:end])

            if trimmed_parts:
                trimmed_audio = np.concatenate(trimmed_parts)
                original_duration = len(audio_data) / sr
                trimmed_duration = len(trimmed_audio) / sr
                logger.info(f"✓ 무음 제거 완료: {original_duration:.2f}초 → {trimmed_duration:.2f}초")
                return trimmed_audio
            else:
                logger.warning("무음 구간 탐지 실패, 원본 반환")
                return audio_data

        except Exception as e:
            logger.error(f"무음 제거 실패: {e}")
            return audio_data

    def split_into_segments(
        self,
        audio_data: np.ndarray,
        sr: int,
        min_length: float = 3.0,
        max_length: float = 10.0,
        overlap: float = 0.5
    ) -> List[np.ndarray]:
        """
        오디오를 세그먼트로 분할

        Args:
            audio_data: 오디오 데이터
            sr: 샘플링 레이트
            min_length: 최소 세그먼트 길이 (초)
            max_length: 최대 세그먼트 길이 (초)
            overlap: 세그먼트 간 겹침 (초)

        Returns:
            세그먼트 리스트
        """
        try:
            logger.info("세그먼트 분할 중...")

            segments = []
            total_duration = len(audio_data) / sr

            # 세그먼트 크기 (샘플 수)
            max_segment_samples = int(max_length * sr)
            overlap_samples = int(overlap * sr)
            step_size = max_segment_samples - overlap_samples

            # 슬라이딩 윈도우로 분할
            for start in range(0, len(audio_data) - int(min_length * sr), step_size):
                end = min(start + max_segment_samples, len(audio_data))
                segment = audio_data[start:end]

                # 최소 길이 체크
                segment_duration = len(segment) / sr
                if segment_duration >= min_length:
                    segments.append(segment)

            logger.info(f"✓ 세그먼트 분할 완료: {len(segments)}개 세그먼트")
            return segments

        except Exception as e:
            logger.error(f"세그먼트 분할 실패: {e}")
            return []

    def assess_quality(self, audio_data: np.ndarray, sr: int) -> Dict[str, float]:
        """
        오디오 품질 평가

        Args:
            audio_data: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            품질 지표 딕셔너리
        """
        try:
            # RMS (Root Mean Square) - 음량 측정
            rms = librosa.feature.rms(y=audio_data)[0]
            avg_rms = np.mean(rms)

            # Zero Crossing Rate - 노이즈 지표
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            avg_zcr = np.mean(zcr)

            # Spectral Centroid - 음색 밝기
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0]
            avg_spectral_centroid = np.mean(spectral_centroid)

            # SNR 추정 (간이 방식)
            signal_power = np.mean(audio_data ** 2)
            noise_estimate = np.mean(np.abs(audio_data[:int(0.1 * sr)])) ** 2
            snr = 10 * np.log10(signal_power / (noise_estimate + 1e-10))

            quality_score = self._calculate_quality_score(
                avg_rms, avg_zcr, snr
            )

            return {
                'rms': float(avg_rms),
                'zcr': float(avg_zcr),
                'spectral_centroid': float(avg_spectral_centroid),
                'snr': float(snr),
                'quality_score': quality_score
            }

        except Exception as e:
            logger.error(f"품질 평가 실패: {e}")
            return {'quality_score': 0.0}

    def _calculate_quality_score(
        self,
        rms: float,
        zcr: float,
        snr: float
    ) -> float:
        """
        품질 점수 계산 (0-1 사이)

        Args:
            rms: RMS 값
            zcr: Zero Crossing Rate
            snr: Signal-to-Noise Ratio

        Returns:
            품질 점수
        """
        # 간단한 휴리스틱 기반 점수
        score = 0.0

        # RMS 기반 (적절한 음량)
        if 0.01 < rms < 0.3:
            score += 0.3

        # ZCR 기반 (낮을수록 깨끗)
        if zcr < 0.1:
            score += 0.3

        # SNR 기반
        if snr > 20:
            score += 0.4
        elif snr > 10:
            score += 0.2

        return min(score, 1.0)

    def process_audio(
        self,
        input_path: str,
        output_dir: str,
        character_name: str,
        enable_noise_reduction: bool = True,
        enable_normalization: bool = True,
        enable_trim_silence: bool = True,
        segment_config: Optional[Dict] = None
    ) -> List[str]:
        """
        전체 오디오 전처리 파이프라인

        Args:
            input_path: 입력 오디오 파일 경로
            output_dir: 출력 디렉토리
            character_name: 캐릭터 이름
            enable_noise_reduction: 노이즈 제거 활성화
            enable_normalization: 정규화 활성화
            enable_trim_silence: 무음 제거 활성화
            segment_config: 세그먼트 설정 (min_length, max_length, overlap)

        Returns:
            처리된 파일 경로 리스트
        """
        logger.info(f"=== 오디오 전처리 시작: {input_path} ===")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. 오디오 로드
        audio_data, sr = self.load_audio(input_path)

        # 2. 노이즈 제거
        if enable_noise_reduction:
            audio_data = self.reduce_noise(audio_data, sr)

        # 3. 무음 제거
        if enable_trim_silence:
            audio_data = self.trim_silence(audio_data, sr)

        # 4. 정규화
        if enable_normalization:
            audio_data = self.normalize_audio(audio_data)

        # 5. 품질 평가
        quality = self.assess_quality(audio_data, sr)
        logger.info(f"품질 점수: {quality['quality_score']:.2f}")

        # 6. 세그먼트 분할
        if segment_config:
            segments = self.split_into_segments(
                audio_data,
                sr,
                min_length=segment_config.get('min_length', 3.0),
                max_length=segment_config.get('max_length', 10.0),
                overlap=segment_config.get('overlap', 0.5)
            )
        else:
            segments = [audio_data]

        # 7. 세그먼트 저장
        output_files = []
        for idx, segment in enumerate(segments):
            output_filename = f"{character_name}_segment_{idx:04d}.wav"
            output_path = output_dir / output_filename

            # 저장
            sf.write(str(output_path), segment, sr)
            logger.info(f"저장: {output_path} ({len(segment)/sr:.2f}초)")

            output_files.append(str(output_path))

        logger.info(f"=== 전처리 완료: {len(output_files)}개 파일 생성 ===")
        return output_files

    def batch_process(
        self,
        input_files: List[str],
        output_dir: str,
        character_name: str,
        **kwargs
    ) -> List[str]:
        """
        여러 파일 배치 처리

        Args:
            input_files: 입력 파일 경로 리스트
            output_dir: 출력 디렉토리
            character_name: 캐릭터 이름
            **kwargs: process_audio에 전달할 추가 인자

        Returns:
            처리된 파일 경로 리스트
        """
        all_output_files = []

        for input_file in input_files:
            logger.info(f"\n처리 중: {input_file}")
            output_files = self.process_audio(
                input_file,
                output_dir,
                character_name,
                **kwargs
            )
            all_output_files.extend(output_files)

        return all_output_files


def main():
    """테스트 예제"""

    preprocessor = AudioPreprocessor(
        sample_rate=22050,
        target_db=-20.0
    )

    # 단일 파일 처리 예제
    # output_files = preprocessor.process_audio(
    #     input_path="./data/raw/pororo_20240119_120000.wav",
    #     output_dir="./data/processed",
    #     character_name="pororo",
    #     enable_noise_reduction=True,
    #     enable_normalization=True,
    #     enable_trim_silence=True,
    #     segment_config={
    #         'min_length': 3.0,
    #         'max_length': 10.0,
    #         'overlap': 0.5
    #     }
    # )

    print("전처리기 준비 완료!")


if __name__ == "__main__":
    main()
