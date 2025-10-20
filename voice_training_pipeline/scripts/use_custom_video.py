# -*- coding: utf-8 -*-
"""
사용자가 직접 녹화한 영상을 사용하는 스크립트
유튜브 대신 로컬 파일 사용
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pydub import AudioSegment
import subprocess


def extract_audio_from_video(video_path, output_path):
    """
    비디오 파일에서 오디오 추출

    Args:
        video_path: 입력 비디오 파일 (.mp4, .mkv, .avi 등)
        output_path: 출력 오디오 파일 (.wav)
    """
    print(f"🎬 비디오 파일: {video_path}")
    print(f"🎵 오디오 추출 중...")

    video_path = Path(video_path)
    output_path = Path(output_path)

    if not video_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
        return False

    # 출력 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # FFmpeg로 오디오 추출
        command = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # 비디오 제거
            '-acodec', 'pcm_s16le',  # WAV 포맷
            '-ar', '22050',  # 샘플링 레이트
            '-ac', '1',  # 모노
            '-y',  # 덮어쓰기
            str(output_path)
        ]

        subprocess.run(command, check=True, capture_output=True)

        print(f"✅ 오디오 추출 완료: {output_path}")

        # 파일 정보
        audio = AudioSegment.from_wav(str(output_path))
        duration_sec = len(audio) / 1000
        size_mb = output_path.stat().st_size / 1024 / 1024

        print(f"   길이: {duration_sec // 60:.0f}분 {duration_sec % 60:.0f}초")
        print(f"   크기: {size_mb:.1f}MB")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg 오류: {e}")
        print("\n💡 FFmpeg가 설치되지 않았을 수 있습니다.")
        print("설치 방법:")
        print("  Windows: choco install ffmpeg")
        print("  또는: https://ffmpeg.org/download.html")
        return False

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def main():
    """메인 함수"""
    print("\n" + "=" * 70)
    print("🎬 녹화한 영상으로 퉁퉁이 학습하기")
    print("=" * 70)
    print()

    # 1. 비디오 파일 경로 입력
    print("녹화한 영상 파일을 준비하세요.")
    print("예: C:\\Users\\Downloads\\tongtong_recording.mp4")
    print()

    video_path = input("비디오 파일 경로를 입력하세요: ").strip().strip('"')

    if not video_path:
        print("❌ 경로가 입력되지 않았습니다.")
        return

    video_path = Path(video_path)

    if not video_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
        return

    # 2. 오디오 추출
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"tongtong_custom_{video_path.stem}.wav"

    success = extract_audio_from_video(video_path, output_path)

    if not success:
        return

    # 3. 다음 단계 안내
    print("\n" + "=" * 70)
    print("✅ 준비 완료!")
    print("=" * 70)
    print()
    print("다음 단계:")
    print()
    print("1. 배경음 제거 (선택):")
    print("   python scripts/quick_start_tongtong.py")
    print("   → 메뉴에서 2 선택")
    print()
    print("2. 전체 파이프라인 실행:")
    print("   python scripts/train_single_audio.py")
    print()
    print("또는:")
    print()
    print("3. 수동으로 단계별 실행:")
    print("   - 보컬 분리")
    print("   - 전처리")
    print("   - 모델 학습")


if __name__ == "__main__":
    main()
