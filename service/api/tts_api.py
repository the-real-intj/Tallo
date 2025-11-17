"""
Zonos Multi-Character TTS API Server
여러 캐릭터의 Speaker Embedding을 관리하고 TTS를 생성하는 FastAPI 서버
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import torch
import torchaudio
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from zonos.utils import DEFAULT_DEVICE as device

# .env 파일에서 환경 변수 로드
# service 디렉토리의 .env 파일 사용
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# OpenAI LLM 지원
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI 패키지가 설치되지 않았습니다. LLM 기능을 사용하려면 'pip install openai'를 실행하세요.")

# MongoDB 지원
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️ MongoDB 패키지가 설치되지 않았습니다. MongoDB 기능을 사용하려면 'pip install pymongo'를 실행하세요.")

# torch.compile 비활성화 (Windows 컴파일러 없음)
import torch._dynamo
torch._dynamo.config.suppress_errors = True
os.environ["TORCHDYNAMO_DISABLE"] = "1"

# ==================== 설정 ====================
app = FastAPI(
    title="Zonos Multi-Character TTS API",
    version="2.0.0",
    description="다중 캐릭터 음성 생성 및 관리 시스템"
)

# CORS 설정 (React와 통신 + ngrok)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 디렉토리 설정 (이미 위에서 정의됨)
EMBEDDINGS_DIR = BASE_DIR / "embeddings"
REFERENCE_DIR = BASE_DIR / "audios"
OUTPUTS_DIR = BASE_DIR / "outputs"
CACHE_DIR = BASE_DIR / "cache"

for directory in [EMBEDDINGS_DIR, REFERENCE_DIR, OUTPUTS_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True)

# 캐릭터 메타데이터 파일
CHARACTERS_DB = EMBEDDINGS_DIR / "characters.json"

# 전역 변수
model = None
characters_db: Dict = {}
story_audio_cache: Dict[str, Dict[int, str]] = {}  # {character_id: {page_num: audio_path}}
mongodb_client = None
mongodb_db = None

# ==================== 데이터 모델 ====================

class TTSRequest(BaseModel):
    """TTS 생성 요청"""
    text: str
    character_id: str
    language: str = "ko"  # 한국어 기본값
    speaking_rate: float = 1.0
    pitch: float = 1.0
    emotion: Optional[str] = None  # happy, sad, angry, fear

class CharacterInfo(BaseModel):
    """캐릭터 정보"""
    id: str
    name: str
    description: Optional[str] = None
    language: str = "ko"  # 한국어 기본값
    created_at: str
    reference_audio: Optional[str] = None

class CreateCharacterRequest(BaseModel):
    """캐릭터 생성 요청"""
    name: str
    description: Optional[str] = None
    language: str = "ko"  # 한국어 기본값

class StoryPage(BaseModel):
    """동화 페이지 정보"""
    page: int
    text: str
    audio_url: Optional[str] = None  # 페이지별 오디오 파일 URL

class PreGenerateStoryRequest(BaseModel):
    """동화책 전체 TTS 미리 생성 요청"""
    character_id: str
    pages: List[Dict]  # [{page: 1, text: "..."}, ...]

class LLMChatRequest(BaseModel):
    """LLM 채팅 요청"""
    message: str = Field(..., description="사용자 메시지")
    character_id: Optional[str] = Field(None, description="캐릭터 ID (TTS에 사용)")
    character_name: Optional[str] = Field(None, description="캐릭터 이름 (프롬프트에 사용)")
    system_prompt: Optional[str] = Field(None, description="시스템 프롬프트 (선택)")
    return_audio: bool = Field(True, description="TTS 오디오도 함께 반환할지 여부")

class LLMChatResponse(BaseModel):
    """LLM 채팅 응답"""
    text: str
    audio_url: Optional[str] = None  # TTS 생성된 오디오 URL

class StoryPage(BaseModel):
    """동화 페이지 정보"""
    page: int
    text: str
    audio_url: Optional[str] = None  # 페이지별 오디오 파일 URL

class StoryInfo(BaseModel):
    """동화 정보 (MongoDB)"""
    id: str
    title: str
    text: str
    pages: Optional[List[StoryPage]] = None  # 페이지별로 나눈 텍스트와 오디오
    audio_url: Optional[str] = None  # 전체 오디오 파일 URL (하위 호환)
    character_id: Optional[str] = None
    created_at: Optional[str] = None

class StoryListResponse(BaseModel):
    """동화 목록 응답"""
    stories: List[StoryInfo]
    total: int

# ==================== 유틸리티 함수 ====================

def load_characters_db():
    """캐릭터 데이터베이스 로드"""
    global characters_db
    if CHARACTERS_DB.exists():
        with open(CHARACTERS_DB, 'r', encoding='utf-8') as f:
            characters_db = json.load(f)
    else:
        characters_db = {}
    return characters_db

def save_characters_db():
    """캐릭터 데이터베이스 저장"""
    with open(CHARACTERS_DB, 'w', encoding='utf-8') as f:
        json.dump(characters_db, f, indent=2, ensure_ascii=False)

def get_embedding_path(character_id: str) -> Path:
    """캐릭터 임베딩 파일 경로"""
    return EMBEDDINGS_DIR / f"{character_id}.pt"

def load_character_embedding(character_id: str) -> torch.Tensor:
    """캐릭터 임베딩 로드"""
    embedding_path = get_embedding_path(character_id)
    if not embedding_path.exists():
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")
    
    try:
        embedding = torch.load(embedding_path, map_location=device)
        return embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load embedding: {str(e)}")

def generate_character_id(name: str) -> str:
    """캐릭터 ID 생성 (고유 ID)"""
    import hashlib
    timestamp = datetime.now().isoformat()
    unique_string = f"{name}_{timestamp}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:12]

def split_story_into_pages(text: str, max_chars_per_page: int = 200) -> List[StoryPage]:
    """
    동화 텍스트를 페이지로 나누기
    
    Args:
        text: 전체 동화 텍스트
        max_chars_per_page: 페이지당 최대 문자 수 (기본값: 200)
        
    Returns:
        List[StoryPage]: 페이지별로 나눈 텍스트 리스트
    """
    if not text:
        return []
    
    # 문장 단위로 나누기 (마침표, 물음표, 느낌표 기준)
    import re
    sentences = re.split(r'([.!?。！？]\s*)', text)
    
    # 문장들을 합치면서 페이지 구성
    pages = []
    current_page_text = ""
    current_page_num = 1
    
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]  # 구분자 포함
            i += 2
        else:
            i += 1
        
        # 현재 페이지에 문장 추가 시 길이 체크
        if len(current_page_text) + len(sentence) > max_chars_per_page and current_page_text:
            # 현재 페이지 저장
            pages.append(StoryPage(
                page=current_page_num,
                text=current_page_text.strip(),
                audio_url=None  # 나중에 오디오 생성 시 업데이트
            ))
            current_page_text = sentence
            current_page_num += 1
        else:
            current_page_text += sentence
    
    # 마지막 페이지 추가
    if current_page_text.strip():
        pages.append(StoryPage(
            page=current_page_num,
            text=current_page_text.strip(),
            audio_url=None
        ))
    
    return pages

# ==================== 시작/종료 이벤트 ====================

@app.on_event("startup")
async def startup_event():
    """서버 시작시 모델 로드"""
    global model, mongodb_client, mongodb_db
    print("=" * 60)
    print("🚀 Zonos Multi-Character TTS API Server Starting...")
    print("=" * 60)
    
    print("\n📦 Loading Zonos model...")
    try:
        # Transformer 모델 (더 빠름)
        model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-transformer", device=device)
        # Hybrid 모델 (더 고품질)
        # model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-hybrid", device=device)
        print(f"✅ Model loaded successfully on {device}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        raise
    
    print("\n📚 Loading characters database...")
    load_characters_db()
    print(f"✅ Loaded {len(characters_db)} characters")
    
    # MongoDB 연결
    if MONGODB_AVAILABLE:
        print("\n🗄️ Connecting to MongoDB...")
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            mongodb_db_name = os.getenv("MONGODB_DB_NAME", "tallo")
            
            mongodb_client = MongoClient(mongodb_uri)
            # 연결 테스트
            mongodb_client.admin.command('ping')
            mongodb_db = mongodb_client[mongodb_db_name]
            print(f"✅ MongoDB connected: {mongodb_uri}")
            print(f"✅ Database: {mongodb_db_name}")
        except ConnectionFailure as e:
            print(f"⚠️ MongoDB connection failed: {e}")
            print("⚠️ MongoDB features will be disabled")
            mongodb_client = None
            mongodb_db = None
        except Exception as e:
            print(f"⚠️ MongoDB error: {e}")
            mongodb_client = None
            mongodb_db = None
    else:
        print("\n⚠️ MongoDB not available (pymongo not installed)")
    
    print("\n" + "=" * 60)
    print("✨ Server is ready!")
    print("📖 API Documentation: {IP주소:port}/docs")
    print("=" * 60 + "\n")

# ==================== API 엔드포인트 ====================

@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "model": "Zonos-v0.1-transformer",
        "device": str(device),
        "total_characters": len(characters_db)
    }

@app.get("/characters", response_model=List[CharacterInfo])
async def list_characters():
    """
    등록된 모든 캐릭터 목록 조회
    
    Returns:
        List[CharacterInfo]: 캐릭터 정보 리스트
    """
    load_characters_db()
    return [CharacterInfo(**char) for char in characters_db.values()]

@app.get("/characters/{character_id}", response_model=CharacterInfo)
async def get_character(character_id: str):
    """
    특정 캐릭터 정보 조회
    
    Args:
        character_id: 캐릭터 ID
        
    Returns:
        CharacterInfo: 캐릭터 상세 정보
    """
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    return CharacterInfo(**characters_db[character_id])

@app.post("/characters/create")
async def create_character(
    name: str = Form(...),
    description: str = Form(None),
    language: str = Form("ko"),  # 한국어 기본값
    reference_audio: UploadFile = File(...)
):
    """
    새로운 캐릭터 생성 (Speaker Embedding 추출 및 저장)
    
    Args:
        name: 캐릭터 이름
        description: 캐릭터 설명
        language: 언어 코드
        reference_audio: 참조 오디오 파일 (10-30초 권장)
        
    Returns:
        CharacterInfo: 생성된 캐릭터 정보
    """
    # 1. 고유 ID 생성
    character_id = generate_character_id(name)
    
    # 2. 임시 파일로 오디오 저장
    temp_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await reference_audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        # 3. 오디오 로드
        print(f"📝 Creating character '{name}' (ID: {character_id})")
        wav, sampling_rate = torchaudio.load(temp_audio_path)
        
        # 4. Speaker Embedding 생성
        print("🎤 Extracting speaker embedding...")
        speaker_embedding = model.make_speaker_embedding(wav, sampling_rate)
        
        # 5. Embedding 저장
        embedding_path = get_embedding_path(character_id)
        torch.save(speaker_embedding, embedding_path)
        print(f"💾 Saved embedding: {embedding_path}")
        
        # 6. 참조 오디오 저장 (선택적)
        ref_audio_path = REFERENCE_DIR / f"{character_id}.wav"
        torchaudio.save(str(ref_audio_path), wav, sampling_rate, backend="soundfile")
        
        # 7. 캐릭터 정보 저장
        character_info = {
            "id": character_id,
            "name": name,
            "description": description,
            "language": language,
            "created_at": datetime.now().isoformat(),
            "reference_audio": str(ref_audio_path.relative_to(BASE_DIR))
        }
        
        characters_db[character_id] = character_info
        save_characters_db()
        
        print(f"✅ Character '{name}' created successfully!")
        return CharacterInfo(**character_info)
        
    except Exception as e:
        print(f"❌ Error creating character: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 임시 파일 정리
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)

@app.delete("/characters/{character_id}")
async def delete_character(character_id: str):
    """
    캐릭터 삭제
    
    Args:
        character_id: 삭제할 캐릭터 ID
    """
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # 임베딩 파일 삭제
    embedding_path = get_embedding_path(character_id)
    if embedding_path.exists():
        embedding_path.unlink()
    
    # 참조 오디오 삭제 (선택적)
    ref_audio_path = REFERENCE_DIR / f"{character_id}.wav"
    if ref_audio_path.exists():
        ref_audio_path.unlink()
    
    # DB에서 삭제
    del characters_db[character_id]
    save_characters_db()
    
    return {"message": f"Character '{character_id}' deleted successfully"}

@app.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    """
    특정 캐릭터의 목소리로 TTS 생성
    
    Args:
        request: TTS 생성 요청 (text, character_id, language, etc.)
        
    Returns:
        FileResponse: 생성된 오디오 파일
    """
    try:
        # 1. 캐릭터 확인
        if request.character_id not in characters_db:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # 2. Speaker Embedding 로드
        speaker_embedding = load_character_embedding(request.character_id)
        
        # 3. Conditioning 준비
        # speaking_rate: 10=느림, 15=보통, 30=빠름 (phonemes per minute)
        # pitch_std: 20-45=자연스러움, 60-150=표현력 있음
        speaking_rate = request.speaking_rate if request.speaking_rate > 1.0 else 15.0
        cond_dict = make_cond_dict(
            text=request.text,
            speaker=speaker_embedding,
            language=request.language,
            speaking_rate=speaking_rate,
            pitch_std=30.0  # 자연스러운 억양
        )
        
        # 감정 추가 (선택적)
        if request.emotion:
            # Zonos는 감정 제어를 위한 파라미터를 지원합니다
            # 예: happiness, sadness, anger, fear
            if request.emotion in ["happy", "happiness"]:
                cond_dict["happiness"] = 0.7
            elif request.emotion in ["sad", "sadness"]:
                cond_dict["sadness"] = 0.7
            elif request.emotion in ["angry", "anger"]:
                cond_dict["anger"] = 0.7
            elif request.emotion == "fear":
                cond_dict["fear"] = 0.7
        
        conditioning = model.prepare_conditioning(cond_dict)
        
        # 4. TTS 생성
        print(f"🎤 Generating TTS for character '{request.character_id}'...")
        with torch.no_grad():
            # 텍스트 길이에 따라 동적으로 조정
            # 한글은 토큰을 더 많이 사용하므로 여유있게 설정
            text_length = len(request.text)
            if text_length < 10:
                max_tokens = 300  # 매우 짧은 문장 (3-4초)
            elif text_length < 20:
                max_tokens = 500  # 짧은 문장 (5-6초)
            elif text_length < 50:
                max_tokens = 800  # 중간 문장 (8-10초)
            elif text_length < 100:
                max_tokens = 1200  # 긴 문장 (12-15초)
            else:
                max_tokens = 86 * 30  # 매우 긴 문장 (기본값)
            
            # 샘플링 파라미터 조정 (더 안정적인 생성)
            codes = model.generate(
                conditioning, 
                max_new_tokens=max_tokens,
                sampling_params={"min_p": 0.1, "temperature": 1.0}
            )
            wavs = model.autoencoder.decode(codes).cpu()
        
        # 5. 파일 저장
        character_name = characters_db[request.character_id]["name"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{character_name}_{timestamp}.wav"
        output_path = OUTPUTS_DIR / filename

        # TorchCodec 오류 방지: backend='soundfile' 사용
        torchaudio.save(
            str(output_path),
            wavs[0],
            model.autoencoder.sampling_rate,
            backend="soundfile"
        )
        
        print(f"✅ TTS generated: {output_path}")
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/batch")
async def batch_generate_tts(
    texts: List[str] = Form(...),
    character_id: str = Form(...),
    language: str = Form("ko")  # 한국어 기본값
):
    """
    여러 텍스트를 한 번에 생성 (배치 처리)
    
    Args:
        texts: 텍스트 리스트
        character_id: 캐릭터 ID
        language: 언어 코드
        
    Returns:
        JSON: 생성된 파일 경로 리스트
    """
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    speaker_embedding = load_character_embedding(character_id)
    generated_files = []
    
    for idx, text in enumerate(texts):
        try:
            cond_dict = make_cond_dict(
                text=text,
                speaker=speaker_embedding,
                language=language
            )
            conditioning = model.prepare_conditioning(cond_dict)
            
            with torch.no_grad():
                # 배치 처리도 길이 제한 적용
                text_length = len(text)
                max_tokens = min(400 if text_length < 50 else 600, 86 * 30)
                codes = model.generate(conditioning, max_new_tokens=max_tokens)
                wavs = model.autoencoder.decode(codes).cpu()
            
            filename = f"{character_id}_batch_{idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            output_path = OUTPUTS_DIR / filename
            torchaudio.save(str(output_path), wavs[0], model.autoencoder.sampling_rate, backend="soundfile")
            
            generated_files.append({
                "index": idx,
                "text": text,
                "file": str(output_path.relative_to(BASE_DIR))
            })
            
        except Exception as e:
            print(f"Error generating batch item {idx}: {e}")
            generated_files.append({
                "index": idx,
                "text": text,
                "error": str(e)
            })
    
    return {"results": generated_files}

@app.get("/outputs/{filename}")
async def get_output_file(filename: str):
    """
    생성된 오디오 파일 다운로드
    
    Args:
        filename: 파일 이름
    """
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/health")
async def health_check():
    """서버 헬스 체크"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": str(device),
        "characters_count": len(characters_db)
    }

