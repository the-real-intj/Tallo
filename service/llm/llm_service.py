"""
LLM 서비스
OpenAI LLM과의 상호작용 처리
"""
import os
from typing import Optional

# OpenAI LLM 지원
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI 패키지가 설치되지 않았습니다. LLM 기능을 사용하려면 'pip install openai'를 실행하세요.")

class LLMService:
    """LLM 서비스 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    def _get_openai_client(self):
        """OpenAI 클라이언트 생성"""
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI 패키지가 설치되지 않았습니다.")
        
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        try:
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            # 구버전 openai (< 1.0.0) 대응
            openai.api_key = self.api_key
            return openai
    
    async def chat(
        self,
        message: str,
        character_id: Optional[str] = None,
        character_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        return_audio: bool = True,
        tts_callback=None  # TTS 생성 콜백 함수 (tts_api에서 전달)
    ) -> dict:
        """
        LLM과 채팅
        
        Args:
            message: 사용자 메시지
            character_id: 캐릭터 ID (TTS용)
            character_name: 캐릭터 이름
            system_prompt: 시스템 프롬프트
            return_audio: TTS 오디오 생성 여부
            tts_callback: TTS 생성 콜백 함수 (text, character_id) -> audio_url
            
        Returns:
            {"text": str, "audio_url": Optional[str]}
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI 패키지가 설치되지 않았습니다.")
        
        # 시스템 프롬프트 설정
        if not system_prompt:
            system_prompt = "당신은 친절한 동화 작가입니다."
        if character_name:
            system_prompt += f" {character_name} 캐릭터의 성격으로 대답해주세요."
        
        # OpenAI LLM API 호출
        try:
            client = self._get_openai_client()
            
            # 최신 API 방식
            try:
                from openai import AsyncOpenAI
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                llm_text = response.choices[0].message.content
            except (ImportError, AttributeError):
                # 구버전 openai (< 1.0.0) 대응
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                llm_text = response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM API 호출 실패: {str(e)}")
        
        audio_url = None
        
        # TTS 생성 (요청된 경우)
        if return_audio and character_id and tts_callback:
            try:
                audio_url = await tts_callback(llm_text, character_id)
            except Exception as e:
                print(f"⚠️ TTS 생성 실패: {e}")
                # TTS 실패해도 텍스트는 반환
        
        return {"text": llm_text, "audio_url": audio_url}
    
    async def generate_question(
        self,
        page_text: str,
        character_id: str,
        character_name: Optional[str] = None,
        story_title: Optional[str] = None,
        tts_callback=None
    ) -> dict:
        """
        페이지 텍스트를 기반으로 질문 생성
        
        Args:
            page_text: 페이지 텍스트
            character_id: 캐릭터 ID
            character_name: 캐릭터 이름
            story_title: 동화 제목
            tts_callback: TTS 생성 콜백 함수
            
        Returns:
            {"text": str, "audio_url": Optional[str]}
        """
        question_prompt = f"""다음 동화 페이지 내용을 읽고, 이 페이지의 내용에 맞는 질문을 하나 만들어주세요.
질문은:
- 이 페이지에서 나온 내용을 바탕으로 해야 합니다
- 아이가 이해하기 쉽고 간단해야 합니다
- 동화의 흐름을 이해하는데 도움이 되어야 합니다
- 질문만 답변해주세요. 다른 설명은 필요 없습니다.
- 질문은 아주 간단히 1-2문장으로 만들어주세요.

페이지 내용:
"{page_text}"
"""
        
        system_prompt = "당신은 친절한 동화 선생님입니다. 아이들이 동화의 각 페이지를 더 잘 이해할 수 있도록 도와주세요."
        if character_name:
            system_prompt += f" {character_name} 캐릭터의 성격으로 질문해주세요."
        
        return await self.chat(
            message=question_prompt,
            character_id=character_id,
            character_name=character_name,
            system_prompt=system_prompt,
            return_audio=True,
            tts_callback=tts_callback
        )
    
    async def generate_closing_message(
        self,
        story_title: str,
        story_summary: str,
        character_id: str,
        character_name: Optional[str] = None,
        tts_callback=None
    ) -> dict:
        """
        동화 마무리 멘트 생성
        
        Args:
            story_title: 동화 제목
            story_summary: 동화 요약 또는 전체 텍스트
            character_id: 캐릭터 ID
            character_name: 캐릭터 이름
            tts_callback: TTS 생성 콜백 함수
            
        Returns:
            {"text": str, "audio_url": Optional[str]}
        """
        closing_prompt = f"""다음 동화를 읽고, 아이에게 동화를 마무리하는 따뜻한 멘트를 해주세요.
멘트는 2-3문장 정도로 간단하고 따뜻해야 합니다.
멘트만 답변해주세요. 다른 설명은 필요 없습니다.

동화 제목: {story_title}
동화 내용: {story_summary[:500]}{'...' if len(story_summary) > 500 else ''}
"""
        
        system_prompt = "당신은 친절한 동화 선생님입니다. 아이들에게 따뜻하고 격려하는 말을 해주세요."
        if character_name:
            system_prompt += f" {character_name} 캐릭터의 성격으로 말해주세요."
        
        return await self.chat(
            message=closing_prompt,
            character_id=character_id,
            character_name=character_name,
            system_prompt=system_prompt,
            return_audio=True,
            tts_callback=tts_callback
        )

