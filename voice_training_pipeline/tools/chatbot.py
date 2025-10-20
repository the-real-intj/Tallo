# -*- coding: utf-8 -*-
"""
AI 챗봇 모듈
- Gemini 2.0 Flash-Lite (최저가)
- GPT-3.5-turbo (대안)
"""

import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiFlashLiteChatbot:
    """
    Gemini 2.0 Flash-Lite 챗봇
    - 가장 비용 효율적인 모델
    - 무료 티어: 15 RPM, 500 RPD, 250K TPM
    """

    def __init__(
        self,
        character_name: str = "뽀로로",
        personality_traits: Optional[List[str]] = None,
        speech_style: str = "밝고 경쾌한 말투"
    ):
        """
        Args:
            character_name: 캐릭터 이름
            personality_traits: 성격 특성 리스트
            speech_style: 말투 스타일
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai 패키지가 필요합니다.\n"
                "설치: pip install google-generativeai"
            )

        # API 키 설정
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다.\n"
                ".env 파일에 API 키를 추가하세요.\n"
                "발급: https://aistudio.google.com/app/apikey"
            )

        genai.configure(api_key=api_key)

        # 캐릭터 설정
        self.character_name = character_name
        self.personality_traits = personality_traits or [
            "호기심 많음",
            "장난기 많음",
            "친구들을 좋아함"
        ]
        self.speech_style = speech_style

        # 시스템 프롬프트 생성
        self.system_prompt = self._create_system_prompt()

        # 모델 초기화 (Gemini 2.0 Flash-Lite)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            system_instruction=self.system_prompt,
            generation_config={
                "temperature": 0.9,  # 창의적인 대답
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 200,  # 짧은 대답 (비용 절감)
            }
        )

        # 대화 히스토리
        self.chat = self.model.start_chat(history=[])

        logger.info(f"✅ Gemini 2.0 Flash-Lite 챗봇 초기화 완료: {character_name}")

    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        traits_str = ", ".join(self.personality_traits)

        return f"""당신은 {self.character_name}입니다.

**성격 특성:**
{traits_str}

**말투 규칙:**
- {self.speech_style}
- "~야!", "~어!", "와!" 같은 감탄사 자주 사용
- 짧고 명확한 문장 (1-3 문장)
- 반말 사용
- 이모티콘 가끔 사용 (😊, 🎉 등)

**대답 가이드:**
- 캐릭터의 성격을 유지하세요
- 자연스럽고 친근하게 대답하세요
- 너무 길지 않게 (2-3 문장 권장)
- {self.character_name}처럼 행동하세요

항상 {self.character_name}의 입장에서 대답해주세요!
"""

    def get_response(self, user_message: str) -> str:
        """
        사용자 메시지에 대한 응답 생성

        Args:
            user_message: 사용자 입력 텍스트

        Returns:
            캐릭터의 응답 텍스트
        """
        try:
            response = self.chat.send_message(user_message)
            return response.text.strip()

        except Exception as e:
            logger.error(f"❌ Gemini API 오류: {e}")

            # 에러 메시지에 따른 대응
            error_msg = str(e).lower()

            if "quota" in error_msg or "rate limit" in error_msg:
                return "잠깐만... 너무 빨리 물어봤어! 조금만 기다려줘! 😅"
            elif "api key" in error_msg:
                raise ValueError("API 키가 유효하지 않습니다. .env 파일을 확인하세요.")
            else:
                return "어... 잠깐 생각이 안 나! 다시 한 번 말해줄래? 😊"

    def reset_conversation(self):
        """대화 히스토리 초기화"""
        self.chat = self.model.start_chat(history=[])
        logger.info("🔄 대화 히스토리 초기화")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """대화 히스토리 조회"""
        history = []
        for msg in self.chat.history:
            history.append({
                "role": msg.role,
                "content": msg.parts[0].text
            })
        return history


class OpenAIChatbot:
    """
    OpenAI GPT-3.5-turbo 챗봇 (대안)
    - Gemini가 안 될 때 사용
    """

    def __init__(
        self,
        character_name: str = "뽀로로",
        personality_traits: Optional[List[str]] = None,
        speech_style: str = "밝고 경쾌한 말투",
        model: str = "gpt-3.5-turbo"
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai 패키지가 필요합니다.\n"
                "설치: pip install openai>=1.0.0"
            )

        # API 키 설정
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY가 설정되지 않았습니다.\n"
                ".env 파일에 API 키를 추가하세요."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

        # 캐릭터 설정
        self.character_name = character_name
        self.personality_traits = personality_traits or [
            "호기심 많음",
            "장난기 많음"
        ]
        self.speech_style = speech_style

        # 시스템 프롬프트
        traits_str = ", ".join(self.personality_traits)
        self.system_prompt = f"""당신은 {character_name}입니다.

성격: {traits_str}
말투: {speech_style}

규칙:
- 짧고 명확한 문장 (1-3 문장)
- 반말 사용
- {character_name}처럼 대답하세요
"""

        # 대화 히스토리
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        logger.info(f"✅ OpenAI {model} 챗봇 초기화 완료: {character_name}")

    def get_response(self, user_message: str) -> str:
        """사용자 메시지에 대한 응답 생성"""
        try:
            self.messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                max_tokens=150,
                temperature=0.8
            )

            assistant_message = response.choices[0].message.content.strip()
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            logger.error(f"❌ OpenAI API 오류: {e}")
            return "어... 잠깐 생각이 안 나! 다시 한 번 말해줄래? 😊"

    def reset_conversation(self):
        """대화 히스토리 초기화"""
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        logger.info("🔄 대화 히스토리 초기화")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """대화 히스토리 조회"""
        return [msg for msg in self.messages if msg["role"] != "system"]


def create_chatbot(
    character_name: str = "뽀로로",
    use_gemini: bool = True,
    **kwargs
):
    """
    챗봇 팩토리 함수

    Args:
        character_name: 캐릭터 이름
        use_gemini: True면 Gemini, False면 OpenAI
        **kwargs: 추가 설정

    Returns:
        챗봇 인스턴스
    """
    if use_gemini:
        return GeminiFlashLiteChatbot(character_name=character_name, **kwargs)
    else:
        return OpenAIChatbot(character_name=character_name, **kwargs)


# 테스트 코드
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🤖 Gemini 2.0 Flash-Lite 챗봇 테스트\n")

    # Gemini 챗봇 생성
    try:
        bot = create_chatbot(
            character_name="뽀로로",
            personality_traits=["호기심 많음", "장난기 많음", "모험을 좋아함"],
            speech_style="밝고 경쾌한 말투"
        )

        # 테스트 대화
        test_messages = [
            "안녕! 너 이름이 뭐야?",
            "오늘 뭐 하고 놀까?",
            "눈이 오면 뭐가 제일 재미있어?"
        ]

        for msg in test_messages:
            print(f"👤 사용자: {msg}")
            response = bot.get_response(msg)
            print(f"🐧 뽀로로: {response}\n")

        # 대화 히스토리 출력
        print("\n📜 대화 히스토리:")
        for item in bot.get_conversation_history():
            role = "사용자" if item["role"] == "user" else "뽀로로"
            print(f"  {role}: {item['content']}")

    except Exception as e:
        print(f"❌ 오류: {e}")