@app.post("/stories/pregenerate")
async def pregenerate_story_audio(request: PreGenerateStoryRequest):
    """
    동화책 전체 페이지의 TTS를 미리 생성하여 캐싱
    
    Args:
        request: character_id와 pages 리스트
        
    Returns:
        생성된 오디오 파일 경로 맵핑
    """
    character_id = request.character_id
    
    # 캐릭터 확인
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Speaker Embedding 로드
    speaker_embedding = load_character_embedding(character_id)
    
    # 캐릭터별 캐시 디렉토리 생성
    cache_dir = CACHE_DIR / character_id
    cache_dir.mkdir(exist_ok=True)
    
    generated_pages = []
    
    print(f"📚 Pre-generating story audio for character '{character_id}'...")
    
    for page_data in request.pages:
        page_num = page_data["page"]
        text = page_data["text"]
        
        try:
            # 이미 캐시된 파일이 있는지 확인
            cached_file = cache_dir / f"page_{page_num}.wav"
            
            if cached_file.exists():
                print(f"✅ Page {page_num} already cached")
                audio_url = f"/cache/{character_id}/page_{page_num}.wav"
            else:
                # TTS 생성
                print(f"🎤 Generating page {page_num}...")
                cond_dict = make_cond_dict(
                    text=text,
                    speaker=speaker_embedding,
                    language="ko"
                )
                conditioning = model.prepare_conditioning(cond_dict)
                
                with torch.no_grad():
                    codes = model.generate(conditioning)
                    wavs = model.autoencoder.decode(codes).cpu()
                
                # 파일 저장
                torchaudio.save(
                    str(cached_file),
                    wavs[0],
                    model.autoencoder.sampling_rate,
                    backend="soundfile"
                )
                
                audio_url = f"/cache/{character_id}/page_{page_num}.wav"
                print(f"✅ Page {page_num} generated and cached")
            
            generated_pages.append({
                "page": page_num,
                "text": text,
                "audio_url": audio_url
            })
            
        except Exception as e:
            print(f"❌ Error generating page {page_num}: {e}")
            generated_pages.append({
                "page": page_num,
                "text": text,
                "error": str(e)
            })
    
    # 캐시 정보 저장
    if character_id not in story_audio_cache:
        story_audio_cache[character_id] = {}
    
    for page_data in generated_pages:
        if "audio_url" in page_data:
            story_audio_cache[character_id][page_data["page"]] = page_data["audio_url"]
    
    return {
        "character_id": character_id,
        "total_pages": len(generated_pages),
        "pages": generated_pages
    }

