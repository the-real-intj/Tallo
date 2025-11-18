"""
API 서버 캐릭터 로딩 테스트
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 환경 변수 로드
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# MongoDB와 TTS API import
from pymongo import MongoClient
import torch
import io

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "story_book")

def test_load_character_embedding(character_id: str):
    """MongoDB에서 캐릭터 임베딩 로드 테스트"""
    print(f"\n{'='*60}")
    print(f"🧪 캐릭터 임베딩 로드 테스트: {character_id}")
    print(f"{'='*60}")

    try:
        # MongoDB 연결
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        characters_collection = db["characters"]

        # 캐릭터 문서 조회
        char_doc = characters_collection.find_one({"character_id": character_id})

        if not char_doc:
            print(f"❌ 캐릭터를 찾을 수 없습니다: {character_id}")
            return False

        print(f"✅ 캐릭터 발견: {char_doc.get('name', 'N/A')}")

        # 임베딩 로드
        if "embedding" in char_doc:
            embedding_bytes = char_doc["embedding"]
            buffer = io.BytesIO(embedding_bytes)
            embedding = torch.load(buffer, map_location='cpu')

            print(f"✅ 임베딩 로드 성공!")
            print(f"   타입: {type(embedding)}")
            print(f"   Shape: {embedding.shape if hasattr(embedding, 'shape') else 'N/A'}")
            print(f"   크기: {len(embedding_bytes):,} bytes")

            return True
        else:
            print(f"❌ 임베딩이 없습니다")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_list_characters():
    """MongoDB에서 캐릭터 목록 조회 테스트"""
    print(f"\n{'='*60}")
    print(f"📋 캐릭터 목록 조회 테스트")
    print(f"{'='*60}")

    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        characters_collection = db["characters"]

        characters_cursor = characters_collection.find()
        characters_list = []

        for char_doc in characters_cursor:
            characters_list.append({
                "id": char_doc.get("character_id", str(char_doc["_id"])),
                "name": char_doc.get("name", ""),
                "description": char_doc.get("description"),
                "language": char_doc.get("language", "ko"),
            })

        print(f"✅ 캐릭터 {len(characters_list)}개 발견:")
        for char in characters_list:
            print(f"   - {char['name']} ({char['id']})")

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 MongoDB 캐릭터 API 테스트 시작\n")

    # 1. 캐릭터 목록 조회 테스트
    success1 = test_list_characters()

    # 2. 각 캐릭터의 임베딩 로드 테스트
    character_ids = ["5fbdc9b344b2", "4c84ef36f400", "6a3fb5695d7c"]
    character_names = ["아나", "하츄핑", "베레사"]

    success2 = True
    for char_id, char_name in zip(character_ids, character_names):
        result = test_load_character_embedding(char_id)
        success2 = success2 and result

    print(f"\n{'='*60}")
    if success1 and success2:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
    print(f"{'='*60}\n")
