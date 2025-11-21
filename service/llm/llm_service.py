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
    
    # 캐릭터별 Assistant ID 매핑
    # character_id 또는 character_name으로 매칭 가능하도록 설정
    ASSISTANT_IDS = {
        # 베레사 (character_id: "8d8bb9642466", name: "베레사")
        "8d8bb9642466": "asst_CAjG1eO7DJL1UtmIg4umBppM",
        "varesa": "asst_CAjG1eO7DJL1UtmIg4umBppM",
        "베레사": "asst_CAjG1eO7DJL1UtmIg4umBppM",
        "바레사": "asst_CAjG1eO7DJL1UtmIg4umBppM",
        
        # 아나 (character_id: "5fbdc9b344b2", name: "아나")
        "5fbdc9b344b2": "asst_GjopixRlOpNEr8qx4jvrRBTB",
        "ana": "asst_GjopixRlOpNEr8qx4jvrRBTB",
        "아나": "asst_GjopixRlOpNEr8qx4jvrRBTB",
        
        # 하츄핑 (character_id: "4c84ef36f400", name: "하츄핑")
        "4c84ef36f400": "asst_t8cx3SsPBjHwIn5ZSlo5GqWq",
        "sijinping": "asst_t8cx3SsPBjHwIn5ZSlo5GqWq",
        "하츄핑": "asst_t8cx3SsPBjHwIn5ZSlo5GqWq",
    }
    
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
    
    def _get_assistant_id(self, character_id: Optional[str] = None, character_name: Optional[str] = None) -> Optional[str]:
        """캐릭터 이름 또는 ID로 Assistant ID 가져오기"""
        if character_name:
            # character_name을 소문자로 변환하여 매핑
            name_lower = character_name.lower()
            for key, assistant_id in self.ASSISTANT_IDS.items():
                if key in name_lower or name_lower in key:
                    return assistant_id
        
        if character_id:
            # character_id에서도 확인 (예: "varesa_voice" 같은 형식)
            id_lower = character_id.lower()
            for key, assistant_id in self.ASSISTANT_IDS.items():
                if key in id_lower:
                    return assistant_id
        
        return None
    
    async def chat(
        self,
        message: str,
        character_id: Optional[str] = None,
        character_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        return_audio: bool = True,
        tts_callback=None,  # TTS 생성 콜백 함수 (tts_api에서 전달)
        current_page_text: Optional[str] = None  # 현재 동화책 페이지 내용
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
        
        client = self._get_openai_client()
        
        # Assistant ID 확인
        assistant_id = self._get_assistant_id(character_id, character_name)
        
        if assistant_id:
            # Assistant API 사용
            try:
                from openai import AsyncOpenAI
                
                # Thread 생성
                thread = await client.beta.threads.create()
                
                # 현재 페이지 내용이 있으면 메시지에 추가
                full_message = message
                if current_page_text:
                    full_message = f"현재 동화책 페이지 내용:\n{current_page_text}\n\n{message}"
                
                # 메시지 추가
                await client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=full_message
                )
                
                # Run 생성 및 실행
                run = await client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant_id
                )
                
                # Run 완료 대기
                import asyncio
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(0.5)
                    run = await client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                if run.status == "completed":
                    # 메시지 가져오기 (최신순)
                    messages = await client.beta.threads.messages.list(
                        thread_id=thread.id,
                        order="desc"
                    )
                    # 가장 최근 어시스턴트 메시지 찾기
                    llm_text = None
                    for msg in messages.data:
                        if msg.role == "assistant" and msg.content:
                            # content는 리스트이고, 각 항목은 TextContentBlock
                            for content_block in msg.content:
                                # content_block은 TextContentBlock 객체
                                if hasattr(content_block, "text"):
                                    # text 속성이 Text 객체
                                    if hasattr(content_block.text, "value"):
                                        llm_text = content_block.text.value
                                        break
                                elif isinstance(content_block, dict):
                                    # 딕셔너리 형태인 경우
                                    if "text" in content_block and isinstance(content_block["text"], dict):
                                        llm_text = content_block["text"].get("value")
                                        break
                            if llm_text:
                                break
                    
                    if not llm_text:
                        raise RuntimeError("Assistant 응답을 찾을 수 없습니다.")
                else:
                    raise RuntimeError(f"Assistant 실행 실패: {run.status}")
                    
            except Exception as e:
                print(f"⚠️ Assistant API 호출 실패, 일반 Chat API로 폴백: {e}")
                # Assistant API 실패 시 일반 Chat API로 폴백
                assistant_id = None
        
        if not assistant_id:
            # 일반 Chat Completions API 사용 (Assistant ID가 없거나 실패한 경우)
            # 시스템 프롬프트 설정
            if not system_prompt:
                system_prompt = "당신은 친절한 동화 작가입니다."
            if character_name:
                system_prompt += f" {character_name} 캐릭터의 성격으로 대답해주세요."
            
            # 현재 페이지 내용이 있으면 시스템 프롬프트에 추가
            if current_page_text:
                system_prompt += f"\n\n현재 동화책 페이지 내용:\n{current_page_text}"
            
            try:
                from openai import AsyncOpenAI
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=150  # 1-2문장 제한을 위해 토큰 수 감소
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
                    max_tokens=150  # 1-2문장 제한을 위해 토큰 수 감소
                )
                llm_text = response.choices[0].message.content
        
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
        tts_callback=None,
        full_story_text: Optional[str] = None,  # 1페이지부터 해당 페이지까지의 텍스트 (선택)
        page: Optional[str] = None  # 페이지 숫자 (string)
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
        # 페이지 정보 포함
        page_info = f" (페이지 {page})" if page else ""
        
        question_prompt = f"""다음 동화{page_info} 내용을 읽고, 이 페이지의 내용에 맞는 질문을 하나 만들어주세요.
질문은:
- 이 페이지에서 나온 내용을 바탕으로 해야 합니다
- 아이가 이해하기 쉽고 간단해야 합니다
- 동화의 흐름을 이해하는데 도움이 되어야 합니다
- 아이의 창의성을 기르는데 도움이 되어야 합니다.
- 질문만 답변해주세요. 다른 설명은 필요 없습니다.
- 질문은 반드시 1문장으로만 만들어주세요.
"""
        
        # 1페이지부터 해당 페이지까지의 텍스트가 있으면 추가
        context_text = page_text
        if full_story_text:
            context_text = f"지금까지의 동화 내용 (1페이지부터 {page}페이지까지):\n{full_story_text}\n\n현재 페이지 ({page}페이지) 내용:\n{page_text}"
        
        return await self.chat(
            message=question_prompt,
            character_id=character_id,
            character_name=character_name,
            return_audio=True,
            tts_callback=tts_callback,
            current_page_text=context_text
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
멘트는 1-2문장으로 간단하고 따뜻해야 합니다.
멘트만 답변해주세요. 다른 설명은 필요 없습니다.

동화 제목: {story_title}
"""
        
        # 동화 내용을 current_page_text로 전달
        story_content = story_summary[:500] + ('...' if len(story_summary) > 500 else '')
        
        return await self.chat(
            message=closing_prompt,
            character_id=character_id,
            character_name=character_name,
            return_audio=True,
            tts_callback=tts_callback,
            current_page_text=f"동화 내용: {story_content}"
        )

