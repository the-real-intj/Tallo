"""
학습된 음성 모델 테스트 및 검증 도구

주요 기능:
1. 텍스트로 음성 생성 테스트
2. 음성 품질 평가
3. 여러 샘플 생성
4. A/B 테스트용 샘플 생성
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.gpt_sovits_trainer import GPTSoVITSTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTester:
    """모델 테스트 클래스"""

    def __init__(self, models_dir: str = "./models/gpt_sovits"):
        self.models_dir = Path(models_dir)
        self.trainer = GPTSoVITSTrainer()

        # 테스트용 텍스트 샘플
        self.test_texts = {
            'short': "안녕하세요!",
            'medium': "오늘은 날씨가 참 좋네요. 우리 함께 놀러 갈까요?",
            'long': "옛날 옛적에 아름다운 숲 속에 작은 토끼가 살고 있었어요. "
                    "토끼는 매일 친구들과 함께 뛰어 놀며 즐거운 시간을 보냈답니다.",
            'question': "오늘 뭐 하고 놀까?",
            'excited': "와! 정말 신난다! 우와우와!",
            'sad': "어떡하지... 걱정이네요...",
        }

    def list_available_models(self) -> List[str]:
        """사용 가능한 모델 목록"""
        if not self.models_dir.exists():
            logger.warning(f"모델 디렉토리가 없습니다: {self.models_dir}")
            return []

        models = [d.name for d in self.models_dir.iterdir() if d.is_dir()]
        return models

    def test_single_generation(
        self,
        character_id: str,
        text: str,
        reference_audio: Optional[str] = None,
        output_dir: str = "./output/audio"
    ) -> Optional[str]:
        """
        단일 음성 생성 테스트

        Args:
            character_id: 캐릭터 ID
            text: 생성할 텍스트
            reference_audio: 참조 음성 (없으면 학습 데이터 중 하나 사용)
            output_dir: 출력 디렉토리

        Returns:
            생성된 파일 경로
        """
        model_dir = self.models_dir / character_id

        if not model_dir.exists():
            logger.error(f"모델을 찾을 수 없습니다: {model_dir}")
            return None

        # 참조 음성이 없으면 학습 데이터에서 찾기
        if not reference_audio:
            dataset_dir = Path(f"./data/datasets/{character_id}/audio")
            if dataset_dir.exists():
                audio_files = list(dataset_dir.glob("*.wav"))
                if audio_files:
                    reference_audio = str(audio_files[0])
                    logger.info(f"참조 음성: {reference_audio}")

        if not reference_audio:
            logger.error("참조 음성이 필요합니다.")
            return None

        # 출력 경로
        output_dir = Path(output_dir) / character_id
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"test_{timestamp}.wav"

        # 음성 생성
        logger.info(f"음성 생성 중: '{text}'")

        result = self.trainer.inference(
            model_dir=model_dir,
            text=text,
            reference_audio=reference_audio,
            output_path=str(output_path)
        )

        return result

    def test_multiple_samples(
        self,
        character_id: str,
        reference_audio: Optional[str] = None
    ) -> Dict[str, str]:
        """
        여러 샘플 텍스트로 테스트

        Args:
            character_id: 캐릭터 ID
            reference_audio: 참조 음성

        Returns:
            {텍스트 타입: 생성된 파일 경로}
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"다중 샘플 테스트: {character_id}")
        logger.info(f"{'='*70}\n")

        results = {}

        for test_type, text in self.test_texts.items():
            logger.info(f"\n[{test_type}] 생성 중...")

            output_path = self.test_single_generation(
                character_id,
                text,
                reference_audio
            )

            if output_path:
                results[test_type] = output_path
                logger.info(f"✓ 생성 완료: {output_path}")
            else:
                logger.error(f"✗ 생성 실패: {test_type}")

        return results

    def evaluate_quality(self, audio_path: str) -> Dict[str, float]:
        """
        생성된 음성 품질 평가

        Args:
            audio_path: 오디오 파일 경로

        Returns:
            품질 지표
        """
        from tools.audio_preprocessor import AudioPreprocessor

        preprocessor = AudioPreprocessor()

        try:
            audio_data, sr = preprocessor.load_audio(audio_path)
            quality = preprocessor.assess_quality(audio_data, sr)

            logger.info(f"\n품질 평가: {Path(audio_path).name}")
            logger.info(f"  RMS: {quality['rms']:.4f}")
            logger.info(f"  ZCR: {quality['zcr']:.4f}")
            logger.info(f"  SNR: {quality['snr']:.2f} dB")
            logger.info(f"  품질 점수: {quality['quality_score']:.2f}")

            return quality

        except Exception as e:
            logger.error(f"품질 평가 실패: {e}")
            return {}

    def create_comparison_report(
        self,
        character_id: str,
        test_results: Dict[str, str]
    ):
        """
        테스트 결과 비교 리포트 생성

        Args:
            character_id: 캐릭터 ID
            test_results: 테스트 결과
        """
        report_dir = Path("./output/reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"test_report_{character_id}_{timestamp}.json"

        report = {
            'character_id': character_id,
            'timestamp': timestamp,
            'samples': {}
        }

        for test_type, audio_path in test_results.items():
            quality = self.evaluate_quality(audio_path)

            report['samples'][test_type] = {
                'text': self.test_texts[test_type],
                'audio_path': audio_path,
                'quality': quality
            }

        # 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✓ 테스트 리포트 저장: {report_file}")

        # 요약 출력
        self._print_report_summary(report)

    def _print_report_summary(self, report: Dict):
        """리포트 요약 출력"""
        logger.info(f"\n{'='*70}")
        logger.info("테스트 결과 요약")
        logger.info(f"{'='*70}")

        logger.info(f"\n캐릭터: {report['character_id']}")
        logger.info(f"테스트 시간: {report['timestamp']}")

        logger.info(f"\n{'샘플':<15} {'품질점수':<12} {'SNR (dB)':<12} {'파일'}")
        logger.info("-" * 70)

        for test_type, data in report['samples'].items():
            quality_score = data['quality'].get('quality_score', 0)
            snr = data['quality'].get('snr', 0)
            file_name = Path(data['audio_path']).name

            logger.info(
                f"{test_type:<15} "
                f"{quality_score:>6.2f}        "
                f"{snr:>6.2f}        "
                f"{file_name}"
            )

        logger.info(f"{'='*70}\n")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="음성 모델 테스트")
    parser.add_argument(
        '--character',
        required=True,
        help='테스트할 캐릭터 ID'
    )
    parser.add_argument(
        '--text',
        help='생성할 텍스트 (지정하지 않으면 샘플 텍스트 사용)'
    )
    parser.add_argument(
        '--reference',
        help='참조 음성 파일 경로'
    )
    parser.add_argument(
        '--full-test',
        action='store_true',
        help='전체 샘플 테스트 실행'
    )

    args = parser.parse_args()

    # 테스터 초기화
    tester = ModelTester()

    # 사용 가능한 모델 확인
    available_models = tester.list_available_models()
    logger.info(f"사용 가능한 모델: {available_models}")

    if args.character not in available_models:
        logger.error(f"모델을 찾을 수 없습니다: {args.character}")
        logger.info(f"사용 가능한 모델: {', '.join(available_models)}")
        return

    # 테스트 실행
    if args.full_test:
        # 전체 샘플 테스트
        results = tester.test_multiple_samples(
            args.character,
            args.reference
        )

        # 리포트 생성
        tester.create_comparison_report(args.character, results)

    elif args.text:
        # 단일 텍스트 테스트
        output_path = tester.test_single_generation(
            args.character,
            args.text,
            args.reference
        )

        if output_path:
            logger.info(f"\n✓ 음성 생성 완료: {output_path}")

            # 품질 평가
            tester.evaluate_quality(output_path)

    else:
        logger.error("--text 또는 --full-test 옵션을 지정하세요.")


if __name__ == "__main__":
    main()
