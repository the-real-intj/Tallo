# -*- coding: utf-8 -*-
"""
퉁퉁이 캐릭터 빠른 시작 스크립트
- 단계별로 실행 가능
- 처음부터 끝까지 가이드
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


def print_banner():
    """배너 출력"""
    print("\n" + "=" * 70)
    print("🐻 퉁퉁이 AI 캐릭터 만들기 - 빠른 시작")
    print("=" * 70)
    print()


def print_step(step_num, title):
    """단계 제목 출력"""
    print("\n" + "-" * 70)
    print(f"📍 {step_num}단계: {title}")
    print("-" * 70)


def check_youtube_urls():
    """유튜브 URL 설정 확인"""
    import yaml

    config_path = project_root / "configs" / "character_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    urls = config['characters']['tongtong']['youtube_urls']

    # EXAMPLE URL 확인
    has_example = any("EXAMPLE" in url for url in urls)

    if has_example:
        print("⚠️  아직 유튜브 URL을 설정하지 않았습니다!")
        print()
        print("📝 다음 단계를 따라하세요:")
        print()
        print("1. 유튜브에서 '뽀로로 퉁퉁이' 검색")
        print("   추천 검색어: '뽀로로 퉁퉁이 모음', '뽀로로 시즌1'")
        print()
        print("2. 영상 URL 복사 (5-10개)")
        print("   예: https://www.youtube.com/watch?v=abc123")
        print()
        print("3. configs/character_config.yaml 파일 열기")
        print()
        print("4. tongtong → youtube_urls 부분 수정:")
        print("""
    youtube_urls:
      - "https://www.youtube.com/watch?v=실제URL1"
      - "https://www.youtube.com/watch?v=실제URL2"
      - "https://www.youtube.com/watch?v=실제URL3"
        """)
        print()
        return False
    else:
        print(f"✅ 유튜브 URL 설정됨: {len(urls)}개")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")
        return True


def step1_download():
    """1단계: 유튜브 다운로드"""
    print_step(1, "유튜브에서 퉁퉁이 음성 다운로드")

    if not check_youtube_urls():
        print("\n❌ URL을 먼저 설정해주세요!")
        return False

    print("\n💡 지금 다운로드를 시작하시겠습니까?")
    print("   예상 시간: 5-10분")
    print()

    choice = input("계속하려면 'y'를 입력하세요 (y/n): ").strip().lower()

    if choice != 'y':
        print("⏸️  다운로드를 건너뜁니다.")
        return False

    try:
        from tools.youtube_downloader import YouTubeAudioDownloader
        import yaml

        # 설정 로드
        config_path = project_root / "configs" / "character_config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        urls = config['characters']['tongtong']['youtube_urls']

        # 다운로더 생성
        downloader = YouTubeAudioDownloader(
            output_dir=str(project_root / "data" / "raw")
        )

        print(f"\n🎬 {len(urls)}개 영상 다운로드 시작...\n")

        downloaded_files = []
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] 다운로드 중: {url}")
            try:
                file_path = downloader.download_audio(url, character_name="tongtong")
                downloaded_files.append(file_path)
                print(f"✅ 완료: {file_path}\n")
            except Exception as e:
                print(f"❌ 실패: {e}\n")

        print(f"\n✅ 다운로드 완료! {len(downloaded_files)}개 파일")
        print(f"📁 저장 위치: {project_root / 'data' / 'raw'}")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n💡 해결 방법:")
        print("1. pip install yt-dlp pytube")
        print("2. FFmpeg 설치 확인")
        return False


def step2_separate():
    """2단계: 보컬 분리"""
    print_step(2, "배경음악 제거 (보컬 분리)")

    # 다운로드된 파일 확인
    raw_dir = project_root / "data" / "raw"
    audio_files = list(raw_dir.glob("tongtong*.mp3")) + list(raw_dir.glob("tongtong*.wav"))

    if not audio_files:
        print("❌ 다운로드된 파일이 없습니다!")
        print("💡 1단계를 먼저 실행하세요.")
        return False

    print(f"\n📂 발견된 파일: {len(audio_files)}개")
    for f in audio_files:
        print(f"   - {f.name}")

    print("\n💡 배경음악을 제거하고 순수한 목소리만 추출합니다.")
    print("   예상 시간: 5-15분")
    print()

    choice = input("계속하려면 'y'를 입력하세요 (y/n): ").strip().lower()

    if choice != 'y':
        print("⏸️  보컬 분리를 건너뜁니다.")
        return False

    try:
        from tools.vocal_separator import VocalSeparator

        separator = VocalSeparator(method="spleeter")

        print(f"\n🎵 {len(audio_files)}개 파일 처리 중...\n")

        for i, audio_file in enumerate(audio_files, 1):
            print(f"[{i}/{len(audio_files)}] 처리 중: {audio_file.name}")
            try:
                vocals_path = separator.separate(
                    input_path=str(audio_file),
                    output_dir=str(project_root / "data" / "vocals" / "tongtong"),
                    stems="2stems"
                )
                print(f"✅ 완료: {vocals_path}\n")
            except Exception as e:
                print(f"❌ 실패: {e}\n")

        print(f"\n✅ 보컬 분리 완료!")
        print(f"📁 저장 위치: {project_root / 'data' / 'vocals' / 'tongtong'}")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n💡 해결 방법:")
        print("1. pip install spleeter")
        print("2. 또는 demucs 사용: pip install demucs")
        return False


def step3_preprocess():
    """3단계: 전처리"""
    print_step(3, "음성 전처리 (노이즈 제거, 세그먼트 분할)")

    # 보컬 파일 확인
    vocals_dir = project_root / "data" / "vocals" / "tongtong"

    if not vocals_dir.exists():
        print("❌ 보컬 파일이 없습니다!")
        print("💡 2단계를 먼저 실행하세요.")
        return False

    vocal_files = list(vocals_dir.rglob("vocals.wav"))

    if not vocal_files:
        print("❌ 보컬 파일이 없습니다!")
        return False

    print(f"\n📂 발견된 보컬 파일: {len(vocal_files)}개")

    print("\n💡 음성을 3-10초 구간으로 나누고 노이즈를 제거합니다.")
    print("   예상 시간: 5-10분")
    print()

    choice = input("계속하려면 'y'를 입력하세요 (y/n): ").strip().lower()

    if choice != 'y':
        print("⏸️  전처리를 건너뜁니다.")
        return False

    try:
        from tools.audio_preprocessor import AudioPreprocessor

        preprocessor = AudioPreprocessor(sample_rate=22050)

        print(f"\n🔧 {len(vocal_files)}개 파일 전처리 중...\n")

        all_segments = []

        for i, vocal_file in enumerate(vocal_files, 1):
            print(f"[{i}/{len(vocal_files)}] 처리 중: {vocal_file.name}")
            try:
                segments = preprocessor.process_audio(
                    input_path=str(vocal_file),
                    output_dir=str(project_root / "data" / "processed" / "tongtong"),
                    character_name="tongtong",
                    enable_noise_reduction=True,
                    enable_normalization=True,
                    segment_config={
                        'min_length': 3.0,
                        'max_length': 10.0,
                        'overlap': 0.5
                    }
                )
                all_segments.extend(segments)
                print(f"✅ 완료: {len(segments)}개 세그먼트 생성\n")
            except Exception as e:
                print(f"❌ 실패: {e}\n")

        print(f"\n✅ 전처리 완료! 총 {len(all_segments)}개 세그먼트")
        print(f"📁 저장 위치: {project_root / 'data' / 'processed' / 'tongtong'}")

        # 총 시간 계산
        total_duration = len(all_segments) * 5  # 평균 5초로 가정
        print(f"⏱️  예상 학습 데이터 길이: 약 {total_duration // 60}분 {total_duration % 60}초")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False


def step4_transcript():
    """4단계: 대본 생성 (선택)"""
    print_step(4, "대본 생성 (선택사항)")

    print("\n💡 Whisper로 음성을 텍스트로 변환합니다.")
    print("   - GPT-SoVITS는 대본이 있으면 품질이 더 좋습니다")
    print("   - 하지만 없어도 학습 가능합니다")
    print()
    print("   예상 시간: 10-30분")
    print()

    choice = input("대본을 생성하시겠습니까? (y/n): ").strip().lower()

    if choice != 'y':
        print("⏸️  대본 생성을 건너뜁니다.")
        return True  # 선택사항이므로 True 반환

    try:
        from tools.speech_to_text import create_stt
        import os

        # Whisper 초기화
        print("\n📦 Whisper 모델 로딩 중... (처음에만 오래 걸립니다)")
        stt = create_stt(method="whisper", model_size="medium")

        # 세그먼트 파일 확인
        segment_dir = project_root / "data" / "processed" / "tongtong"
        segment_files = sorted(segment_dir.glob("*.wav"))

        if not segment_files:
            print("❌ 전처리된 파일이 없습니다!")
            return False

        print(f"\n🎤 {len(segment_files)}개 파일 텍스트 변환 중...\n")

        # 대본 파일 생성
        dataset_dir = project_root / "data" / "datasets" / "tongtong"
        dataset_dir.mkdir(parents=True, exist_ok=True)

        transcript_file = dataset_dir / "transcript.txt"

        with open(transcript_file, 'w', encoding='utf-8') as f:
            for i, audio_file in enumerate(segment_files, 1):
                print(f"[{i}/{len(segment_files)}] 변환 중: {audio_file.name}")
                try:
                    result = stt.transcribe_file(str(audio_file), language="ko")
                    text = result["text"].strip()

                    # 파일명|텍스트 형식
                    f.write(f"{audio_file.name}|{text}\n")
                    print(f"   → {text}\n")

                except Exception as e:
                    print(f"   ❌ 실패: {e}\n")

        print(f"\n✅ 대본 생성 완료!")
        print(f"📁 저장 위치: {transcript_file}")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n💡 해결 방법:")
        print("1. pip install openai-whisper")
        return False


def step5_train():
    """5단계: 모델 학습"""
    print_step(5, "GPT-SoVITS 모델 학습")

    print("\n💡 퉁퉁이 목소리를 학습합니다.")
    print("   - GPU: 1-3시간")
    print("   - CPU: 6-12시간 (느림)")
    print()
    print("⚠️  이 단계는 시간이 오래 걸립니다!")
    print()

    choice = input("지금 학습을 시작하시겠습니까? (y/n): ").strip().lower()

    if choice != 'y':
        print("\n⏸️  학습을 건너뜁니다.")
        print("\n💡 나중에 학습하려면:")
        print("   python scripts/train_multiple_characters.py --character tongtong")
        return False

    try:
        print("\n🤖 학습 시작...\n")
        print("💡 학습 중에는 다른 작업을 하셔도 됩니다.")
        print("   진행 상황은 logs/training.log 에서 확인할 수 있습니다.")
        print()

        # 학습 스크립트 실행
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "train_multiple_characters.py"),
                "--character", "tongtong"
            ],
            cwd=str(project_root)
        )

        if result.returncode == 0:
            print("\n✅ 학습 완료!")
            print(f"📁 모델 저장 위치: {project_root / 'models' / 'gpt_sovits' / 'tongtong'}")
            return True
        else:
            print("\n❌ 학습 실패!")
            return False

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False


def step6_test():
    """6단계: 모델 테스트"""
    print_step(6, "모델 테스트")

    # 모델 존재 확인
    model_dir = project_root / "models" / "gpt_sovits" / "tongtong"

    if not model_dir.exists():
        print("❌ 학습된 모델이 없습니다!")
        print("💡 5단계를 먼저 실행하세요.")
        return False

    print("\n💡 퉁퉁이 목소리로 테스트 문장을 생성합니다.")
    print()

    test_sentences = [
        "안녕? 나는 퉁퉁이야!",
        "너희들 뭐하니?",
        "나도 같이 놀고 싶어!",
        "엄마... 보고 싶어",
        "내가 제일 힘이 세!"
    ]

    print("📝 테스트 문장:")
    for i, text in enumerate(test_sentences, 1):
        print(f"   {i}. {text}")

    print()
    choice = input("테스트를 시작하시겠습니까? (y/n): ").strip().lower()

    if choice != 'y':
        print("⏸️  테스트를 건너뜁니다.")
        return False

    try:
        from tools.text_to_speech import CharacterTTS

        print("\n🎤 TTS 모델 로딩 중...")
        tts = CharacterTTS(character_name="tongtong")

        output_dir = project_root / "output" / "audio" / "tongtong_test"
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n🎵 {len(test_sentences)}개 문장 생성 중...\n")

        for i, text in enumerate(test_sentences, 1):
            print(f"[{i}/{len(test_sentences)}] 생성 중: {text}")
            try:
                output_path = output_dir / f"test_{i}.wav"
                tts.synthesize(text, str(output_path))
                print(f"✅ 완료: {output_path}\n")

                # 자동 재생 (선택)
                play = input("   재생하시겠습니까? (y/n): ").strip().lower()
                if play == 'y':
                    tts.play_audio(str(output_path))

            except Exception as e:
                print(f"❌ 실패: {e}\n")

        print(f"\n✅ 테스트 완료!")
        print(f"📁 저장 위치: {output_dir}")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False


def main():
    """메인 함수"""
    print_banner()

    print("🎯 이 스크립트는 처음부터 끝까지 퉁퉁이 캐릭터를 만듭니다.")
    print()
    print("📋 전체 단계:")
    print("   1. 유튜브 다운로드 (5-10분)")
    print("   2. 보컬 분리 (5-15분)")
    print("   3. 전처리 (5-10분)")
    print("   4. 대본 생성 (10-30분, 선택)")
    print("   5. 모델 학습 (1-12시간)")
    print("   6. 모델 테스트 (5분)")
    print()
    print("💡 각 단계를 개별적으로 실행할 수 있습니다.")
    print()

    # 메뉴
    while True:
        print("\n" + "=" * 70)
        print("📍 어떤 단계를 실행하시겠습니까?")
        print("=" * 70)
        print("1. 1단계: 유튜브 다운로드")
        print("2. 2단계: 보컬 분리")
        print("3. 3단계: 전처리")
        print("4. 4단계: 대본 생성 (선택)")
        print("5. 5단계: 모델 학습")
        print("6. 6단계: 모델 테스트")
        print()
        print("0. 전체 실행 (1-6단계 모두)")
        print("q. 종료")
        print()

        choice = input("선택 (0-6, q): ").strip().lower()

        if choice == 'q':
            print("\n👋 프로그램을 종료합니다!")
            break

        elif choice == '0':
            print("\n🚀 전체 파이프라인 실행!")
            step1_download()
            step2_separate()
            step3_preprocess()
            step4_transcript()
            step5_train()
            step6_test()
            print("\n🎉 모든 단계 완료!")
            break

        elif choice == '1':
            step1_download()
        elif choice == '2':
            step2_separate()
        elif choice == '3':
            step3_preprocess()
        elif choice == '4':
            step4_transcript()
        elif choice == '5':
            step5_train()
        elif choice == '6':
            step6_test()
        else:
            print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
