"""
MongoDB 데이터 접근 레이어
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from bson import ObjectId
import torch
import io

from .models import CharacterDB, StorybookDB, AudioCacheDB

class CharacterRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["characters"]
        self.gridfs = db.fs  # GridFS
    
    async def get_all(self) -> List[CharacterDB]:
        """모든 캐릭터 조회"""
        cursor = self.collection.find()
        characters = await cursor.to_list(length=100)
        return [CharacterDB(**char) for char in characters]
    
    async def get_by_id(self, character_id: str) -> Optional[CharacterDB]:
        """캐릭터 ID로 조회"""
        char = await self.collection.find_one({"character_id": character_id})
        return CharacterDB(**char) if char else None
    
    async def save_embedding(self, character_id: str, embedding: torch.Tensor) -> str:
        """임베딩을 GridFS에 저장"""
        buffer = io.BytesIO()
        torch.save(embedding, buffer)
        buffer.seek(0)
        
        from motor.motor_asyncio import AsyncIOMotorGridFSBucket
        bucket = AsyncIOMotorGridFSBucket(self.collection.database)
        
        file_id = await bucket.upload_from_stream(
            f"{character_id}_embedding.pt",
            buffer,
            metadata={"character_id": character_id, "type": "embedding"}
        )
        return str(file_id)
    
    async def load_embedding(self, file_id: str) -> torch.Tensor:
        """GridFS에서 임베딩 로드"""
        from motor.motor_asyncio import AsyncIOMotorGridFSBucket
        bucket = AsyncIOMotorGridFSBucket(self.collection.database)
        
        grid_out = await bucket.open_download_stream(ObjectId(file_id))
        data = await grid_out.read()
        buffer = io.BytesIO(data)
        embedding = torch.load(buffer, map_location='cpu')
        return embedding

class StorybookRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["texts"]  # 기존 컬렉션 사용
    
    async def get_all(self) -> List[StorybookDB]:
        """모든 동화책 조회"""
        cursor = self.collection.find()
        stories = await cursor.to_list(length=100)
        return [StorybookDB(**story) for story in stories]
    
    async def get_by_id(self, story_id: str) -> Optional[StorybookDB]:
        """동화책 ID로 조회"""
        story = await self.collection.find_one({"_id": ObjectId(story_id)})
        return StorybookDB(**story) if story else None
    
    def chunk_text(self, text: str, lines_per_chunk: int = 4) -> List[str]:
        """텍스트를 4-5줄 단위로 분할"""
        # \r\n을 \n으로 통일
        text = text.replace('\r\n', '\n')
        
        # 문단 단위로 분리 (빈 줄 기준)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        
        for para in paragraphs:
            lines = para.split('\n')
            for line in lines:
                if line.strip():
                    current_chunk.append(line.strip())
                    if len(current_chunk) >= lines_per_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
        
        # 남은 줄 처리
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

class AudioCacheRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["audio_cache"]
    
    async def find_cache(self, character_id: str, story_id: str, chunk_index: int) -> Optional[AudioCacheDB]:
        """캐시된 오디오 찾기"""
        cache = await self.collection.find_one({
            "character_id": character_id,
            "story_id": story_id,
            "chunk_index": chunk_index
        })
        return AudioCacheDB(**cache) if cache else None
    
    async def save_cache(self, cache: AudioCacheDB) -> str:
        """오디오 캐시 저장"""
        result = await self.collection.insert_one(cache.dict(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)