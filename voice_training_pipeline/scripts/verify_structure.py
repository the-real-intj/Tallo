"""
프로젝트 구조 검증 스크립트

폴더명 변경 후 모든 경로가 올바르게 업데이트되었는지 확인합니다.
"""

import os
from pathlib import Path
import sys

class StructureVerifier:
    """프로젝트 구조 검증 클래스"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []

    def check_directory_names(self):
        """디렉토리명 확인"""
        print("\n=== 디렉토리명 검증 ===")

        # 현재 디렉토리가 올바른 이름인지 확인
        current_dir = Path.cwd().name

        if current_dir == "voice_training_pipeline":
            self.success.append("OK 메인 디렉토리명이 올바릅니다: voice_training_pipeline")
            print("OK 메인 디렉토리명: voice_training_pipeline")
        elif current_dir == "voice-training-pipeline":
            self.errors.append("NG 디렉토리명이 아직 변경되지 않았습니다: voice-training-pipeline")
            print("NG 디렉토리명이 하이픈(-) 형식입니다. 언더스코어(_)로 변경해주세요.")
        else:
            self.warnings.append(f"WN  예상치 못한 디렉토리명: {current_dir}")
            print(f"WN  디렉토리명: {current_dir}")

        # models 하위 디렉토리 확인
        models_dir = Path("models")
        if models_dir.exists():
            if (models_dir / "gpt_sovits").exists():
                self.success.append("OK models/gpt_sovits 디렉토리가 존재합니다")
                print("OK models/gpt_sovits/")
            else:
                self.errors.append("NG models/gpt_sovits 디렉토리를 찾을 수 없습니다")
                print("NG models/gpt_sovits/ 없음")

            if (models_dir / "gpt-sovits").exists():
                self.warnings.append("WN  이전 이름의 디렉토리가 남아있습니다: models/gpt-sovits")
                print("WN  models/gpt-sovits/ 발견 (삭제 권장)")

    def check_file_references(self):
        """파일 내 경로 참조 확인"""
        print("\n=== 파일 내 참조 검증 ===")

        files_to_check = [
            "tools/gpt_sovits_trainer.py",
            "scripts/train_multiple_characters.py",
            "scripts/test_model.py",
            ".env",
            "README.md",
        ]

        old_patterns = [
            "voice-training-pipeline",
            "gpt-sovits",
            "models/gpt-sovits",
        ]

        for file_path in files_to_check:
            path = Path(file_path)
            if not path.exists():
                self.warnings.append(f"WN  파일을 찾을 수 없습니다: {file_path}")
                continue

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                found_old = False
                for pattern in old_patterns:
                    if pattern in content:
                        self.errors.append(f"NG {file_path}에서 이전 경로 발견: {pattern}")
                        print(f"NG {file_path}: '{pattern}' 발견")
                        found_old = True

                if not found_old:
                    self.success.append(f"OK {file_path} 검증 통과")
                    print(f"OK {file_path}")

            except Exception as e:
                self.warnings.append(f"WN  {file_path} 읽기 실패: {e}")

    def check_required_directories(self):
        """필수 디렉토리 존재 확인"""
        print("\n=== 필수 디렉토리 확인 ===")

        required_dirs = [
            "configs",
            "data",
            "models",
            "models/gpt_sovits",
            "models/rvc",
            "models/xtts",
            "tools",
            "scripts",
            "output",
            "logs",
        ]

        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists():
                print(f"OK {dir_path}/")
                self.success.append(f"OK {dir_path}/ 존재")
            else:
                print(f"WN  {dir_path}/ (자동 생성 예정)")
                # 디렉토리 생성
                path.mkdir(parents=True, exist_ok=True)
                print(f"   → 생성됨: {dir_path}/")

    def check_env_files(self):
        """환경 파일 확인"""
        print("\n=== 환경 파일 확인 ===")

        if Path(".env.example").exists():
            self.success.append("OK .env.example 파일 존재")
            print("OK .env.example")

            # GPT_SOVITS_DIR 확인
            with open(".env.example", 'r', encoding='utf-8') as f:
                content = f.read()
                if "GPT_SOVITS_DIR=./models/gpt_sovits" in content:
                    print("   OK GPT_SOVITS_DIR 경로 올바름")
                else:
                    self.errors.append("NG .env.example에서 GPT_SOVITS_DIR 경로가 올바르지 않음")
                    print("   NG GPT_SOVITS_DIR 경로 확인 필요")
        else:
            self.warnings.append("WN  .env.example 파일이 없습니다")
            print("WN  .env.example 없음")

        if Path(".env").exists():
            print("OK .env")
        else:
            self.warnings.append("WN  .env 파일을 생성하세요 (cp .env.example .env)")
            print("WN  .env 없음 (cp .env.example .env 실행 권장)")

    def print_summary(self):
        """결과 요약"""
        print("\n" + "=" * 70)
        print("검증 결과 요약")
        print("=" * 70)

        print(f"\nOK 성공: {len(self.success)}개")
        print(f"WN  경고: {len(self.warnings)}개")
        print(f"NG 오류: {len(self.errors)}개")

        if self.errors:
            print("\n" + "=" * 70)
            print("NG 해결 필요한 오류:")
            print("=" * 70)
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print("\n" + "=" * 70)
            print("WN  확인 필요한 경고:")
            print("=" * 70)
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n모든 검증 통과! 프로젝트 구조가 올바릅니다.")
        elif not self.errors:
            print("\n주요 오류 없음. 경고 사항을 확인하세요.")
        else:
            print("\n오류가 발견되었습니다. 위 내용을 확인하고 수정해주세요.")

        print("\n" + "=" * 70)

    def run(self):
        """전체 검증 실행"""
        print("\n" + "=" * 70)
        print("프로젝트 구조 검증 시작")
        print("=" * 70)

        self.check_directory_names()
        self.check_required_directories()
        self.check_file_references()
        self.check_env_files()
        self.print_summary()


def main():
    verifier = StructureVerifier()
    verifier.run()


if __name__ == "__main__":
    main()
