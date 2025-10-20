"""
환경 설정 체크 스크립트

시스템 환경을 검사하고 필요한 라이브러리와 도구가 설치되어 있는지 확인합니다.
"""

import sys
import subprocess
import importlib
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentChecker:
    """환경 체크 클래스"""

    def __init__(self):
        self.issues = []
        self.warnings = []

    def check_python_version(self):
        """Python 버전 확인"""
        print("\n=== Python 버전 ===")

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        print(f"현재 버전: {version_str}")

        if version.major < 3 or (version.major == 3 and version.minor < 9):
            self.issues.append("Python 3.9 이상이 필요합니다.")
            print("❌ Python 3.9 이상이 필요합니다.")
        else:
            print("✅ Python 버전 OK")

    def check_gpu(self):
        """GPU 확인"""
        print("\n=== GPU 확인 ===")

        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_count = torch.cuda.device_count()
                vram = torch.cuda.get_device_properties(0).total_memory / 1024**3

                print(f"✅ GPU 사용 가능")
                print(f"   GPU: {gpu_name}")
                print(f"   개수: {gpu_count}")
                print(f"   VRAM: {vram:.1f} GB")

                if vram < 8:
                    self.warnings.append(f"VRAM이 {vram:.1f}GB입니다. 8GB 이상 권장합니다.")
                    print(f"⚠️  VRAM이 {vram:.1f}GB입니다. 8GB 이상 권장합니다.")

            else:
                print("⚠️  GPU를 사용할 수 없습니다. CPU로 학습됩니다 (매우 느림)")
                self.warnings.append("GPU 없이 학습하면 매우 느립니다.")

        except ImportError:
            print("❌ PyTorch가 설치되지 않았습니다.")
            self.issues.append("PyTorch를 설치하세요: pip install torch")

    def check_ffmpeg(self):
        """FFmpeg 설치 확인"""
        print("\n=== FFmpeg ===")

        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=True
            )

            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")

        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg가 설치되지 않았습니다.")
            self.issues.append("FFmpeg를 설치하세요: https://ffmpeg.org/download.html")

    def check_required_packages(self):
        """필수 패키지 확인"""
        print("\n=== 필수 패키지 ===")

        required_packages = {
            'torch': 'PyTorch',
            'librosa': 'Librosa',
            'soundfile': 'SoundFile',
            'yt_dlp': 'yt-dlp',
            'pydub': 'PyDub',
            'noisereduce': 'NoiseReduce',
            'whisper': 'OpenAI Whisper',
            'yaml': 'PyYAML',
            'tqdm': 'tqdm',
        }

        for package, name in required_packages.items():
            try:
                importlib.import_module(package)
                print(f"✅ {name}")
            except ImportError:
                print(f"❌ {name}")
                self.issues.append(f"{name}를 설치하세요: pip install {package}")

    def check_optional_packages(self):
        """선택 패키지 확인"""
        print("\n=== 선택 패키지 (음성 분리) ===")

        optional_packages = {
            'spleeter': 'Spleeter (보컬 분리)',
        }

        for package, name in optional_packages.items():
            try:
                importlib.import_module(package)
                print(f"✅ {name}")
            except ImportError:
                print(f"⚠️  {name} - 설치 권장: pip install {package}")
                self.warnings.append(f"{name} 설치 권장")

    def check_directories(self):
        """디렉토리 구조 확인"""
        print("\n=== 디렉토리 구조 ===")

        required_dirs = [
            'data/raw',
            'data/processed',
            'data/vocals',
            'data/segments',
            'data/datasets',
            'models/gpt_sovits',
            'configs',
            'logs',
            'output/audio',
            'output/reports',
            'tools',
            'scripts',
        ]

        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists():
                print(f"✅ {dir_path}")
            else:
                print(f"⚠️  {dir_path} - 자동 생성됩니다")

    def check_gpt_sovits(self):
        """GPT-SoVITS 설치 확인"""
        print("\n=== GPT-SoVITS ===")

        gpt_sovits_dir = Path("./GPT-SoVITS")

        if gpt_sovits_dir.exists():
            print(f"✅ GPT-SoVITS 디렉토리 존재: {gpt_sovits_dir}")

            # 주요 파일 확인
            important_files = [
                "GPT_SoVITS/s1_train.py",
                "GPT_SoVITS/inference.py",
            ]

            for file in important_files:
                if (gpt_sovits_dir / file).exists():
                    print(f"   ✅ {file}")
                else:
                    print(f"   ⚠️  {file} 없음")

        else:
            print("⚠️  GPT-SoVITS가 설치되지 않았습니다.")
            print("   설치: git clone https://github.com/RVC-Boss/GPT-SoVITS.git")
            self.warnings.append("GPT-SoVITS 설치 필요")

    def check_pretrained_models(self):
        """사전학습 모델 확인"""
        print("\n=== 사전학습 모델 ===")

        pretrained_dir = Path("./pretrained_models")

        if pretrained_dir.exists():
            models = list(pretrained_dir.glob("*.ckpt")) + list(pretrained_dir.glob("*.pth"))

            if models:
                print(f"✅ 사전학습 모델 발견: {len(models)}개")
                for model in models:
                    print(f"   - {model.name}")
            else:
                print("⚠️  사전학습 모델이 없습니다.")
                print("   다운로드: https://huggingface.co/lj1995/GPT-SoVITS")
                self.warnings.append("사전학습 모델 다운로드 필요")
        else:
            print("⚠️  pretrained_models 디렉토리가 없습니다.")
            self.warnings.append("사전학습 모델 디렉토리 생성 및 모델 다운로드 필요")

    def check_config_files(self):
        """설정 파일 확인"""
        print("\n=== 설정 파일 ===")

        config_files = {
            'configs/character_config.yaml': '캐릭터 설정',
            '.env': '환경 변수',
        }

        for file_path, description in config_files.items():
            path = Path(file_path)
            if path.exists():
                print(f"✅ {description}: {file_path}")
            else:
                print(f"⚠️  {description}: {file_path} 없음")

                if file_path == '.env':
                    print("   .env.example을 복사하여 .env 파일을 생성하세요")

    def print_summary(self):
        """요약 출력"""
        print("\n" + "=" * 70)
        print("환경 체크 요약")
        print("=" * 70)

        if not self.issues and not self.warnings:
            print("\n✅ 모든 환경이 정상입니다!")
            print("학습을 시작할 수 있습니다.\n")
            print("빠른 시작: python scripts/quick_start.py")

        else:
            if self.issues:
                print(f"\n❌ 해결 필요한 문제: {len(self.issues)}개")
                for i, issue in enumerate(self.issues, 1):
                    print(f"   {i}. {issue}")

            if self.warnings:
                print(f"\n⚠️  경고: {len(self.warnings)}개")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"   {i}. {warning}")

            if self.issues:
                print("\n위 문제를 해결한 후 다시 실행하세요.")
            else:
                print("\n경고 사항이 있지만 학습을 시작할 수 있습니다.")

        print("\n" + "=" * 70)

    def run_all_checks(self):
        """모든 체크 실행"""
        print("\n" + "=" * 70)
        print("🔍 환경 설정 체크")
        print("=" * 70)

        self.check_python_version()
        self.check_gpu()
        self.check_ffmpeg()
        self.check_required_packages()
        self.check_optional_packages()
        self.check_directories()
        self.check_gpt_sovits()
        self.check_pretrained_models()
        self.check_config_files()

        self.print_summary()


def main():
    checker = EnvironmentChecker()
    checker.run_all_checks()


if __name__ == "__main__":
    main()
