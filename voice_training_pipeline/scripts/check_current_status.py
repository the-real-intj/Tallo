# -*- coding: utf-8 -*-
"""
현재 진행 상황 체크 + 블로그 가이드라인 비교
"""

import os
from pathlib import Path
from datetime import datetime


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_blog_pipeline():
    """블로그 가이드라인 단계"""
    print_header("📋 블로그 가이드라인 단계 (sesang06.tistory.com/216)")

    steps = [
        ("1단계", "음성 데이터 수집", "애니메이션 447개 대사 추출"),
        ("2단계", "음성 정제", "Ultimate Vocal Remover로 배경음악 제거"),
        ("3단계", "음성 필터링", "감정 없는 평온한 목소리만 선별"),
        ("4단계", "메타데이터 작성", "각 음성 파일에 대응하는 텍스트 대본"),
        ("5단계", "XTTS 파인튜닝", "음성 모델 학습 (2-3시간)"),
        ("6단계", "테스트", "학습된 모델로 음성 생성 테스트"),
    ]

    print()
    for step, title, desc in steps:
        print(f"   {step}: {title}")
        print(f"        → {desc}")
    print()


def check_current_status():
    """현재 프로젝트 진행 상황"""
    print_header("📊 현재 진행 상황")

    print()

    # 1단계: 원본 음성
    raw_files = list(Path("data/raw").glob("*.wav"))
    if raw_files:
        print("✅ 1단계: 음성 데이터 수집 - 완료")
        print(f"   파일: {len(raw_files)}개")
        for f in raw_files:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"   - {f.name} ({size_mb:.1f}MB)")
    else:
        print("❌ 1단계: 음성 데이터 수집 - 미완료")

    print()

    # 2단계: 보컬 분리 (배경음악 제거)
    vocals_files = list(Path("data/vocals/tongtong").rglob("vocals.wav"))
    if vocals_files:
        print("✅ 2단계: 배경음악 제거 (보컬 분리) - 완료")
        print(f"   파일: {len(vocals_files)}개")
        for f in vocals_files:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"   - {f} ({size_mb:.1f}MB)")
    else:
        print("⏳ 2단계: 배경음악 제거 (보컬 분리) - 진행 필요")
        print("   실행: python scripts/remove_background_music.py")

    print()

    # 3단계: 전처리 (세그먼트 분할)
    processed_files = list(Path("data/processed/tongtong").glob("*.wav"))
    if processed_files:
        print("✅ 3단계: 전처리 (세그먼트 분할) - 완료")
        print(f"   세그먼트: {len(processed_files)}개")
        total_duration = len(processed_files) * 5  # 평균 5초
        print(f"   예상 데이터: 약 {total_duration // 60}분 {total_duration % 60}초")
    else:
        print("⏳ 3단계: 전처리 (세그먼트 분할) - 진행 필요")
        print("   실행: python scripts/train_single_audio.py")

    print()

    # 4단계: 메타데이터 (대본)
    transcript_file = Path("data/datasets/tongtong/transcript.txt")
    if transcript_file.exists():
        with open(transcript_file, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
        print("✅ 4단계: 메타데이터 (대본) - 완료")
        print(f"   대본: {lines}줄")
    else:
        print("⚠️  4단계: 메타데이터 (대본) - 선택사항")
        print("   (없어도 학습 가능, 있으면 품질 향상)")

    print()

    # 5단계: 모델 학습
    model_files = list(Path("models/gpt-sovits/tongtong").glob("*.pth"))
    if model_files:
        print("✅ 5단계: 모델 학습 - 완료")
        print(f"   모델: {len(model_files)}개")
        for f in model_files:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"   - {f.name} ({size_mb:.1f}MB)")
    else:
        print("⏳ 5단계: 모델 학습 - 진행 필요")
        print("   실행: python scripts/train_single_audio.py")

    print()


def calculate_progress():
    """진행률 계산"""
    print_header("📈 전체 진행률")

    steps_status = []

    # 1. 원본 음성
    steps_status.append(len(list(Path("data/raw").glob("*.wav"))) > 0)

    # 2. 보컬 분리
    steps_status.append(len(list(Path("data/vocals/tongtong").rglob("vocals.wav"))) > 0)

    # 3. 전처리
    steps_status.append(len(list(Path("data/processed/tongtong").glob("*.wav"))) > 0)

    # 4. 메타데이터 (선택)
    has_transcript = Path("data/datasets/tongtong/transcript.txt").exists()

    # 5. 모델 학습
    steps_status.append(len(list(Path("models/gpt-sovits/tongtong").glob("*.pth"))) > 0)

    # 진행률 계산 (대본 제외, 4단계 기준)
    completed = sum(steps_status)
    total = len(steps_status)
    progress = (completed / total) * 100

    print()
    print(f"완료된 단계: {completed}/{total}")
    print(f"진행률: {progress:.1f}%")

    # 진행 바
    bar_length = 50
    filled = int(bar_length * completed / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n[{bar}] {progress:.0f}%")
    print()

    return completed, total


def next_steps():
    """다음 단계 안내"""
    print_header("🎯 다음 단계")

    vocals_files = list(Path("data/vocals/tongtong").rglob("vocals.wav"))
    processed_files = list(Path("data/processed/tongtong").glob("*.wav"))
    model_files = list(Path("models/gpt-sovits/tongtong").glob("*.pth"))

    print()

    if not vocals_files:
        print("▶️  지금 해야 할 일:")
        print("   1. 배경음악 제거")
        print("      python scripts/remove_background_music.py")
        print()

    elif not processed_files:
        print("▶️  지금 해야 할 일:")
        print("   1. 전처리 + 모델 학습")
        print("      python scripts/train_single_audio.py")
        print()

    elif not model_files:
        print("▶️  지금 해야 할 일:")
        print("   1. 모델 학습")
        print("      python scripts/train_single_audio.py")
        print()

    else:
        print("🎉 모든 단계 완료!")
        print()
        print("▶️  테스트:")
        print("   1. 텍스트 챗봇 테스트")
        print("      python scripts/test_chatbot_simple.py")
        print()
        print("   2. 음성 대화 테스트")
        print("      python scripts/test_voice_chat.py")
        print()


def check_vocals_quality():
    """보컬 파일 품질 확인"""
    vocals_files = list(Path("data/vocals/tongtong").rglob("vocals.wav"))

    if not vocals_files:
        return

    print_header("🎧 보컬 파일 품질 확인")

    print()
    print("생성된 파일:")

    for f in vocals_files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"\n📁 {f}")
        print(f"   크기: {size_mb:.1f}MB")

        # 듣어보기
        print(f"\n   듣어보기:")
        print(f"   start {f}")
        print()

    print("💡 확인 사항:")
    print("   - 퉁퉁이 목소리만 들리는가?")
    print("   - 배경음악이 제거되었는가?")
    print("   - 음질이 깨끗한가?")
    print()


def main():
    """메인 함수"""
    print("\n" + "=" * 70)
    print("  🔍 퉁퉁이 AI 프로젝트 현황 체크")
    print("=" * 70)

    # 블로그 가이드라인
    check_blog_pipeline()

    # 현재 상황
    check_current_status()

    # 진행률
    completed, total = calculate_progress()

    # 보컬 품질 확인
    check_vocals_quality()

    # 다음 단계
    next_steps()

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
