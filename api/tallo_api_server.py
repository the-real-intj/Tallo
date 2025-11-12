"""
Zonos Multi-Character TTS API Server
여러 캐릭터의 Speaker Embedding을 관리하고 TTS를 생성하는 FastAPI 서버
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import torch
import torchaudio
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime

from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from zonos.utils import DEFAULT_DEVICE as device

# ==================== 설정 ====================
app = FastAPI(
    title="Zonos Multi-Character TTS API",
    version="2.0.0",
    description="다중 캐릭터 음성 생성 및 관리 시스템"
)

# CORS 설정 (React와 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 디렉토리 설정
BASE_DIR = Path(__file__).parent.parent
EMBEDDINGS_DIR = BASE_DIR / "embeddings"
REFERENCE_DIR = BASE_DIR / "reference_audios"
OUTPUTS_DIR = BASE_DIR / "outputs"
CACHE_DIR = BASE_DIR / "cache"

for directory in [EMBEDDINGS_DIR, REFERENCE_DIR, OUTPUTS_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True)

# 캐릭터 메타데이터 파일
CHARACTERS_DB = EMBEDDINGS_DIR / "characters.json"

# 전역 변수
model = None
characters_db: Dict = {}

# ==================== 데이터 모델 ====================

class TTSRequest(BaseModel):
    """TTS 생성 요청"""
    text: str
    character_id: str
    language: str = "en-us"
    speaking_rate: float = 1.0
    pitch: float = 1.0
    emotion: Optional[str] = None  # happy, sad, angry, fear

class CharacterInfo(BaseModel):
    """캐릭터 정보"""
    id: str
    name: str
    description: Optional[str] = None
    language: str = "en-us"
    created_at: str
    reference_audio: Optional[str] = None

class CreateCharacterRequest(BaseModel):
    """캐릭터 생성 요청"""
    name: str
    description: Optional[str] = None
    language: str = "en-us"

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

# ==================== 시작/종료 이벤트 ====================

@app.on_event("startup")
async def startup_event():
    """서버 시작시 모델 로드"""
    global model
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
    language: str = Form("en-us"),
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
        torchaudio.save(str(ref_audio_path), wav, sampling_rate)
        
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
        cond_dict = make_cond_dict(
            text=request.text,
            speaker=speaker_embedding,
            language=request.language,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch
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
            codes = model.generate(conditioning)
            wavs = model.autoencoder.decode(codes).cpu()
        
        # 5. 파일 저장
        character_name = characters_db[request.character_id]["name"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{character_name}_{timestamp}.wav"
        output_path = OUTPUTS_DIR / filename
        
        torchaudio.save(str(output_path), wavs[0], model.autoencoder.sampling_rate)
        
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
    language: str = Form("en-us")
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
                codes = model.generate(conditioning)
                wavs = model.autoencoder.decode(codes).cpu()
            
            filename = f"{character_id}_batch_{idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            output_path = OUTPUTS_DIR / filename
            torchaudio.save(str(output_path), wavs[0], model.autoencoder.sampling_rate)
            
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

# ==================== 메인 실행 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host= "{IP주소}",
        port=8000,
        log_level="info"
    )