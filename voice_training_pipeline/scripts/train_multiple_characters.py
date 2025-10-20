"""
여러 캐릭터 배치 학습 스크립트

YAML 설정 파일을 읽어서 여러 캐릭터를 순차 또는 병렬로 학습합니다.
"""

try:
    import os
    import sys
    import yaml
    import logging
    from pathlib import Path
    from typing import Dict, List
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from datetime import datetime
    import json

    # 프로젝트 루트를 Python 경로에 추가
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    from tools.youtube_downloader import YouTubeAudioDownloader
    from tools.audio_preprocessor import AudioPreprocessor
    from tools.vocal_separator import VocalSeparator
    from tools.gpt_sovits_trainer import TrainingPipeline

    # 로그 디렉토리 생성
    log_dir = Path('./logs')
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('./logs/training.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

except Exception as e:
    print(f"Import 오류: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


class MultiCharacterTrainer:
    """다중 캐릭터 학습 관리자"""

    def __init__(self, config_path: str = "./configs/character_config.yaml"):
        """
        Args:
            config_path: 캐릭터 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # 컴포넌트 초기화
        self.downloader = YouTubeAudioDownloader(
            output_dir="./data/raw"
        )
        self.preprocessor = AudioPreprocessor(
            sample_rate=22050
        )
        self.vocal_separator = VocalSeparator(
            method="spleeter",
            output_dir="./data/vocals"
        )
        self.training_pipeline = TrainingPipeline()

        # 진행 상황 추적
        self.progress = {}
        self.results = {}

    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.info(f"✓ 설정 파일 로드: {self.config_path}")
        logger.info(f"  캐릭터 수: {len(config['characters'])}")

        return config

    def train_character(self, character_id: str, character_config: Dict) -> Dict:
        """
        단일 캐릭터 학습 전체 과정

        Args:
            character_id: 캐릭터 ID
            character_config: 캐릭터 설정

        Returns:
            학습 결과
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"캐릭터 학습 시작: {character_config['name']} ({character_id})")
        logger.info(f"{'='*70}\n")

        start_time = datetime.now()
        result = {
            'character_id': character_id,
            'character_name': character_config['name'],
            'start_time': start_time.isoformat(),
            'status': 'started',
            'steps': {}
        }

        try:
            # === 1단계: 유튜브에서 오디오 다운로드 ===
            logger.info(f"\n[1/5] 유튜브 오디오 다운로드")
            youtube_urls = character_config.get('youtube_urls', [])

            if not youtube_urls:
                raise ValueError("유튜브 URL이 설정되지 않았습니다.")

            downloaded_files = self.downloader.download_batch(
                character_id,
                youtube_urls,
                delay_between_downloads=2
            )

            result['steps']['download'] = {
                'status': 'success',
                'files_count': len(downloaded_files),
                'files': downloaded_files
            }

            logger.info(f"✓ 다운로드 완료: {len(downloaded_files)}개 파일")

            # === 2단계: 보컬 분리 (배경음악 제거) ===
            logger.info(f"\n[2/5] 보컬 분리 (배경음악 제거)")

            vocals_files = self.vocal_separator.batch_separate(
                downloaded_files,
                stems="2stems"
            )

            result['steps']['vocal_separation'] = {
                'status': 'success',
                'files_count': len(vocals_files),
                'files': vocals_files
            }

            logger.info(f"✓ 보컬 분리 완료: {len(vocals_files)}개 파일")

            # === 3단계: 음성 전처리 ===
            logger.info(f"\n[3/5] 음성 전처리 (노이즈 제거, 정규화, 세그먼트 분할)")

            audio_config = character_config.get('audio_processing', {})
            training_config = character_config.get('training', {})

            processed_files = self.preprocessor.batch_process(
                vocals_files,
                output_dir="./data/processed",
                character_name=character_id,
                enable_noise_reduction=audio_config.get('noise_reduction', True),
                enable_normalization=audio_config.get('normalization', True),
                enable_trim_silence=audio_config.get('trim_silence', True),
                segment_config={
                    'min_length': training_config.get('min_segment_length', 3.0),
                    'max_length': training_config.get('max_segment_length', 10.0),
                    'overlap': 0.5
                }
            )

            result['steps']['preprocessing'] = {
                'status': 'success',
                'segments_count': len(processed_files),
                'files': processed_files
            }

            logger.info(f"✓ 전처리 완료: {len(processed_files)}개 세그먼트")

            # === 4단계: 품질 필터링 ===
            logger.info(f"\n[4/5] 품질 필터링")

            # 품질이 낮은 세그먼트 제거
            filtered_files = []
            for audio_file in processed_files:
                if self.downloader.validate_audio(audio_file, min_duration=3.0):
                    filtered_files.append(audio_file)

            result['steps']['quality_filter'] = {
                'status': 'success',
                'original_count': len(processed_files),
                'filtered_count': len(filtered_files),
                'files': filtered_files
            }

            logger.info(f"✓ 품질 필터링 완료: {len(filtered_files)}/{len(processed_files)} 통과")

            # === 5단계: GPT-SoVITS 학습 ===
            logger.info(f"\n[5/5] GPT-SoVITS 모델 학습")

            gpt_sovits_config = training_config.get('gpt_sovits', {})

            model_dir = self.training_pipeline.run_full_pipeline(
                character_name=character_id,
                audio_files=filtered_files,
                training_config=gpt_sovits_config
            )

            result['steps']['training'] = {
                'status': 'success',
                'model_dir': str(model_dir),
                'config': gpt_sovits_config
            }

            logger.info(f"✓ 학습 완료: {model_dir}")

            # === 최종 결과 ===
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result['status'] = 'success'
            result['end_time'] = end_time.isoformat()
            result['duration_seconds'] = duration
            result['model_dir'] = str(model_dir)

            logger.info(f"\n{'='*70}")
            logger.info(f"✓ 캐릭터 학습 완료: {character_config['name']}")
            logger.info(f"  소요 시간: {duration/60:.1f}분")
            logger.info(f"  모델 경로: {model_dir}")
            logger.info(f"{'='*70}\n")

        except Exception as e:
            logger.error(f"✗ 캐릭터 학습 실패: {e}", exc_info=True)

            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = datetime.now().isoformat()

        return result

    def train_all_sequential(self) -> Dict[str, Dict]:
        """모든 캐릭터 순차 학습"""
        logger.info(f"\n{'#'*70}")
        logger.info(f"순차 학습 모드: 캐릭터를 하나씩 학습합니다")
        logger.info(f"{'#'*70}\n")

        results = {}

        for character_id, character_config in self.config['characters'].items():
            result = self.train_character(character_id, character_config)
            results[character_id] = result

        return results

    def train_all_parallel(self, max_workers: int = 2) -> Dict[str, Dict]:
        """모든 캐릭터 병렬 학습"""
        logger.info(f"\n{'#'*70}")
        logger.info(f"병렬 학습 모드: 최대 {max_workers}개 캐릭터 동시 학습")
        logger.info(f"{'#'*70}\n")

        results = {}

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 작업 제출
            future_to_character = {}
            for character_id, character_config in self.config['characters'].items():
                future = executor.submit(
                    self.train_character,
                    character_id,
                    character_config
                )
                future_to_character[future] = character_id

            # 결과 수집
            for future in as_completed(future_to_character):
                character_id = future_to_character[future]
                try:
                    result = future.result()
                    results[character_id] = result
                except Exception as e:
                    logger.error(f"캐릭터 {character_id} 학습 중 오류: {e}")
                    results[character_id] = {
                        'status': 'failed',
                        'error': str(e)
                    }

        return results

    def save_results(self, results: Dict[str, Dict]):
        """학습 결과 저장"""
        output_dir = Path("./output/reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"training_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✓ 학습 결과 저장: {report_file}")

        # 요약 출력
        self._print_summary(results)

    def _print_summary(self, results: Dict[str, Dict]):
        """학습 결과 요약 출력"""
        logger.info(f"\n{'='*70}")
        logger.info("학습 결과 요약")
        logger.info(f"{'='*70}")

        total = len(results)
        success = sum(1 for r in results.values() if r['status'] == 'success')
        failed = total - success

        logger.info(f"\n총 캐릭터: {total}")
        logger.info(f"성공: {success}")
        logger.info(f"실패: {failed}")

        logger.info(f"\n{'캐릭터':<15} {'상태':<10} {'소요시간':<15} {'모델 경로'}")
        logger.info("-" * 70)

        for character_id, result in results.items():
            status = result.get('status', 'unknown')
            duration = result.get('duration_seconds', 0) / 60
            model_dir = result.get('model_dir', 'N/A')

            logger.info(
                f"{character_id:<15} "
                f"{status:<10} "
                f"{duration:>6.1f}분      "
                f"{model_dir}"
            )

        logger.info(f"{'='*70}\n")


def main():
    """메인 함수"""
    print("스크립트 시작")
    try:
        import argparse

        parser = argparse.ArgumentParser(description="다중 캐릭터 음성 모델 학습")
        parser.add_argument(
            '--config',
            default='./configs/character_config.yaml',
            help='설정 파일 경로'
        )
        parser.add_argument(
            '--mode',
            choices=['sequential', 'parallel'],
            default='sequential',
            help='학습 모드 (순차 또는 병렬)'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=2,
            help='병렬 학습 시 최대 워커 수'
        )
        parser.add_argument(
            '--character',
            type=str,
            help='특정 캐릭터만 학습 (캐릭터 ID)'
        )

        args = parser.parse_args()

        # 트레이너 초기화
        trainer = MultiCharacterTrainer(config_path=args.config)

        # 학습 실행
        if args.character:
            # 특정 캐릭터만 학습
            character_config = trainer.config['characters'].get(args.character)
            if not character_config:
                logger.error(f"캐릭터를 찾을 수 없습니다: {args.character}")
                return

            result = trainer.train_character(args.character, character_config)
            results = {args.character: result}

        elif args.mode == 'parallel':
            # 병렬 학습
            results = trainer.train_all_parallel(max_workers=args.workers)

        else:
            # 순차 학습
            results = trainer.train_all_sequential()

        # 결과 저장
        trainer.save_results(results)

    except Exception as e:
        logger.error(f"스크립트 실행 중 오류 발생: {e}", exc_info=True)
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"메인 실행 오류: {e}")
        import traceback
        traceback.print_exc()
