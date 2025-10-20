# -*- coding: utf-8 -*-
"""
배경음악 제거 스크립트
단일 오디오 파일에서 배경음악을 제거하고 목소리만 추출합니다.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.vocal_separator import VocalSeparator


def remove_background_music(
    input_file,
    output_dir="./data/vocals",
    method="spleeter"
):
    """
    배경음악 제거

    Args:
        input_file: 입력 오디오 파일
        output_dir: 출력 디렉토리
        method: 분리 방법 (spleeter 또는 demucs)
    """
    print("\n" + "=" * 70)
    print("🎵 배경음악 제거 (보컬 분리)")
    print("=" * 70)
    print()

    input_file = Path(input_file)

    if not input_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        return None

    # 파일 정보
    size_mb = input_file.stat().st_size / 1024 / 1024
    print(f"📂 입력 파일: {input_file.name}")
    print(f"   크기: {size_mb:.1f}MB")
    print()

    # 보컬 분리기 초기화
    print(f"🔧 방법: {method}")
    print("⏳ 처리 시간: 파일 크기에 따라 1-5분 소요")
    print()

    try:
        separator = VocalSeparator(method=method, output_dir=output_dir)

        # 배경음악 제거
        print("🎤 보컬 분리 중...")
        vocals_path = separator.separate(
            audio_path=str(input_file),
            stems="2stems"  # vocals + accompaniment
        )

        print()
        print("=" * 70)
        print("✅ 완료!")
        print("=" * 70)
        print()
        print(f"📁 결과 파일:")
        print(f"   목소리만: {vocals_path}")

        # 배경음악 파일 경로
        bg_music_path = vocals_path.replace("vocals.wav", "accompaniment.wav")
        if os.path.exists(bg_music_path):
            print(f"   배경음악: {bg_music_path}")

        print()
        print("💡 다음 단계:")
        print("   python scripts/train_single_audio.py")
        print()

        return vocals_path

    except ImportError as e:
        print(f"\n❌ 필요한 패키지가 설치되지 않았습니다: {e}")
        print("\n설치 방법:")
        print("   pip install spleeter")
        print("   또는")
        print("   pip install demucs")
        return None

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """메인 함수"""
    print("\n🎯 배경음악 제거 도구")
    print()

    # 자동으로 파일 찾기
    raw_dir = Path("data/raw")

    if not raw_dir.exists():
        print("❌ data/raw 디렉토리가 없습니다.")
        return

    # tongtong_custom*.wav 파일 찾기
    audio_files = list(raw_dir.glob("tongtong_custom*.wav"))

    if not audio_files:
        print("❌ data/raw/tongtong_custom*.wav 파일이 없습니다.")
        print("\n파일을 직접 지정하려면:")
        print('   python scripts/remove_background_music.py "경로/파일.wav"')
        return

    print(f"📂 발견된 파일: {len(audio_files)}개")
    print()

    # 파일 목록 출력
    for i, f in enumerate(audio_files, 1):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"   {i}. {f.name} ({size_mb:.1f}MB)")

    print()

    # 파일 선택
    if len(audio_files) == 1:
        selected_file = audio_files[0]
        print(f"✅ 자동 선택: {selected_file.name}")
    else:
        try:
            choice = input(f"파일 선택 (1-{len(audio_files)}): ").strip()
            idx = int(choice) - 1
            selected_file = audio_files[idx]
        except:
            print("❌ 잘못된 선택")
            return

    print()

    # 방법 선택
    print("분리 방법 선택:")
    print("   1. Spleeter (빠름, 권장)")
    print("   2. Demucs (느림, 고품질)")
    print()

    method_choice = input("선택 (1-2, Enter=1): ").strip()

    if method_choice == "2":
        method = "demucs"
    else:
        method = "spleeter"

    # 배경음악 제거 실행
    vocals_path = remove_background_music(
        input_file=selected_file,
        output_dir="./data/vocals/tongtong",
        method=method
    )

    if vocals_path:
        print("🎉 성공!")


if __name__ == "__main__":
    # 명령줄 인자로 파일 지정 가능
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        remove_background_music(input_file)
    else:
        main()
