"""
MongoDB 문서 모델 (Pydantic)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId

class CharacterDB(BaseModel):
    """캐릭터 MongoDB 문서"""
    id: Optional[str] = Field(None, alias="_id")
    character_id: str
    name: str
    description: Optional[str] = None
    language: str = "ko"
    created_at: datetime
    embedding_file_id: Optional[str] = None  # GridFS file ID
    reference_audio_id: Optional[str] = None  # GridFS file ID

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

class StorybookDB(BaseModel):
    """동화책 MongoDB 문서 (기존 texts 컬렉션 호환)"""
    id: Optional[str] = Field(None, alias="_id")
    filename: str
    content: str
    uploadedAt: datetime
    
    # 추가 필드 (선택)
    title: Optional[str] = None
    description: Optional[str] = None
    total_chunks: Optional[int] = None
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

class AudioCacheDB(BaseModel):
    """오디오 캐시 문서"""
    id: Optional[str] = Field(None, alias="_id")
    character_id: str
    story_id: str
    chunk_index: int
    audio_file_id: str  # GridFS file ID
    generated_at: datetime
    expires_at: Optional[datetime] = None  # TTL 인덱스 가능
    
    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True