@app.get("/cache/{character_id}/{filename}")
async def get_cached_audio(character_id: str, filename: str):
    """
    캐시된 오디오 파일 제공
    
    Args:
        character_id: 캐릭터 ID
        filename: 파일명
    """
    file_path = CACHE_DIR / character_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Cached audio not found")
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/stories/audio/{character_id}")
async def get_story_audio_map(character_id: str):
    """
    특정 캐릭터의 동화책 오디오 맵핑 조회
    
    Returns:
        {page_num: audio_url} 딕셔너리
    """
    if character_id not in story_audio_cache:
        return {"character_id": character_id, "pages": {}}
    
    return {
        "character_id": character_id,
        "pages": story_audio_cache[character_id]
    }

# ==================== LLM API 엔드포인트 ====================

@app.post("/llm/chat", response_model=LLMChatResponse)
async def chat_with_llm(request: LLMChatRequest):
    """
    OpenAI LLM과 대화하고, 선택적으로 TTS로 변환
    
    Args:
        request: LLM 채팅 요청 (message, character_id, return_audio 등)
        
    Returns:
        LLMChatResponse: LLM 응답 텍스트 및 TTS 오디오 URL (선택)
    """
    if not OPENAI_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="OpenAI 패키지가 설치되지 않았습니다. 'pip install openai'를 실행하세요."
        )
    
    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경 변수를 설정하세요."
        )
    
    try:
        # 1. 시스템 프롬프트 설정
        system_prompt = request.system_prompt or "당신은 친절한 동화 작가입니다."
        if request.character_name:
            system_prompt += f" {request.character_name} 캐릭터의 성격으로 대답해주세요."
        
        # 2. OpenAI LLM API 호출 (최신 API 방식)
        # openai >= 1.0.0 버전 대응
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            llm_text = response.choices[0].message.content
        except ImportError:
            # 구버전 openai (< 1.0.0) 대응
            openai.api_key = api_key
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            llm_text = response.choices[0].message.content
        
        audio_url = None
        
        # 4. TTS 생성 (요청된 경우)
        if request.return_audio and request.character_id:
            if request.character_id not in characters_db:
                raise HTTPException(status_code=404, detail="Character not found")
            
            # Speaker Embedding 로드
            speaker_embedding = load_character_embedding(request.character_id)
            
            # TTS 생성
            # speaking_rate: 10=느림, 15=보통, 30=빠름
            # pitch_std: 20-45=자연스러움
            cond_dict = make_cond_dict(
                text=llm_text,
                speaker=speaker_embedding,
                language="ko",
                speaking_rate=15.0,
                pitch_std=30.0
            )
            conditioning = model.prepare_conditioning(cond_dict)
            
            with torch.no_grad():
                # LLM 응답 길이에 따라 토큰 수 제한
                text_length = len(llm_text)
                if text_length < 20:
                    max_tokens = 500
                elif text_length < 50:
                    max_tokens = 800
                elif text_length < 100:
                    max_tokens = 1200
                else:
                    max_tokens = 86 * 30
                
                codes = model.generate(
                    conditioning, 
                    max_new_tokens=max_tokens,
                    sampling_params={"min_p": 0.1, "temperature": 1.0}
                )
                wavs = model.autoencoder.decode(codes).cpu()
            
            # 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_{request.character_id}_{timestamp}.wav"
            output_path = OUTPUTS_DIR / filename
            
            torchaudio.save(
                str(output_path),
                wavs[0],
                model.autoencoder.sampling_rate,
                backend="soundfile"
            )
            
            audio_url = f"/outputs/{filename}"
            print(f"✅ LLM + TTS generated: {output_path}")
        
        return LLMChatResponse(text=llm_text, audio_url=audio_url)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in LLM chat: {e}")
        raise HTTPException(status_code=500, detail=f"LLM 처리 중 오류: {str(e)}")

