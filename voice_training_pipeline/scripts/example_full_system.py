# -*- coding: utf-8 -*-
"""
전체 시스템 예제 - Gemini API 사용 위치 명확히 보여주기
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.speech_to_text import create_stt
from tools.chatbot import create_chatbot
# from tools.text_to_speech import CharacterTTS  # 학습 후 사용
from dotenv import load_dotenv

load_dotenv()


def example_without_voice():
    """
    예제 1: 음성 없이 텍스트만 (Gemini만 사용)
    - 음성 학습 전에도 테스트 가능
    - Gemini API만 필요
    """
    print("=" * 70)
    print("📝 예제 1: 텍스트 챗봇 (Gemini만 사용)")
    print("=" * 70)
    print()

    # ⭐ 여기서 Gemini API 사용!
    chatbot = create_chatbot(
        character_name="퉁퉁이",
        personality_traits=[
            "순수함",
            "힘이 셈",
            "느리지만 착함"
        ],
        speech_style="느리고 굵은 목소리, 단순한 말투",
        use_gemini=True  # ← Gemini 2.0 Flash-Lite 사용
    )

    # 대화 예시
    conversations = [
        "퉁퉁아, 너 이름이 뭐야?",
        "오늘 뭐하고 놀까?",
        "너 가장 좋아하는 친구는 누구야?"
    ]

    for user_input in conversations:
        print(f"👤 사용자: {user_input}")

        # ⭐ Gemini API 호출 (대화 생성)
        response = chatbot.get_response(user_input)

        print(f"🐻 퉁퉁이: {response}\n")

    print("\n💡 이 예제에서 Gemini가 한 일:")
    print("   - 사용자 질문 이해")
    print("   - 퉁퉁이 성격에 맞는 대답 생성")
    print("   - 대화 맥락 기억")
    print()
    print("💰 비용: $0.00 (무료 티어)")


def example_with_voice_input():
    """
    예제 2: 음성 입력 추가 (Whisper + Gemini)
    - 마이크 필요
    - Whisper + Gemini API 사용
    """
    print("\n" + "=" * 70)
    print("🎤 예제 2: 음성 입력 + 텍스트 출력 (Whisper + Gemini)")
    print("=" * 70)
    print()

    # 1. Whisper 초기화 (음성→텍스트)
    print("📦 Whisper 로딩...")
    stt = create_stt(method="whisper", model_size="base")

    # 2. Gemini 챗봇 초기화 (대화 생성)
    print("📦 Gemini 챗봇 초기화...")
    chatbot = create_chatbot(
        character_name="퉁퉁이",
        personality_traits=["순수함", "힘이 셈"],
        speech_style="느리고 굵은 목소리",
        use_gemini=True  # ← Gemini API 사용
    )

    print("\n✅ 준비 완료!\n")
    print("Enter를 누르면 5초간 녹음합니다...")
    input()

    # 3. 음성 녹음 및 인식 (Whisper 사용)
    print("🎤 녹음 중... (5초)")
    user_text = stt.record_and_transcribe(duration=5, language="ko")
    print(f"\n📝 인식됨: {user_text}\n")

    if not user_text.strip():
        print("⚠️ 음성이 인식되지 않았습니다.")
        return

    # 4. ⭐ Gemini API로 대화 생성
    print("🤖 퉁퉁이 생각 중...")
    response = chatbot.get_response(user_text)
    print(f"🐻 퉁퉁이: {response}\n")

    print("\n💡 이 예제에서 각 도구가 한 일:")
    print("   1. Whisper: 음성→텍스트 (로컬, 무료)")
    print("   2. ⭐ Gemini: 대답 생성 (API, 무료)")
    print("   3. (TTS 없음: 텍스트로만 출력)")
    print()
    print("💰 비용: $0.00 (모두 무료)")


def example_full_pipeline():
    """
    예제 3: 완전한 음성 대화 (Whisper + Gemini + GPT-SoVITS)
    - 퉁퉁이 음성 모델 학습 필요
    - 전체 파이프라인 사용
    """
    print("\n" + "=" * 70)
    print("🎭 예제 3: 완전한 음성 대화 (전체 파이프라인)")
    print("=" * 70)
    print()

    # 1. Whisper (음성→텍스트)
    print("📦 Whisper 로딩...")
    stt = create_stt(method="whisper", model_size="base")

    # 2. Gemini 챗봇 (대화 생성)
    print("📦 Gemini 챗봇 초기화...")
    chatbot = create_chatbot(
        character_name="퉁퉁이",
        personality_traits=["순수함", "힘이 셈"],
        use_gemini=True  # ← Gemini API
    )

    # 3. GPT-SoVITS TTS (텍스트→음성)
    print("📦 퉁퉁이 TTS 모델 로딩...")

    # 모델 존재 확인
    model_dir = project_root / "models" / "gpt_sovits" / "tongtong"
    if not model_dir.exists():
        print("❌ 퉁퉁이 음성 모델이 없습니다!")
        print("💡 먼저 음성 학습을 완료하세요:")
        print("   python scripts/quick_start_tongtong.py")
        return

    # TTS 로드 (주석 해제 - 학습 후)
    # tts = CharacterTTS(character_name="tongtong")

    print("\n✅ 모든 모듈 준비 완료!\n")
    print("Enter를 누르면 대화 시작...")
    input()

    # 대화 루프
    while True:
        try:
            # 3-1. 음성 입력 (Whisper)
            print("\n🎤 녹음 중... (5초)")
            user_text = stt.record_and_transcribe(duration=5, language="ko")

            if not user_text.strip():
                print("⚠️ 음성이 인식되지 않았습니다.")
                continue

            print(f"\n📝 인식됨: {user_text}")

            # 종료 명령
            if "종료" in user_text or "끝" in user_text:
                print("\n🐻 퉁퉁이: 안녕! 다음에 또 놀자!")
                break

            # 3-2. ⭐ Gemini로 대답 생성
            print("🤖 퉁퉁이 생각 중...")
            response = chatbot.get_response(user_text)
            print(f"\n💬 퉁퉁이: {response}")

            # 3-3. TTS로 음성 생성 (주석 해제 - 학습 후)
            # print("🎵 음성 생성 중...")
            # output_path = "output/audio/response.wav"
            # tts.synthesize(response, output_path)
            #
            # print("🔊 재생 중...")
            # tts.play_audio(output_path)

            print("\n   (TTS 미구현 - 텍스트로만 출력)")

        except KeyboardInterrupt:
            print("\n\n🐻 퉁퉁이: 안녕!")
            break
        except Exception as e:
            print(f"\n❌ 오류: {e}")
            continue

    print("\n💡 이 예제에서 각 도구가 한 일:")
    print("   1. Whisper: 음성→텍스트 (로컬, 무료)")
    print("   2. ⭐ Gemini: 대답 생성 (API, 무료)")
    print("   3. GPT-SoVITS: 텍스트→퉁퉁이 음성 (로컬, 무료)")
    print()
    print("💰 총 비용: $0.00 (모두 무료!)")


def show_gemini_role():
    """
    Gemini의 역할 명확히 설명
    """
    print("\n" + "=" * 70)
    print("🔍 Gemini API의 역할")
    print("=" * 70)
    print()

    print("📌 Gemini는 '대화 내용 생성'만 담당합니다")
    print()
    print("예시:")
    print("   입력: '퉁퉁아, 오늘 뭐하고 놀까?'")
    print("   ↓ (⭐ Gemini 처리)")
    print("   출력: '음... 나는 축구하고 싶어! 너도 같이?'")
    print()
    print("=" * 70)
    print()

    print("🔧 각 도구의 역할:")
    print()
    print("1️⃣  Whisper (OpenAI)")
    print("   역할: 음성→텍스트")
    print("   예시: [음성 녹음] → '퉁퉁아 안녕'")
    print("   비용: 무료 (로컬)")
    print()

    print("2️⃣  ⭐ Gemini 2.0 Flash-Lite (Google)")
    print("   역할: 대화 생성 (퉁퉁이처럼 대답)")
    print("   예시: '퉁퉁아 안녕' → '안녕! 나는 퉁퉁이야!'")
    print("   비용: 무료 (15 RPM, 500 RPD)")
    print()

    print("3️⃣  GPT-SoVITS (로컬)")
    print("   역할: 텍스트→음성 (퉁퉁이 목소리)")
    print("   예시: '안녕! 나는 퉁퉁이야!' → [퉁퉁이 음성]")
    print("   비용: 무료 (로컬)")
    print()

    print("=" * 70)
    print()

    print("❓ 자주 묻는 질문:")
    print()
    print("Q: Gemini가 퉁퉁이 목소리를 학습하나요?")
    print("A: ❌ 아니요. Gemini는 '무슨 말을 할지'만 정합니다.")
    print("   목소리는 GPT-SoVITS가 학습합니다.")
    print()

    print("Q: Gemini가 음성을 인식하나요?")
    print("A: ❌ 아니요. 음성 인식은 Whisper가 합니다.")
    print("   Gemini는 텍스트만 받습니다.")
    print()

    print("Q: Gemini 없이도 가능한가요?")
    print("A: ✅ 가능합니다! GPT-3.5-turbo 등 다른 LLM 사용 가능")
    print("   하지만 Gemini가 가장 저렴합니다 (무료)")
    print()


def main():
    """메인 함수"""
    print("\n🎯 Gemini API 사용 위치 이해하기\n")

    print("선택하세요:")
    print("1. Gemini 역할 설명 보기")
    print("2. 예제 1: 텍스트 챗봇 (Gemini만)")
    print("3. 예제 2: 음성 입력 (Whisper + Gemini)")
    print("4. 예제 3: 완전한 시스템 (Whisper + Gemini + TTS)")
    print()

    choice = input("선택 (1-4): ").strip()

    if choice == '1':
        show_gemini_role()
    elif choice == '2':
        example_without_voice()
    elif choice == '3':
        example_with_voice_input()
    elif choice == '4':
        example_full_pipeline()
    else:
        print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
