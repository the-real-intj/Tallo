"""
Zonos Multi-Character TTS API Server
여러 캐릭터의 Speaker Embedding을 관리하고 TTS를 생성하는 FastAPI 서버
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, TYPE_CHECKING
import torch
import torchaudio
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import soundfile as sf  # torchaudio 버그 우회용

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
MONGODB_AVAILABLE = False

if TYPE_CHECKING:
    from .db.repo import CharacterRepository, StorybookRepository, AudioCacheRepository
    from .db.model import StorybookDB

try:
    from .db.db_client import connect_to_mongo, close_mongo_connection, get_database
    from .db.repo import CharacterRepository, StorybookRepository, AudioCacheRepository
    from .db.model import StorybookDB
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MongoDB 모듈을 불러올 수 없습니다: {e}")
    print("⚠️ MongoDB 기능을 사용하려면 'pip install motor pymongo'를 실행하세요.")

# torch.compile 비활성화 (Windows 컴파일러 없음)
import torch._dynamo
torch._dynamo.config.suppress_errors = True
os.environ["TORCHDYNAMO_DISABLE"] = "1"

# espeak 경로 설정 (Windows)
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ["PATH"]
os.environ["PHONEMIZER_ESPEAK_PATH"] = r"C:\Program Files\eSpeak NG\espeak-ng.exe"
os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"

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
characters_db: Dict = {}  # 로컬 캐릭터 DB (하위 호환)
story_audio_cache: Dict[str, Dict[int, str]] = {}  # {character_id: {page_num: audio_path}}

# Repository 인스턴스 (startup에서 초기화)
character_repo: Optional["CharacterRepository"] = None
storybook_repo: Optional["StorybookRepository"] = None
audio_cache_repo: Optional["AudioCacheRepository"] = None

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

class PreGenerateStoryRequest(BaseModel):
    """동화책 전체 TTS 미리 생성 요청"""
    character_id: str
    pages: List[Dict]  # [{page: 1, text: "..."}, ...]

class StoryPage(BaseModel):
    """동화 페이지 정보"""
    page: int
    text: str
    audio_url: Optional[str] = None  # 페이지별 오디오 파일 URL

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

def format_datetime_to_string(dt) -> Optional[str]:
    """
    datetime 객체를 ISO 형식 문자열로 변환
    
    Args:
        dt: datetime 객체 또는 None
        
    Returns:
        ISO 형식 문자열 또는 None
    """
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, str):
        return dt
    # 다른 타입이면 문자열로 변환 시도
    return str(dt)

def split_story_into_pages(text: str, sentences_per_page: int = 2) -> List[StoryPage]:
    """
    동화 텍스트를 페이지로 나누기 (1-2문장씩)
    Repository의 chunk_text와 다르게 문장 단위로 분할 (하위 호환 유지)
    
    Args:
        text: 전체 동화 텍스트
        sentences_per_page: 페이지당 문장 수 (기본값: 2)
        
    Returns:
        List[StoryPage]: 페이지별로 나눈 텍스트 리스트
    """
    if not text:
        return []
    
    # 문장 단위로 나누기 (마침표, 물음표, 느낌표 기준)
    import re
    # 문장 끝 구분자(마침표, 물음표, 느낌표)를 포함하여 분리
    sentences = re.split(r'([.!?。！？]\s*)', text)
    
    # 문장과 구분자를 합쳐서 완전한 문장 만들기
    complete_sentences = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences):
            # 문장 + 구분자 합치기
            complete_sentence = (sentences[i] + sentences[i + 1]).strip()
            if complete_sentence:  # 빈 문장 제외
                complete_sentences.append(complete_sentence)
            i += 2
        else:
            # 마지막 문장 (구분자 없을 수 있음)
            if sentences[i].strip():
                complete_sentences.append(sentences[i].strip())
            i += 1
    
    # 1-2문장씩 페이지로 구성
    pages = []
    current_page_num = 1
    
    i = 0
    while i < len(complete_sentences):
        # 1-2문장을 한 페이지에 넣기
        page_sentences = complete_sentences[i:i + sentences_per_page]
        page_text = " ".join(page_sentences)
        
        pages.append(StoryPage(
            page=current_page_num,
            text=page_text,
            audio_url=None  # 나중에 오디오 생성 시 업데이트
        ))
        
        i += sentences_per_page
        current_page_num += 1
    
    return pages

def calculate_max_tokens(text_length: int) -> int:
    """텍스트 길이에 따라 적절한 max_tokens 계산"""
    if text_length < 10:
        return 300
    elif text_length < 20:
        return 500
    elif text_length < 50:
        return 800
    elif text_length < 100:
        return 1200
    else:
        return 86 * 30

def save_audio_file(wavs: torch.Tensor, sampling_rate: int, output_path: Path):
    """오디오 파일 저장 (torchaudio 버그 우회)"""
    sf.write(str(output_path), wavs[0].squeeze(0).numpy(), sampling_rate)

def generate_tts_audio(text: str, speaker_embedding: torch.Tensor, language: str = "ko", 
                       speaking_rate: float = 15.0, pitch_std: float = 30.0,
                       emotion: Optional[str] = None) -> torch.Tensor:
    """TTS 오디오 생성"""
    cond_dict = make_cond_dict(
        text=text,
        speaker=speaker_embedding,
        language=language,
        speaking_rate=speaking_rate,
        pitch_std=pitch_std
    )
    
    # 감정 추가 (선택적)
    if emotion:
        emotion_map = {
            "happy": "happiness", "happiness": "happiness",
            "sad": "sadness", "sadness": "sadness",
            "angry": "anger", "anger": "anger",
            "fear": "fear"
        }
        emotion_key = emotion_map.get(emotion.lower())
        if emotion_key:
            cond_dict[emotion_key] = 0.7
    
    conditioning = model.prepare_conditioning(cond_dict)
    
    with torch.no_grad():
        max_tokens = calculate_max_tokens(len(text))
        codes = model.generate(
            conditioning,
            max_new_tokens=max_tokens,
            sampling_params={"min_p": 0.1, "temperature": 1.0}
        )
        return model.autoencoder.decode(codes).cpu()

def check_mongodb_available():
    """MongoDB 연결 확인"""
    if not MONGODB_AVAILABLE or storybook_repo is None:
        raise HTTPException(
            status_code=500,
            detail="MongoDB가 연결되지 않았습니다. MONGO_URI 환경 변수를 설정하세요."
        )

def storybookdb_to_storyinfo(story_db: "StorybookDB") -> StoryInfo:
    """StorybookDB를 StoryInfo로 변환"""
    pages = split_story_into_pages(story_db.content)
    title = story_db.filename.replace(".txt", "") if story_db.filename else "제목 없음"
    
    return StoryInfo(
        id=str(story_db.id),
        title=title,
        text=story_db.content,
        pages=pages,
        audio_url=None,
        character_id=None,
        created_at=story_db.uploadedAt.isoformat() if story_db.uploadedAt else None
    )

# ==================== 시작/종료 이벤트 ====================

@app.on_event("startup")
async def startup_event():
    """서버 시작시 모델 로드"""
    global model, character_repo, storybook_repo, audio_cache_repo
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
    print(f"✅ Loaded {len(characters_db)} characters from local storage")
    
    # MongoDB 연결 및 Repository 초기화
    if MONGODB_AVAILABLE:
        try:
            print("\n🗄️ Connecting to MongoDB...")
            await connect_to_mongo()
            
            # Repository 인스턴스 생성
            db = get_database()
            if db:
                character_repo = CharacterRepository(db)
                storybook_repo = StorybookRepository(db)
                audio_cache_repo = AudioCacheRepository(db)
                print("✅ Repositories initialized")
        except Exception as e:
            print(f"⚠️ MongoDB connection failed: {e}")
            print("⚠️ MongoDB features will be disabled")
            character_repo = None
            storybook_repo = None
            audio_cache_repo = None
    else:
        print("\n⚠️ MongoDB not available")
        character_repo = None
        storybook_repo = None
        audio_cache_repo = None
    
    print("\n" + "=" * 60)
    print("✨ Server is ready!")
    print("📖 API Documentation: {IP주소:port}/docs")
    print("=" * 60 + "\n")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료시 MongoDB 연결 종료"""
    if MONGODB_AVAILABLE:
        try:
            await close_mongo_connection()
        except Exception as e:
            print(f"⚠️ Error closing MongoDB connection: {e}")

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
        
        # 6. 참조 오디오 저장
        ref_audio_path = REFERENCE_DIR / f"{character_id}.wav"
        save_audio_file(wav, sampling_rate, ref_audio_path)
        
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
        
        # 3. TTS 생성
        speaking_rate = request.speaking_rate if request.speaking_rate > 1.0 else 15.0
        print(f"🎤 Generating TTS for character '{request.character_id}'...")
        wavs = generate_tts_audio(
            text=request.text,
            speaker_embedding=speaker_embedding,
            language=request.language,
            speaking_rate=speaking_rate,
            emotion=request.emotion
        )
        
        # 4. 파일 저장
        character_name = characters_db[request.character_id]["name"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{character_name}_{timestamp}.wav"
        output_path = OUTPUTS_DIR / filename
        save_audio_file(wavs, model.autoencoder.sampling_rate, output_path)
        
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
            wavs = generate_tts_audio(text, speaker_embedding, language)
            filename = f"{character_id}_batch_{idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            output_path = OUTPUTS_DIR / filename
            save_audio_file(wavs, model.autoencoder.sampling_rate, output_path)
            
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
                wavs = generate_tts_audio(text, speaker_embedding, language="ko")
                save_audio_file(wavs, model.autoencoder.sampling_rate, cached_file)
                
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

@app.get("/cache/{character_id}/{story_id}/{filename}")
async def get_cached_audio(character_id: str, story_id: str, filename: str):
    """
    캐시된 오디오 파일 제공 (story_id 포함)
    
    Args:
        character_id: 캐릭터 ID
        story_id: 스토리 ID
        filename: 파일명
    """
    file_path = CACHE_DIR / character_id / story_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Cached audio not found")
    return FileResponse(file_path, media_type="audio/wav")

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
            
            # Speaker Embedding 로드 및 TTS 생성
            speaker_embedding = load_character_embedding(request.character_id)
            wavs = generate_tts_audio(llm_text, speaker_embedding, language="ko")
            
            # 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_{request.character_id}_{timestamp}.wav"
            output_path = OUTPUTS_DIR / filename
            save_audio_file(wavs, model.autoencoder.sampling_rate, output_path)
            
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
        "mongodb_connected": storybook_repo is not None,
        "database_name": os.getenv("MONGO_DB_NAME", "not set"),
        "collections": [],
        "stories_count": 0,
        "error": None
    }
    
    if not MONGODB_AVAILABLE:
        debug_info["error"] = "MongoDB modules not available"
        return debug_info
    
    if storybook_repo is None:
        debug_info["error"] = "MongoDB not connected"
        return debug_info
    
    try:
        db = get_database()
        if db:
            # 컬렉션 목록 가져오기
            debug_info["collections"] = await db.list_collection_names()
            
            # "texts" 컬렉션 확인
            if "texts" in debug_info["collections"]:
                debug_info["stories_count"] = await storybook_repo.collection.count_documents({})
                
                # 샘플 문서 하나 가져오기
                sample = await storybook_repo.collection.find_one()
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
    check_mongodb_available()
    
    try:
        # Repository를 사용하여 동화 목록 조회
        all_stories = await storybook_repo.get_all()
        
        # 최대 5개로 제한 (최신순 정렬)
        limit = min(limit, 5)
        sorted_stories = sorted(all_stories, key=lambda x: x.id, reverse=True)[:limit]
        
        # StorybookDB를 StoryInfo로 변환
        stories_list = [storybookdb_to_storyinfo(story_db) for story_db in sorted_stories]
        
        # 전체 개수
        total = len(all_stories)
        
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
    check_mongodb_available()
    
    try:
        story_db = await storybook_repo.get_by_id(story_id)
        if not story_db:
            raise HTTPException(status_code=404, detail="Story not found")
        return storybookdb_to_storyinfo(story_db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching story: {e}")
        raise HTTPException(status_code=500, detail=f"동화 조회 중 오류: {str(e)}")

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
async def pregenerate_story_pages_audio(story_id: str, character_id: str = Form(...)):
    """
    동화의 모든 페이지에 대한 오디오를 미리 생성
    
    Args:
        story_id: 동화 ID
        character_id: 캐릭터 ID
        
    Returns:
        생성된 페이지별 오디오 정보
    """
    check_mongodb_available()
    
    # 동화 및 캐릭터 확인
    story_db = await storybook_repo.get_by_id(story_id)
    if not story_db:
        raise HTTPException(status_code=404, detail="Story not found")
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    speaker_embedding = load_character_embedding(character_id)
    pages = split_story_into_pages(story_db.content)
    cache_dir = CACHE_DIR / character_id / story_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    generated_pages = []
    print(f"🎤 Pre-generating audio for story '{story_id}' ({len(pages)} pages)...")
    
    for page in pages:
        try:
            audio_filename = f"page_{page.page}.wav"
            audio_path = cache_dir / audio_filename
            
            if audio_path.exists():
                print(f"✅ Page {page.page} already exists, skipping...")
                audio_url = f"/cache/{character_id}/{story_id}/{audio_filename}"
            else:
                print(f"🎤 Generating audio for page {page.page}...")
                wavs = generate_tts_audio(page.text, speaker_embedding, language="ko")
                save_audio_file(wavs, model.autoencoder.sampling_rate, audio_path)
                audio_url = f"/cache/{character_id}/{story_id}/{audio_filename}"
                print(f"✅ Page {page.page} audio generated")
                
            generated_pages.append({
                "page": page.page,
                "text": page.text,
                "audio_url": audio_url
            })
        except Exception as e:
            print(f"❌ Error generating page {page.page}: {e}")
            generated_pages.append({
                "page": page.page,
                "text": page.text,
                "error": str(e)
            })
    
    return {
        "story_id": story_id,
        "character_id": character_id,
        "total_pages": len(pages),
        "generated_pages": generated_pages
    }

@app.get("/stories/{story_id}/check-audio")
async def check_story_audio_files(story_id: str, character_id: str = Query(...)):
    """
    동화의 페이지별 오디오 파일이 이미 생성되어 있는지 확인
    
    Args:
        story_id: 동화 ID
        character_id: 캐릭터 ID (쿼리 파라미터)
        
    Returns:
        생성된 오디오 파일 목록
    """
    check_mongodb_available()
    
    story_db = await storybook_repo.get_by_id(story_id)
    if not story_db:
        raise HTTPException(status_code=404, detail="Story not found")
        
    pages = split_story_into_pages(story_db.content)
    cache_dir = CACHE_DIR / character_id / story_id
    existing_audio = []
    
    for page in pages:
        audio_filename = f"page_{page.page}.wav"
        audio_path = cache_dir / audio_filename
        
        if audio_path.exists():
            audio_url = f"/cache/{character_id}/{story_id}/{audio_filename}"
            existing_audio.append({
                "page": page.page,
                "text": page.text,
                "audio_url": audio_url
            })
    
    return {
        "story_id": story_id,
        "character_id": character_id,
        "total_pages": len(pages),
        "existing_audio_count": len(existing_audio),
        "existing_audio": existing_audio,
        "all_audio_exists": len(existing_audio) == len(pages)
    }

# ==================== 메인 실행 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host= "0.0.0.0",
        port=8000,
        log_level="info"
    )