# ==================== MongoDB 동화 API 엔드포인트 ====================

@app.get("/stories/debug")
async def debug_mongodb():
    """MongoDB 연결 상태 및 컬렉션 정보 디버깅"""
    debug_info = {
        "mongodb_available": MONGODB_AVAILABLE,
        "mongodb_connected": mongodb_db is not None,
        "database_name": os.getenv("MONGODB_DB_NAME", "not set"),
        "collections": [],
        "stories_count": 0,
        "error": None
    }
    
    if not MONGODB_AVAILABLE:
        debug_info["error"] = "pymongo not installed"
        return debug_info
    
    if mongodb_db is None:
        debug_info["error"] = "MongoDB not connected"
        return debug_info
    
    try:
        # 컬렉션 목록 가져오기
        debug_info["collections"] = mongodb_db.list_collection_names()
        
        # "texts" 컬렉션 확인
        if "texts" in debug_info["collections"]:
            stories_collection = mongodb_db["texts"]
            debug_info["stories_count"] = stories_collection.count_documents({})
            
            # 샘플 문서 하나 가져오기
            sample = stories_collection.find_one()
            if sample:
                debug_info["sample_doc"] = {
                    "_id": str(sample.get("_id", "")),
                    "filename": sample.get("filename", ""),
                    "has_content": bool(sample.get("content", "")),
                    "content_length": len(sample.get("content", "")) if sample.get("content") else 0
                }
    except Exception as e:
        debug_info["error"] = str(e)
    
    return debug_info

