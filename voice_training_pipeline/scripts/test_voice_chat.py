# -*- coding: utf-8 -*-
"""
음성 대화 테스트 (풀 파이프라인)
- Whisper (음성→텍스트)
- Gemini 2.0 Flash-Lite (대화 생성)
- GPT-SoVITS (텍스트→음성)
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.speech_to_text import create_stt
from tools.chatbot import create_chatbot
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_stt_only():
    """STT(음성 인식)만 테스트"""
    print("=" * 60)
    print("🎤 Whisper 음성 인식 테스트")
    print("=" * 60)
    print()

    # Whisper 초기화
    print("📦 Whisper 모델 로딩 중...")
    stt = create_stt(method="whisper", model_size="base")

    print("\n✅ 준비 완료! Enter를 누르면 5초간 녹음합니다.")
    input("Press Enter to start...")

    # 녹음 및 인식
    text = stt.record_and_transcribe(duration=5, language="ko")

    print("\n" + "=" * 60)
    print("📝 인식 결과:")
    print("=" * 60)
    print(f"{text}")
    print()


def test_chatbot_only():
    """챗봇만 테스트 (텍스트 입력)"""
    print("=" * 60)
    print("🤖 Gemini 2.0 Flash-Lite 챗봇 테스트")
    print("=" * 60)
    print()

    # 챗봇 초기화
    chatbot = create_chatbot(
        character_name="뽀로로",
        use_gemini=True
    )

    # 테스트 메시지
    test_messages = [
        "안녕! 너 이름이 뭐야?",
        "오늘 날씨가 좋은데 뭐 하고 놀까?",
        "너 가장 좋아하는 친구는 누구야?"
    ]

    for msg in test_messages:
        print(f"👤 사용자: {msg}")
        response = chatbot.get_response(msg)
        print(f"🐧 뽀로로: {response}\n")


def test_full_pipeline():
    """전체 파이프라인 테스트 (음성 대화)"""
    print("=" * 60)
    print("🎭 AI 음성 캐릭터 - 풀 파이프라인 테스트")
    print("=" * 60)
    print()

    # 1. 초기화
    print("📦 모듈 로딩 중...")
    print("  ⏳ Whisper 로딩...")
    stt = create_stt(method="whisper", model_size="base")

    print("  ⏳ Gemini 챗봇 초기화...")
    chatbot = create_chatbot(
        character_name="뽀로로",
        personality_traits=["호기심 많음", "장난기 많음", "모험을 좋아함"],
        speech_style="밝고 경쾌한 말투",
        use_gemini=True
    )

    print("  ⏳ TTS 준비...")
    # TODO: GPT-SoVITS 통합 (모델 학습 후)
    tts_available = False

    print("\n✅ 모든 모듈 로드 완료!")
    print()

    # 2. 대화 루프
    print("=" * 60)
    print("💬 음성 대화를 시작합니다!")
    print("   - Enter: 녹음 시작 (5초)")
    print("   - Ctrl+C: 종료")
    if not tts_available:
        print("   ⚠️ TTS 미사용 (텍스트 출력만)")
    print("=" * 60)
    print()

    conversation_count = 0

    while True:
        try:
            # 사용자 입력 대기
            input("\n✋ Enter를 누르면 녹음 시작...")

            # 음성 녹음 및 인식
            print("🎤 녹음 중... (5초)")
            user_text = stt.record_and_transcribe(duration=5, language="ko")

            if not user_text.strip():
                print("⚠️ 음성이 인식되지 않았습니다. 다시 시도해주세요.")
                continue

            print(f"\n📝 인식됨: {user_text}")

            # 종료 명령 확인
            if any(word in user_text for word in ["종료", "끝", "그만"]):
                print(f"\n🐧 뽀로로: 안녕! 다음에 또 놀자! 👋")
                break

            # 대화 생성
            print("🤖 뽀로로 생각 중...")
            response = chatbot.get_response(user_text)
            print(f"\n💬 뽀로로: {response}")

            # TTS (사용 가능한 경우)
            if tts_available:
                print("🎵 음성 생성 중...")
                # TODO: TTS 통합
                # tts.synthesize(response)
                # tts.play_audio()
            else:
                print("   (텍스트만 출력 - TTS 미구현)")

            conversation_count += 1

        except KeyboardInterrupt:
            print(f"\n\n🐧 뽀로로: 안녕! 다음에 또 놀자! 👋")
            break

        except Exception as e:
            logger.error(f"오류 발생: {e}")
            print(f"❌ 오류: {e}")
            continue

    # 통계 출력
    print("\n" + "=" * 60)
    print("📊 대화 통계")
    print("=" * 60)
    print(f"총 대화 수: {conversation_count}회")
    print(f"STT: Whisper (로컬) - $0.00")
    print(f"LLM: Gemini 2.0 Flash-Lite - $0.00 (무료 티어)")
    print(f"TTS: {'GPT-SoVITS (로컬) - $0.00' if tts_available else '미사용'}")
    print()


def main():
    """메인 함수"""
    print("\n🎯 테스트 모드 선택:")
    print("1. STT만 테스트 (음성 인식)")
    print("2. 챗봇만 테스트 (텍스트 대화)")
    print("3. 풀 파이프라인 (음성 대화)")
    print()

    choice = input("선택 (1-3): ").strip()

    try:
        if choice == "1":
            test_stt_only()
        elif choice == "2":
            test_chatbot_only()
        elif choice == "3":
            test_full_pipeline()
        else:
            print("❌ 잘못된 선택입니다.")
            return

    except Exception as e:
        logger.error(f"테스트 실패: {e}", exc_info=True)
        print(f"\n❌ 테스트 실패: {e}")
        print("\n💡 문제 해결:")
        print("1. .env 파일에 GEMINI_API_KEY가 설정되어 있는지 확인")
        print("2. 필요한 패키지 설치: pip install -r requirements.txt")
        print("3. 마이크가 연결되어 있는지 확인 (STT 테스트 시)")


if __name__ == "__main__":
    main()
