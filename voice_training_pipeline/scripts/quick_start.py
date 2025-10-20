"""
빠른 시작 스크립트

대화형 CLI로 쉽게 캐릭터 음성 학습을 시작할 수 있습니다.
"""

import os
import sys
from pathlib import Path
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuickStartWizard:
    """빠른 시작 마법사"""

    def __init__(self):
        self.config = {
            'characters': {}
        }

    def welcome(self):
        """환영 메시지"""
        print("\n" + "=" * 70)
        print("🎤 음성 모델 학습 파이프라인 - 빠른 시작")
        print("=" * 70)
        print("\n이 마법사가 캐릭터 음성 모델 학습을 도와드립니다.")
        print("몇 가지 질문에 답변해주세요!\n")

    def ask_character_info(self) -> dict:
        """캐릭터 정보 입력"""
        print("\n--- 캐릭터 기본 정보 ---\n")

        character_id = input("캐릭터 ID (영문, 예: pororo): ").strip()
        if not character_id:
            character_id = "my_character"

        name = input(f"캐릭터 이름 (예: 뽀로로): ").strip()
        if not name:
            name = character_id

        description = input("캐릭터 설명 (선택, Enter로 건너뛰기): ").strip()

        return {
            'id': character_id,
            'name': name,
            'description': description or f"{name} 캐릭터"
        }

    def ask_youtube_urls(self) -> list:
        """유튜브 URL 입력"""
        print("\n--- 음성 소스 (유튜브 URL) ---\n")
        print("캐릭터 음성이 포함된 유튜브 영상 URL을 입력하세요.")
        print("여러 개를 입력하려면 계속 입력하고, 완료하면 Enter를 누르세요.\n")

        urls = []
        while True:
            url = input(f"유튜브 URL #{len(urls) + 1} (완료하려면 Enter): ").strip()

            if not url:
                break

            if "youtube.com" in url or "youtu.be" in url:
                urls.append(url)
                print(f"  ✓ 추가됨: {url}")
            else:
                print("  ✗ 올바른 유튜브 URL이 아닙니다. 다시 입력하세요.")

        if not urls:
            print("\n⚠ URL이 입력되지 않았습니다. 나중에 설정 파일에서 추가하세요.")

        return urls

    def ask_training_config(self) -> dict:
        """학습 설정 입력"""
        print("\n--- 학습 설정 ---\n")

        print("학습 품질을 선택하세요:")
        print("  1. 빠른 테스트 (50 epochs, 배치 크기 8) - 약 30분")
        print("  2. 일반 품질 (100 epochs, 배치 크기 4) - 약 1-2시간")
        print("  3. 고품질 (200 epochs, 배치 크기 4) - 약 3-4시간")

        choice = input("선택 (1-3, 기본값: 2): ").strip()

        if choice == "1":
            return {
                'epochs': 50,
                'batch_size': 8,
                'learning_rate': 0.0002
            }
        elif choice == "3":
            return {
                'epochs': 200,
                'batch_size': 4,
                'learning_rate': 0.0001
            }
        else:  # 기본값 또는 2
            return {
                'epochs': 100,
                'batch_size': 4,
                'learning_rate': 0.0001
            }

    def ask_personality(self) -> dict:
        """성격 정보 입력 (선택)"""
        print("\n--- 캐릭터 성격 (선택) ---\n")
        print("나중에 스토리 생성에 사용됩니다. 건너뛰려면 Enter를 누르세요.\n")

        traits_input = input("성격 특성 (쉼표로 구분, 예: 호기심많음,장난기많음): ").strip()
        traits = [t.strip() for t in traits_input.split(',')] if traits_input else []

        speech_style = input("말투 특징 (예: 밝고 경쾌한 말투): ").strip()

        age_group = input("권장 연령대 (예: 3-5세): ").strip()

        return {
            'traits': traits,
            'speech_style': speech_style or "친근한 말투",
            'age_group': age_group or "전체"
        }

    def create_config(self):
        """설정 생성"""
        self.welcome()

        # 캐릭터 정보
        char_info = self.ask_character_info()

        # 유튜브 URL
        youtube_urls = self.ask_youtube_urls()

        # 학습 설정
        training_config = self.ask_training_config()

        # 성격 (선택)
        personality = self.ask_personality()

        # 설정 구성
        character_config = {
            'name': char_info['name'],
            'description': char_info['description'],
            'youtube_urls': youtube_urls,
            'personality': personality,
            'training': {
                'target_duration': 300,
                'min_segment_length': 3,
                'max_segment_length': 10,
                'sample_rate': 22050,
                'gpt_sovits': training_config,
                'rvc': {'enabled': False}
            },
            'audio_processing': {
                'noise_reduction': True,
                'normalization': True,
                'trim_silence': True,
                'target_loudness': -20
            }
        }

        self.config['characters'][char_info['id']] = character_config

        # 전역 설정
        self.config['global_settings'] = {
            'parallel_training': False,
            'max_parallel_jobs': 1,
            'data_augmentation': {
                'enabled': False
            },
            'quality_control': {
                'min_audio_quality_score': 0.7,
                'auto_reject_low_quality': True,
                'manual_review': False
            },
            'backup': {
                'enabled': True,
                'interval': 10,
                'max_backups': 3
            }
        }

        return char_info['id']

    def save_config(self, filename: str = "character_config.yaml"):
        """설정 저장"""
        config_path = Path("./configs") / filename
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)

        logger.info(f"\n✓ 설정 파일 저장됨: {config_path}")
        return config_path

    def show_summary(self, character_id: str):
        """설정 요약 표시"""
        char = self.config['characters'][character_id]

        print("\n" + "=" * 70)
        print("📋 설정 요약")
        print("=" * 70)
        print(f"\n캐릭터 ID: {character_id}")
        print(f"이름: {char['name']}")
        print(f"설명: {char['description']}")
        print(f"\n유튜브 URL: {len(char['youtube_urls'])}개")
        for i, url in enumerate(char['youtube_urls'], 1):
            print(f"  {i}. {url}")
        print(f"\n학습 설정:")
        print(f"  - Epochs: {char['training']['gpt_sovits']['epochs']}")
        print(f"  - Batch Size: {char['training']['gpt_sovits']['batch_size']}")
        print(f"  - Learning Rate: {char['training']['gpt_sovits']['learning_rate']}")
        print("\n" + "=" * 70)

    def ask_start_training(self) -> bool:
        """학습 시작 여부 확인"""
        print("\n바로 학습을 시작하시겠습니까?")
        choice = input("(y/n, 기본값: n): ").strip().lower()

        return choice == 'y'

    def start_training(self, character_id: str):
        """학습 시작"""
        print(f"\n🚀 {character_id} 캐릭터 학습을 시작합니다...\n")

        import subprocess

        cmd = [
            sys.executable,
            "scripts/train_multiple_characters.py",
            "--character", character_id,
            "--config", "./configs/character_config.yaml"
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"학습 실패: {e}")
        except KeyboardInterrupt:
            logger.info("\n학습이 중단되었습니다.")

    def run(self):
        """마법사 실행"""
        # 설정 생성
        character_id = self.create_config()

        # 요약 표시
        self.show_summary(character_id)

        # 설정 저장
        config_path = self.save_config()

        print(f"\n설정이 저장되었습니다: {config_path}")
        print("\n다음 명령으로 학습을 시작할 수 있습니다:")
        print(f"  python scripts/train_multiple_characters.py --character {character_id}")

        # 바로 시작 여부
        if self.ask_start_training():
            self.start_training(character_id)
        else:
            print("\n나중에 위 명령을 실행하여 학습을 시작하세요.")
            print("설정을 수정하려면 configs/character_config.yaml 파일을 편집하세요.")


def main():
    wizard = QuickStartWizard()

    try:
        wizard.run()
    except KeyboardInterrupt:
        print("\n\n종료되었습니다.")
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)


if __name__ == "__main__":
    main()