@app.get("/stories/list", response_model=StoryListResponse)
async def list_stories(limit: int = 5):
    """
    MongoDB에서 동화 목록 조회 (최대 5개)
    
    Args:
        limit: 가져올 동화 개수 (기본값: 5)
        
    Returns:
        StoryListResponse: 동화 목록
    """
    if not MONGODB_AVAILABLE or mongodb_db is None:
        raise HTTPException(
            status_code=500,
            detail="MongoDB가 연결되지 않았습니다. MONGODB_URI 환경 변수를 설정하세요."
        )
    
    try:
        # MongoDB 컬렉션 이름: "texts" (실제 컬렉션 이름)
        stories_collection = mongodb_db["texts"]
        
        # 최대 5개로 제한
        limit = min(limit, 5)
        
        # MongoDB에서 동화 목록 가져오기
        # created_at이 없을 수 있으므로 _id로 정렬 (최신순)
        stories_cursor = stories_collection.find().limit(limit).sort("_id", -1)
        stories_list = []
        
        for story_doc in stories_cursor:
            # MongoDB 필드명: filename, content
            filename = story_doc.get("filename", "")
            # .txt 확장자 제거하여 제목으로 사용
            title = filename.replace(".txt", "") if filename else "제목 없음"
            content = story_doc.get("content", "")
            
            # 페이지로 나누기 (문장 단위)
            pages = split_story_into_pages(content)
            
            story_info = StoryInfo(
                id=str(story_doc.get("_id", "")),
                title=title,
                text=content,  # 전체 텍스트 (하위 호환)
                pages=pages,  # 페이지별로 나눈 텍스트
                audio_url=story_doc.get("audio_url"),
                character_id=story_doc.get("character_id"),
                created_at=story_doc.get("uploadedAt") or story_doc.get("created_at")
            )
            stories_list.append(story_info)
        
        total = stories_collection.count_documents({})
        
        return StoryListResponse(
            stories=stories_list,
            total=total
        )
        
    except Exception as e:
        print(f"❌ Error fetching stories: {e}")
        raise HTTPException(status_code=500, detail=f"동화 목록 조회 중 오류: {str(e)}")

