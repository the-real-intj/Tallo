# -*- coding: utf-8 -*-
"""
간단한 텍스트 챗봇 테스트
- Gemini 2.0 Flash-Lite 사용
- 텍스트 입력/출력만 (음성 없음)
"""

import sys
import os
import logging
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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


def main():
    """간단한 텍스트 챗봇 테스트"""

    print("=" * 60)
    print("🤖 Gemini 2.0 Flash-Lite 텍스트 챗봇 테스트")
    print("=" * 60)
    print()

    # 캐릭터 설정
    character_name = "뽀로로"
    personality_traits = [
        "호기심 많음",
        "장난기 많음",
        "모험을 좋아함",
        "친구들을 아낌"
    ]
    speech_style = "밝고 경쾌한 말투, 반말 사용"

    print(f"📋 캐릭터: {character_name}")
    print(f"📋 성격: {', '.join(personality_traits)}")
    print(f"📋 말투: {speech_style}")
    print()

    # 챗봇 초기화
    try:
        chatbot = create_chatbot(
            character_name=character_name,
            personality_traits=personality_traits,
            speech_style=speech_style,
            use_gemini=True  # Gemini 2.0 Flash-Lite 사용
        )
        print("✅ 챗봇 초기화 완료!\n")

    except ValueError as e:
        print(f"❌ 오류: {e}")
        print("\n💡 해결 방법:")
        print("1. https://aistudio.google.com/app/apikey 에서 API 키 발급")
        print("2. .env 파일에 GEMINI_API_KEY 추가")
        return

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return

    # 대화 시작
    print("=" * 60)
    print("💬 대화를 시작합니다! ('종료', 'exit', 'quit' 입력 시 종료)")
    print("=" * 60)
    print()

    while True:
        try:
            # 사용자 입력
            user_input = input("👤 당신: ").strip()

            if not user_input:
                continue

            # 종료 명령
            if user_input.lower() in ["종료", "exit", "quit", "그만"]:
                print(f"\n🐧 {character_name}: 안녕! 다음에 또 놀자! 👋")
                break

            # 특수 명령
            if user_input == "/reset":
                chatbot.reset_conversation()
                print("🔄 대화 히스토리가 초기화되었습니다.\n")
                continue

            if user_input == "/history":
                print("\n📜 대화 히스토리:")
                history = chatbot.get_conversation_history()
                for i, msg in enumerate(history, 1):
                    role = "당신" if msg["role"] == "user" else character_name
                    print(f"  {i}. {role}: {msg['content']}")
                print()
                continue

            # 응답 생성
            response = chatbot.get_response(user_input)
            print(f"🐧 {character_name}: {response}\n")

        except KeyboardInterrupt:
            print(f"\n\n🐧 {character_name}: 안녕! 다음에 또 놀자! 👋")
            break

        except Exception as e:
            logger.error(f"오류 발생: {e}")
            print(f"❌ 오류가 발생했습니다: {e}\n")
            continue

    # 종료 시 통계 출력
    history = chatbot.get_conversation_history()
    print("\n" + "=" * 60)
    print(f"📊 대화 통계")
    print("=" * 60)
    print(f"총 대화 수: {len(history) // 2}회")
    print(f"사용 모델: Gemini 2.0 Flash-Lite")
    print(f"예상 비용: $0.00 (무료 티어)")
    print()


if __name__ == "__main__":
    main()
