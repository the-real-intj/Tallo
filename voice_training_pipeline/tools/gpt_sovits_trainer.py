"""
GPT-SoVITS 음성 모델 학습 도구

GPT-SoVITS는 1분의 음성 데이터로도 고품질 TTS 모델을 학습할 수 있는
Few-shot Voice Cloning 시스템입니다.

주요 기능:
1. 데이터셋 준비
2. 자동 라벨링 (Whisper 사용)
3. 모델 학습
4. Inference (음성 생성)
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPTSoVITSTrainer:
    """GPT-SoVITS 학습 클래스"""

    def __init__(
        self,
        gpt_sovits_dir: str = "./GPT-SoVITS",
        models_dir: str = "./models/gpt_sovits",
        pretrained_dir: str = "./pretrained_models"
    ):
        """
        Args:
            gpt_sovits_dir: GPT-SoVITS 저장소 경로
            models_dir: 학습된 모델 저장 경로
            pretrained_dir: 사전학습 모델 경로
        """
        self.gpt_sovits_dir = Path(gpt_sovits_dir)
        self.models_dir = Path(models_dir)
        self.pretrained_dir = Path(pretrained_dir)

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.pretrained_dir.mkdir(parents=True, exist_ok=True)

    def setup_gpt_sovits(self, force_reinstall: bool = False):
        """
        GPT-SoVITS 저장소 클론 및 설정

        Args:
            force_reinstall: 기존 설치를 삭제하고 재설치
        """
        if self.gpt_sovits_dir.exists() and force_reinstall:
            logger.info("기존 GPT-SoVITS 제거 중...")
            shutil.rmtree(self.gpt_sovits_dir)

        if not self.gpt_sovits_dir.exists():
            logger.info("GPT-SoVITS 클론 중...")
            cmd = [
                "git", "clone",
                "https://github.com/RVC-Boss/GPT-SoVITS.git",
                str(self.gpt_sovits_dir)
            ]
            subprocess.run(cmd, check=True)
            logger.info("✓ GPT-SoVITS 클론 완료")

            # 의존성 설치
            logger.info("의존성 설치 중...")
            requirements_file = self.gpt_sovits_dir / "requirements.txt"
            if requirements_file.exists():
                subprocess.run(
                    ["pip", "install", "-r", str(requirements_file)],
                    check=True
                )
                logger.info("✓ 의존성 설치 완료")
        else:
            logger.info("✓ GPT-SoVITS이 이미 설치되어 있습니다.")

    def download_pretrained_models(self):
        """
        사전학습된 모델 다운로드

        실제로는 Hugging Face나 모델 저장소에서 다운로드해야 합니다.
        """
        logger.info("사전학습 모델 다운로드...")

        # 모델 다운로드 URL (예시 - 실제 URL로 변경 필요)
        models = {
            "s1bert": "https://huggingface.co/...",  # 실제 URL 필요
            "s2G": "https://huggingface.co/...",      # 실제 URL 필요
        }

        logger.warning("⚠ 사전학습 모델은 수동으로 다운로드해야 합니다.")
        logger.info("다운로드 링크:")
        logger.info("  https://huggingface.co/lj1995/GPT-SoVITS")
        logger.info(f"다운로드 후 {self.pretrained_dir}에 저장하세요.")

    def prepare_dataset(
        self,
        audio_files: List[str],
        character_name: str,
        use_whisper: bool = True
    ) -> Path:
        """
        학습용 데이터셋 준비

        Args:
            audio_files: 오디오 파일 경로 리스트
            character_name: 캐릭터 이름
            use_whisper: Whisper로 자동 라벨링 여부

        Returns:
            데이터셋 디렉토리 경로
        """
        logger.info(f"데이터셋 준비 중: {character_name}")

        # 데이터셋 디렉토리 생성
        dataset_dir = Path(f"./data/datasets/{character_name}")
        dataset_dir.mkdir(parents=True, exist_ok=True)

        audio_dir = dataset_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        # 오디오 파일 복사
        for idx, audio_file in enumerate(audio_files):
            src = Path(audio_file)
            dst = audio_dir / f"{character_name}_{idx:04d}.wav"
            shutil.copy2(src, dst)

        logger.info(f"✓ {len(audio_files)}개 파일 복사 완료")

        # Whisper로 전사 (transcription)
        if use_whisper:
            self._transcribe_with_whisper(audio_dir, dataset_dir)

        return dataset_dir

    def _transcribe_with_whisper(
        self,
        audio_dir: Path,
        dataset_dir: Path,
        model_size: str = "medium"
    ):
        """
        Whisper로 음성 전사

        Args:
            audio_dir: 오디오 디렉토리
            dataset_dir: 데이터셋 디렉토리
            model_size: Whisper 모델 크기 (tiny, base, small, medium, large)
        """
        try:
            import whisper

            logger.info(f"Whisper 모델 로드 중: {model_size}")
            model = whisper.load_model(model_size)

            # 전사 파일 생성
            transcription_file = dataset_dir / "transcriptions.txt"

            with open(transcription_file, 'w', encoding='utf-8') as f:
                for audio_file in sorted(audio_dir.glob("*.wav")):
                    logger.info(f"전사 중: {audio_file.name}")

                    result = model.transcribe(
                        str(audio_file),
                        language="ko",  # 한국어
                        fp16=False
                    )

                    text = result["text"].strip()

                    # 형식: audio_path|text
                    line = f"{audio_file.name}|{text}\n"
                    f.write(line)

                    logger.info(f"  → {text}")

            logger.info(f"✓ 전사 완료: {transcription_file}")

        except ImportError:
            logger.error("Whisper가 설치되지 않았습니다.")
            logger.info("설치: pip install openai-whisper")
        except Exception as e:
            logger.error(f"전사 실패: {e}")

    def create_config(
        self,
        character_name: str,
        dataset_dir: Path,
        config: Dict
    ) -> Path:
        """
        학습 설정 파일 생성

        Args:
            character_name: 캐릭터 이름
            dataset_dir: 데이터셋 디렉토리
            config: 학습 설정

        Returns:
            설정 파일 경로
        """
        config_template = {
            "train": {
                "log_interval": 100,
                "eval_interval": 500,
                "save_interval": config.get('save_interval', 1000),
                "batch_size": config.get('batch_size', 4),
                "learning_rate": config.get('learning_rate', 0.0001),
                "epochs": config.get('epochs', 100),
                "num_workers": 4,
            },
            "data": {
                "training_files": str(dataset_dir / "transcriptions.txt"),
                "sampling_rate": 22050,
                "filter_length": 1024,
                "hop_length": 256,
                "win_length": 1024,
            },
            "model": {
                "inter_channels": 192,
                "hidden_channels": 192,
                "filter_channels": 768,
                "n_heads": 2,
                "n_layers": 6,
                "kernel_size": 3,
            }
        }

        config_file = self.models_dir / f"{character_name}_config.json"

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_template, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ 설정 파일 생성: {config_file}")
        return config_file

    def train(
        self,
        character_name: str,
        dataset_dir: Path,
        config_file: Path,
        use_gpu: bool = True
    ) -> Path:
        """
        모델 학습 실행

        Args:
            character_name: 캐릭터 이름
            dataset_dir: 데이터셋 디렉토리
            config_file: 설정 파일
            use_gpu: GPU 사용 여부

        Returns:
            학습된 모델 경로
        """
        logger.info(f"=== 학습 시작: {character_name} ===")

        # 출력 디렉토리
        output_dir = self.models_dir / character_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # 학습 명령 (GPT-SoVITS의 실제 스크립트에 맞춰 수정 필요)
        # 이것은 예시입니다 - 실제 GPT-SoVITS 사용법에 맞춰 조정하세요
        train_script = self.gpt_sovits_dir / "GPT_SoVITS" / "s1_train.py"

        if not train_script.exists():
            logger.warning(f"⚠ 학습 스크립트를 찾을 수 없습니다: {train_script}")
            logger.info("GPT-SoVITS 문서를 참고하여 수동으로 학습을 진행하세요.")
            logger.info("https://github.com/RVC-Boss/GPT-SoVITS")
            return output_dir

        cmd = [
            "python",
            str(train_script),
            "--config", str(config_file),
            "--output_dir", str(output_dir),
        ]

        if use_gpu:
            cmd.extend(["--device", "cuda"])

        try:
            logger.info(f"명령 실행: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            logger.info(f"✓ 학습 완료: {output_dir}")
        except subprocess.CalledProcessError as e:
            logger.error(f"학습 실패: {e}")
        except FileNotFoundError:
            logger.error("Python을 찾을 수 없습니다.")

        return output_dir

    def inference(
        self,
        model_dir: Path,
        text: str,
        reference_audio: str,
        output_path: str
    ) -> Optional[str]:
        """
        학습된 모델로 음성 생성

        Args:
            model_dir: 학습된 모델 디렉토리
            text: 생성할 텍스트
            reference_audio: 참조 음성 (5초 이상)
            output_path: 출력 파일 경로

        Returns:
            생성된 음성 파일 경로
        """
        logger.info(f"음성 생성 중: '{text}'")

        # Inference 스크립트 (실제 GPT-SoVITS 사용법에 맞춰 수정)
        inference_script = self.gpt_sovits_dir / "GPT_SoVITS" / "inference.py"

        if not inference_script.exists():
            logger.warning("⚠ Inference 스크립트를 찾을 수 없습니다.")
            logger.info("GPT-SoVITS API를 사용하거나 WebUI를 통해 생성하세요.")
            return None

        cmd = [
            "python",
            str(inference_script),
            "--model_dir", str(model_dir),
            "--text", text,
            "--reference_audio", reference_audio,
            "--output", output_path,
        ]

        try:
            subprocess.run(cmd, check=True)
            logger.info(f"✓ 음성 생성 완료: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"음성 생성 실패: {e}")
            return None


class TrainingPipeline:
    """전체 학습 파이프라인 통합"""

    def __init__(self):
        self.trainer = GPTSoVITSTrainer()

    def run_full_pipeline(
        self,
        character_name: str,
        audio_files: List[str],
        training_config: Dict
    ) -> Path:
        """
        전체 파이프라인 실행

        Args:
            character_name: 캐릭터 이름
            audio_files: 전처리된 오디오 파일 리스트
            training_config: 학습 설정

        Returns:
            학습된 모델 경로
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"학습 파이프라인 시작: {character_name}")
        logger.info(f"{'='*60}\n")

        # 1. GPT-SoVITS 설정
        self.trainer.setup_gpt_sovits()

        # 2. 데이터셋 준비
        dataset_dir = self.trainer.prepare_dataset(
            audio_files,
            character_name,
            use_whisper=True
        )

        # 3. 설정 파일 생성
        config_file = self.trainer.create_config(
            character_name,
            dataset_dir,
            training_config
        )

        # 4. 학습 실행
        model_dir = self.trainer.train(
            character_name,
            dataset_dir,
            config_file,
            use_gpu=True
        )

        logger.info(f"\n{'='*60}")
        logger.info(f"학습 파이프라인 완료!")
        logger.info(f"모델 경로: {model_dir}")
        logger.info(f"{'='*60}\n")

        return model_dir


def main():
    """사용 예제"""

    # 파이프라인 초기화
    pipeline = TrainingPipeline()

    # 학습 설정
    config = {
        'batch_size': 4,
        'learning_rate': 0.0001,
        'epochs': 100,
        'save_interval': 1000,
    }

    # 전처리된 오디오 파일 리스트
    # audio_files = [
    #     "./data/processed/pororo_segment_0000.wav",
    #     "./data/processed/pororo_segment_0001.wav",
    #     # ...
    # ]

    # 학습 실행
    # model_dir = pipeline.run_full_pipeline(
    #     character_name="pororo",
    #     audio_files=audio_files,
    #     training_config=config
    # )

    print("GPT-SoVITS 트레이너 준비 완료!")


if __name__ == "__main__":
    main()