@app.get("/stories/{story_id}", response_model=StoryInfo)
async def get_story(story_id: str):
    """
    특정 동화 조회
    
    Args:
        story_id: 동화 ID
        
    Returns:
        StoryInfo: 동화 정보
    """
    if not MONGODB_AVAILABLE or mongodb_db is None:
        raise HTTPException(
            status_code=500,
            detail="MongoDB가 연결되지 않았습니다."
        )
    
    try:
        from bson import ObjectId
        stories_collection = mongodb_db["texts"]
        
        story_doc = stories_collection.find_one({"_id": ObjectId(story_id)})
        
        if not story_doc:
            raise HTTPException(status_code=404, detail="Story not found")
        
        filename = story_doc.get("filename", "")
        title = filename.replace(".txt", "") if filename else "제목 없음"
        content = story_doc.get("content", "")
        pages = split_story_into_pages(content)
        
        return StoryInfo(
            id=str(story_doc.get("_id", "")),
            title=title,
            text=content,
            pages=pages,
            audio_url=story_doc.get("audio_url"),
            character_id=story_doc.get("character_id"),
            created_at=story_doc.get("uploadedAt") or story_doc.get("created_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching story: {e}")
        raise HTTPException(status_code=500, detail=f"동화 조회 중 오류: {str(e)}")

@app.get("/stories/{story_id}/audio")
async def get_story_audio(story_id: str):
    """
    동화의 미리 생성된 오디오 파일 재생
    
    Args:
        story_id: 동화 ID
        
    Returns:
        FileResponse: 오디오 파일
    """
    if not MONGODB_AVAILABLE or mongodb_db is None:
        raise HTTPException(
            status_code=500,
            detail="MongoDB가 연결되지 않았습니다."
        )
    
    try:
        from bson import ObjectId
        stories_collection = mongodb_db["stories"]
        
        story_doc = stories_collection.find_one({"_id": ObjectId(story_id)})
        
        if not story_doc:
            raise HTTPException(status_code=404, detail="Story not found")
        
        audio_url = story_doc.get("audio_url")
        if not audio_url:
            raise HTTPException(status_code=404, detail="Audio file not found for this story")
        
        # audio_url이 상대 경로면 절대 경로로 변환
        if audio_url.startswith("/"):
            audio_path = BASE_DIR / audio_url.lstrip("/")
        else:
            audio_path = Path(audio_url)
        
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename=f"story_{story_id}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching story audio: {e}")
        raise HTTPException(status_code=500, detail=f"오디오 파일 조회 중 오류: {str(e)}")

