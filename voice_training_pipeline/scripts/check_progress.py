# -*- coding: utf-8 -*-
"""
학습 진행 상황 확인 스크립트
실시간으로 파일 생성 및 학습 상태를 모니터링합니다.
"""

import os
from pathlib import Path
import time
from datetime import datetime


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_directory(path, description):
    """디렉토리 내용 확인"""
    path = Path(path)

    if not path.exists():
        print(f"❌ {description}: 없음")
        return 0

    files = list(path.rglob("*"))
    file_count = len([f for f in files if f.is_file()])

    if file_count == 0:
        print(f"⚠️  {description}: 폴더는 있지만 파일 없음")
        return 0

    print(f"✅ {description}: {file_count}개 파일")

    # 최근 파일 5개 표시
    recent_files = sorted(
        [f for f in files if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:5]

    for f in recent_files:
        size_mb = f.stat().st_size / 1024 / 1024
        mod_time = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M:%S")
        print(f"   - {f.name} ({size_mb:.1f}MB, {mod_time})")

    return file_count


def check_logs():
    """로그 파일 확인"""
    log_file = Path("logs/training.log")

    if not log_file.exists():
        print("❌ 로그 파일 없음 (아직 시작 안 함)")
        return

    print(f"✅ 로그 파일: {log_file}")
    print(f"   크기: {log_file.stat().st_size / 1024:.1f}KB")

    # 마지막 10줄 출력
    print("\n📝 최근 로그 (마지막 10줄):")
    print("-" * 70)

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print("   " + line.rstrip())
    except Exception as e:
        print(f"   로그 읽기 오류: {e}")


def check_character_progress(character_id="tongtong"):
    """캐릭터별 진행 상황 체크"""
    print_section(f"퉁퉁이 ({character_id}) 학습 진행 상황")

    steps = [
        ("data/raw", f"1단계: 유튜브 다운로드 (data/raw/{character_id}_*.mp3)"),
        (f"data/vocals/{character_id}", "2단계: 보컬 분리 (vocals.wav)"),
        (f"data/processed/{character_id}", "3단계: 전처리 (segment_*.wav)"),
        (f"data/datasets/{character_id}", "4단계: 대본 생성 (transcript.txt)"),
        (f"models/gpt-sovits/{character_id}", "5단계: 모델 학습 (*.pth)"),
    ]

    total_steps = len(steps)
    completed_steps = 0

    for path, description in steps:
        count = check_directory(path, description)
        if count > 0:
            completed_steps += 1

    # 진행률
    progress = (completed_steps / total_steps) * 100
    print(f"\n📊 전체 진행률: {progress:.1f}% ({completed_steps}/{total_steps} 단계)")

    # 진행 바
    bar_length = 50
    filled = int(bar_length * completed_steps / total_steps)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"   [{bar}]")

    return completed_steps, total_steps


def estimate_time_remaining():
    """남은 시간 추정"""
    model_dir = Path("models/gpt-sovits/tongtong")

    if not model_dir.exists():
        print("\n⏱️  예상 남은 시간: 학습 시작 전 (1-12시간 예상)")
        return

    checkpoints = list(model_dir.glob("*.pth"))

    if not checkpoints:
        print("\n⏱️  예상 남은 시간: 학습 초기 단계")
        return

    print("\n⏱️  학습 진행 중... (체크포인트 발견)")
    print(f"   저장된 모델: {len(checkpoints)}개")


def check_errors():
    """오류 확인"""
    print_section("오류 확인")

    log_file = Path("logs/training.log")

    if not log_file.exists():
        print("로그 파일 없음")
        return

    errors = []

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, 1):
                if 'ERROR' in line or 'Exception' in line or '오류' in line:
                    errors.append((i, line.strip()))
    except Exception as e:
        print(f"로그 읽기 오류: {e}")
        return

    if not errors:
        print("✅ 오류 없음")
        return

    print(f"⚠️  발견된 오류: {len(errors)}개")
    print("\n최근 오류 (최대 5개):")
    print("-" * 70)

    for line_num, error in errors[-5:]:
        print(f"   Line {line_num}: {error}")


def watch_mode():
    """실시간 모니터링 모드"""
    print("\n🔄 실시간 모니터링 모드 (Ctrl+C로 종료)")
    print("=" * 70)

    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')

            print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            completed, total = check_character_progress()

            if completed == total:
                print("\n🎉 학습 완료!")
                break

            print("\n⏳ 30초 후 자동 갱신... (Ctrl+C로 종료)")
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n종료됨")


def main():
    """메인 함수"""
    print("\n🔍 퉁퉁이 학습 진행 상황 체크")

    # 1. 진행 상황 체크
    completed, total = check_character_progress()

    # 2. 로그 확인
    print_section("로그 확인")
    check_logs()

    # 3. 오류 확인
    check_errors()

    # 4. 남은 시간 추정
    estimate_time_remaining()

    # 5. 다음 단계 안내
    print_section("다음 단계")

    if completed == 0:
        print("❌ 아직 시작하지 않았습니다!")
        print("\n실행 명령어:")
        print("   python scripts/train_multiple_characters.py --character tongtong")

    elif completed < total:
        print(f"⏳ 학습 진행 중... ({completed}/{total} 단계)")
        print("\n진행 상황을 계속 확인하려면:")
        print("   python scripts/check_progress.py --watch")

    else:
        print("🎉 학습 완료!")
        print("\n다음 단계:")
        print("1. 모델 테스트:")
        print("   python scripts/test_chatbot_simple.py")
        print("\n2. 음성 대화 테스트:")
        print("   python scripts/test_voice_chat.py")

    print("\n" + "=" * 70)

    # 실시간 모니터링 옵션
    import sys
    if '--watch' in sys.argv:
        watch_mode()


if __name__ == "__main__":
    main()
