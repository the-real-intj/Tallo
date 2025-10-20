# -*- coding: utf-8 -*-
"""
단일 오디오 파일로 학습하는 스크립트
녹화한 영상이나 단일 오디오 파일 사용
"""

import os
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.vocal_separator import VocalSeparator
from tools.audio_preprocessor import AudioPreprocessor


def train_from_audio(audio_path, character_name="tongtong", skip_vocal_separation=False):
    """
    단일 오디오 파일로 학습

    Args:
        audio_path: 오디오 파일 경로 (.wav, .mp3)
        character_name: 캐릭터 이름
        skip_vocal_separation: 보컬 분리 건너뛰기 (이미 보컬 분리된 파일인 경우)
    """
    print("\n" + "=" * 70)
    print(f"🎤 {character_name} 학습 시작")
    print("=" * 70)
    print()

    audio_path = Path(audio_path)

    if not audio_path.exists():
        print(f"❌ 파일 없음: {audio_path}")
        return

    # 파일이 이미 보컬 분리된 파일인지 확인
    if skip_vocal_separation or "vocals" in str(audio_path):
        print("✅ 이미 보컬 분리된 파일입니다. 보컬 분리 단계를 건너뜁니다.")
        vocals_path = str(audio_path)
    else:
        # === 1단계: 보컬 분리 ===
        print("[1/3] 보컬 분리 (배경음악 제거)")

        separator = VocalSeparator(method="spleeter")

        vocals_path = separator.separate(
            input_path=str(audio_path),
            output_dir=f"./data/vocals/{character_name}",
            stems="2stems"
        )

        print(f"✅ 보컬 분리 완료: {vocals_path}")

    # === 2단계: 전처리 ===
    step_num = "2/3" if not skip_vocal_separation else "1/2"
    print(f"\n[{step_num}] 전처리 (노이즈 제거, 세그먼트 분할)")

    preprocessor = AudioPreprocessor(sample_rate=22050)

    segments = preprocessor.process_audio(
        input_path=vocals_path,
        output_dir=f"./data/processed/{character_name}",
        character_name=character_name,
        enable_noise_reduction=True,
        enable_normalization=True,
        segment_config={
            'min_length': 3.0,
            'max_length': 10.0,
            'overlap': 0.5
        }
    )

    print(f"✅ 전처리 완료: {len(segments)}개 세그먼트")

    # 총 시간 계산
    total_duration = len(segments) * 5  # 평균 5초
    print(f"   예상 학습 데이터: {total_duration // 60}분 {total_duration % 60}초")

    # === 3단계: 모델 학습 안내 ===
    step_num = "3/3" if not skip_vocal_separation else "2/2"
    print(f"\n[{step_num}] 모델 학습")
    print("⚠️  이 단계는 오래 걸립니다 (1-12시간)")
    print()

    choice = input("지금 학습을 시작하시겠습니까? (y/n): ").strip().lower()

    if choice != 'y':
        print("\n⏸️  학습을 건너뜁니다.")
        print("\n나중에 학습하려면:")
        print(f"   python scripts/train_multiple_characters.py --character {character_name}")
        return

    print("\n🤖 학습 시작...")
    print("💡 로그: logs/training.log")

    # 학습 실행 (train_multiple_characters.py 호출)
    import subprocess

    result = subprocess.run([
        sys.executable,
        str(project_root / "scripts" / "train_multiple_characters.py"),
        "--character", character_name
    ])

    if result.returncode == 0:
        print("\n✅ 학습 완료!")
    else:
        print("\n❌ 학습 실패. logs/training.log 확인")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="단일 오디오 파일로 캐릭터 학습")
    parser.add_argument(
        '--file',
        type=str,
        help='학습할 오디오 파일 경로 (보컬 분리된 파일인 경우 --skip-vocal-separation 사용)'
    )
    parser.add_argument(
        '--character',
        type=str,
        default='tongtong',
        help='캐릭터 이름'
    )
    parser.add_argument(
        '--skip-vocal-separation',
        action='store_true',
        help='보컬 분리 단계 건너뛰기 (이미 보컬 분리된 파일인 경우)'
    )

    args = parser.parse_args()

    if args.file:
        # 명령줄로 파일 지정
        audio_path = Path(args.file)
        if not audio_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {audio_path}")
            return

        train_from_audio(
            audio_path=audio_path,
            character_name=args.character,
            skip_vocal_separation=args.skip_vocal_separation
        )
        return

    # 인터랙티브 모드
    print("\n🎯 단일 오디오 파일로 학습")
    print()

    # data/vocals에서 보컬 분리된 파일 찾기
    vocals_dir = Path("data/vocals")

    if vocals_dir.exists():
        vocals_files = list(vocals_dir.rglob("vocals.wav"))
        if vocals_files:
            print("📂 data/vocals에서 보컬 분리된 파일 발견:")
            for i, f in enumerate(vocals_files, 1):
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"   {i}. {f} ({size_mb:.1f}MB)")

            print()

            if len(vocals_files) == 1:
                selected_file = vocals_files[0]
                print(f"✅ 자동 선택: {selected_file}")
            else:
                choice = input(f"파일 선택 (1-{len(vocals_files)}): ").strip()
                try:
                    idx = int(choice) - 1
                    selected_file = vocals_files[idx]
                except:
                    print("❌ 잘못된 선택")
                    return

            # 학습 시작 (보컬 분리 건너뛰기)
            train_from_audio(
                audio_path=selected_file,
                character_name="tongtong",
                skip_vocal_separation=True
            )
            return

    # data/raw에서 원본 파일 찾기
    raw_dir = Path("data/raw")

    if not raw_dir.exists():
        print("❌ data/raw 또는 data/vocals 디렉토리가 없습니다.")
        print("\n먼저 영상을 추출하세요:")
        print("   python scripts/use_custom_video.py")
        return

    # 오디오 파일 목록
    audio_files = list(raw_dir.glob("tongtong_custom*.wav"))

    if not audio_files:
        print("❌ data/raw/tongtong_custom*.wav 파일이 없습니다.")
        print("\n먼저 영상을 추출하세요:")
        print("   python scripts/use_custom_video.py")
        return

    print(f"📂 발견된 파일: {len(audio_files)}개")
    print()

    for i, f in enumerate(audio_files, 1):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"   {i}. {f.name} ({size_mb:.1f}MB)")

    print()

    if len(audio_files) == 1:
        selected_file = audio_files[0]
        print(f"✅ 자동 선택: {selected_file.name}")
    else:
        choice = input(f"파일 선택 (1-{len(audio_files)}): ").strip()
        try:
            idx = int(choice) - 1
            selected_file = audio_files[idx]
        except:
            print("❌ 잘못된 선택")
            return

    # 학습 시작
    train_from_audio(selected_file, character_name="tongtong")


if __name__ == "__main__":
    main()