@app.post("/stories/{story_id}/chat", response_model=LLMChatResponse)
async def story_chat(story_id: str, request: LLMChatRequest):
    """
    동화 재생 중 채팅 (오디오 재생 중지 후 LLM + TTS 생성)
    
    Args:
        story_id: 동화 ID
        request: LLM 채팅 요청
        
    Returns:
        LLMChatResponse: LLM 응답 및 TTS 오디오 URL
    """
    # 기존 LLM 채팅 로직 사용
    # 클라이언트에서 오디오 재생 중지는 처리해야 함
    return await chat_with_llm(request)

@app.post("/stories/{story_id}/pregenerate-audio")
async def pregenerate_story_pages_audio(story_id: str, character_id: str):
    """
    동화의 모든 페이지에 대한 오디오를 미리 생성
    
    Args:
        story_id: 동화 ID
        character_id: 캐릭터 ID
        
    Returns:
        생성된 페이지별 오디오 정보
    """
    if not MONGODB_AVAILABLE or mongodb_db is None:
        raise HTTPException(
            status_code=500,
            detail="MongoDB가 연결되지 않았습니다."
        )
    
    try:
        from bson import ObjectId
        stories_collection = mongodb_db["texts"]
        
        story_doc = stories_collection.find_one({"_id": ObjectId(story_id)})
        if not story_doc:
            raise HTTPException(status_code=404, detail="Story not found")
        
        # 캐릭터 확인
        if character_id not in characters_db:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Speaker Embedding 로드
        speaker_embedding = load_character_embedding(character_id)
        
        # 동화 텍스트를 페이지로 나누기
        content = story_doc.get("content", "")
        pages = split_story_into_pages(content)
        
        # 스토리별 오디오 디렉토리 생성
        story_audio_dir = OUTPUTS_DIR / "stories" / story_id
        story_audio_dir.mkdir(parents=True, exist_ok=True)
        
        generated_pages = []
        
        print(f"🎤 Pre-generating audio for story '{story_id}' ({len(pages)} pages)...")
        
        for page in pages:
            try:
                # 페이지별 오디오 파일 경로
                audio_filename = f"page_{page.page}.wav"
                audio_path = story_audio_dir / audio_filename
                
                # 이미 생성된 파일이 있으면 스킵
                if audio_path.exists():
                    print(f"✅ Page {page.page} already exists, skipping...")
                    audio_url = f"/outputs/stories/{story_id}/{audio_filename}"
                    generated_pages.append({
                        "page": page.page,
                        "text": page.text,
                        "audio_url": audio_url
                    })
                    continue
                
                # TTS 생성
                print(f"🎤 Generating audio for page {page.page}...")
                cond_dict = make_cond_dict(
                    text=page.text,
                    speaker=speaker_embedding,
                    language="ko",
                    speaking_rate=15.0,
                    pitch_std=30.0
                )
                conditioning = model.prepare_conditioning(cond_dict)
                
                with torch.no_grad():
                    text_length = len(page.text)
                    if text_length < 20:
                        max_tokens = 500
                    elif text_length < 50:
                        max_tokens = 800
                    elif text_length < 100:
                        max_tokens = 1200
                    else:
                        max_tokens = 86 * 30
                    
                    codes = model.generate(
                        conditioning,
                        max_new_tokens=max_tokens,
                        sampling_params={"min_p": 0.1, "temperature": 1.0}
                    )
                    wavs = model.autoencoder.decode(codes).cpu()
                
                # 파일 저장
                torchaudio.save(
                    str(audio_path),
                    wavs[0],
                    model.autoencoder.sampling_rate,
                    backend="soundfile"
                )
                
                audio_url = f"/outputs/stories/{story_id}/{audio_filename}"
                generated_pages.append({
                    "page": page.page,
                    "text": page.text,
                    "audio_url": audio_url
                })
                
                print(f"✅ Page {page.page} audio generated: {audio_path}")
                
            except Exception as e:
                print(f"❌ Error generating page {page.page}: {e}")
                generated_pages.append({
                    "page": page.page,
                    "text": page.text,
                    "error": str(e)
                })
        
        # MongoDB에 페이지별 오디오 URL 업데이트 (선택적)
        # stories_collection.update_one(
        #     {"_id": ObjectId(story_id)},
        #     {"$set": {"pages_audio": generated_pages}}
        # )
        
        return {
            "story_id": story_id,
            "character_id": character_id,
            "total_pages": len(pages),
            "generated_pages": generated_pages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error pregenerating story audio: {e}")
        raise HTTPException(status_code=500, detail=f"오디오 생성 중 오류: {str(e)}")

@app.get("/outputs/stories/{story_id}/{filename}")
async def get_story_page_audio(story_id: str, filename: str):
    """
    동화 페이지별 오디오 파일 제공
    
    Args:
        story_id: 동화 ID
        filename: 파일명 (예: page_1.wav)
    """
    file_path = OUTPUTS_DIR / "stories" / story_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")

# ==================== 메인 실행 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host= "0.0.0.0",
        port=8000,
        log_level="info"
    )