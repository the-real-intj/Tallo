"""
보컬 분리 도구 - 배경음악/효과음 제거

지원 방식:
1. Spleeter (빠르고 효과적)
2. Demucs (더 높은 품질, 느림)
"""

import os
import subprocess
from pathlib import Path
from typing import Literal, Optional
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VocalSeparator:
    """보컬 분리 클래스"""

    def __init__(
        self,
        method: Literal["spleeter", "demucs"] = "spleeter",
        output_dir: str = "./data/vocals"
    ):
        """
        Args:
            method: 분리 방법 (spleeter 또는 demucs)
            output_dir: 출력 디렉토리
        """
        self.method = method
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Spleeter 사용 가능 여부 확인
        if method == "spleeter":
            try:
                subprocess.run(
                    ["spleeter", "--version"],
                    check=True,
                    capture_output=True
                )
                logger.info("✓ Spleeter 사용 가능")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("⚠ Spleeter가 설치되지 않았습니다.")
                logger.info("설치: pip install spleeter")

    def separate_vocals_spleeter(
        self,
        audio_path: str,
        stems: Literal["2stems", "4stems", "5stems"] = "2stems"
    ) -> Optional[str]:
        """
        Spleeter로 보컬 분리

        Args:
            audio_path: 입력 오디오 파일
            stems: 분리 모드
                - 2stems: vocals, accompaniment
                - 4stems: vocals, drums, bass, other
                - 5stems: vocals, drums, bass, piano, other

        Returns:
            분리된 보컬 파일 경로
        """
        try:
            logger.info(f"Spleeter 보컬 분리 시작: {audio_path}")

            # Spleeter 실행
            cmd = [
                "spleeter",
                "separate",
                "-p", f"spleeter:{stems}",
                "-o", str(self.output_dir),
                audio_path
            ]

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            # 분리된 보컬 파일 찾기
            audio_name = Path(audio_path).stem
            vocals_path = self.output_dir / audio_name / "vocals.wav"

            if vocals_path.exists():
                logger.info(f"✓ 보컬 분리 완료: {vocals_path}")
                return str(vocals_path)
            else:
                logger.error("보컬 파일을 찾을 수 없습니다.")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Spleeter 실행 실패: {e}")
            logger.error(f"stderr: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"보컬 분리 중 오류: {e}")
            return None

    def separate_vocals_demucs(
        self,
        audio_path: str,
        model: str = "htdemucs"
    ) -> Optional[str]:
        """
        Demucs로 보컬 분리 (더 높은 품질)

        Args:
            audio_path: 입력 오디오 파일
            model: Demucs 모델 (htdemucs, mdx, mdx_extra)

        Returns:
            분리된 보컬 파일 경로
        """
        try:
            logger.info(f"Demucs 보컬 분리 시작: {audio_path}")

            # Demucs 실행
            cmd = [
                "demucs",
                "-n", model,
                "-o", str(self.output_dir),
                audio_path
            ]

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            # 분리된 보컬 파일 찾기
            audio_name = Path(audio_path).stem
            vocals_path = self.output_dir / model / audio_name / "vocals.wav"

            if vocals_path.exists():
                logger.info(f"✓ 보컬 분리 완료: {vocals_path}")
                return str(vocals_path)
            else:
                logger.error("보컬 파일을 찾을 수 없습니다.")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Demucs 실행 실패: {e}")
            return None
        except FileNotFoundError:
            logger.error("Demucs가 설치되지 않았습니다.")
            logger.info("설치: pip install demucs")
            return None
        except Exception as e:
            logger.error(f"보컬 분리 중 오류: {e}")
            return None

    def separate(self, audio_path: str, **kwargs) -> Optional[str]:
        """
        설정된 방법으로 보컬 분리

        Args:
            audio_path: 입력 오디오 파일
            **kwargs: 각 방법별 추가 인자

        Returns:
            분리된 보컬 파일 경로
        """
        if self.method == "spleeter":
            return self.separate_vocals_spleeter(audio_path, **kwargs)
        elif self.method == "demucs":
            return self.separate_vocals_demucs(audio_path, **kwargs)
        else:
            logger.error(f"지원하지 않는 방법: {self.method}")
            return None

    def batch_separate(
        self,
        audio_files: list[str],
        **kwargs
    ) -> list[str]:
        """
        여러 파일 배치 처리

        Args:
            audio_files: 입력 오디오 파일 리스트
            **kwargs: separate 메서드에 전달할 인자

        Returns:
            분리된 보컬 파일 경로 리스트
        """
        vocals_files = []

        for audio_file in audio_files:
            logger.info(f"\n처리 중: {audio_file}")
            vocals_path = self.separate(audio_file, **kwargs)

            if vocals_path:
                vocals_files.append(vocals_path)

        logger.info(f"\n배치 분리 완료: {len(vocals_files)}/{len(audio_files)} 성공")
        return vocals_files

    def organize_vocals(self, character_name: str):
        """
        분리된 보컬을 캐릭터별로 정리

        Args:
            character_name: 캐릭터 이름
        """
        character_dir = self.output_dir / character_name
        character_dir.mkdir(parents=True, exist_ok=True)

        # vocals.wav 파일들을 찾아서 이동
        for vocals_file in self.output_dir.rglob("vocals.wav"):
            if character_name.lower() in str(vocals_file.parent).lower():
                # 파일명 생성
                parent_name = vocals_file.parent.name
                new_name = f"{parent_name}_vocals.wav"
                dest_path = character_dir / new_name

                # 이동
                shutil.copy2(vocals_file, dest_path)
                logger.info(f"정리: {vocals_file} → {dest_path}")


class SimplifiedVocalSeparator:
    """
    간단한 보컬 분리 (Python만 사용)
    외부 도구 없이 사용 가능하지만 품질은 낮음
    """

    def __init__(self, output_dir: str = "./data/vocals"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def separate_by_frequency(
        self,
        audio_path: str,
        low_cutoff: int = 80,
        high_cutoff: int = 8000
    ) -> str:
        """
        주파수 필터링으로 간단한 보컬 추출
        (품질이 낮으므로 테스트용으로만 사용)

        Args:
            audio_path: 입력 오디오
            low_cutoff: 저역 차단 주파수
            high_cutoff: 고역 차단 주파수

        Returns:
            필터링된 파일 경로
        """
        import librosa
        import soundfile as sf
        import scipy.signal as signal

        logger.info("간단한 주파수 필터링 방식 (테스트용)")

        # 오디오 로드
        y, sr = librosa.load(audio_path, sr=None)

        # 밴드패스 필터
        nyquist = sr / 2
        low = low_cutoff / nyquist
        high = high_cutoff / nyquist

        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, y)

        # 저장
        output_path = self.output_dir / f"{Path(audio_path).stem}_filtered.wav"
        sf.write(str(output_path), filtered, sr)

        logger.info(f"✓ 필터링 완료: {output_path}")
        return str(output_path)


def main():
    """사용 예제"""

    # Spleeter 사용
    separator = VocalSeparator(
        method="spleeter",
        output_dir="./data/vocals"
    )

    # 단일 파일 처리
    # vocals_path = separator.separate(
    #     "./data/raw/pororo_20240119.wav",
    #     stems="2stems"
    # )

    # 배치 처리
    # audio_files = [
    #     "./data/raw/pororo_1.wav",
    #     "./data/raw/pororo_2.wav",
    # ]
    # vocals_files = separator.batch_separate(audio_files, stems="2stems")

    print("보컬 분리기 준비 완료!")


if __name__ == "__main__":
    main()
