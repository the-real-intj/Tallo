"""
기존 로컬 캐릭터 임베딩을 MongoDB로 마이그레이션하는 스크립트

사용법:
    python migrate_characters_to_mongodb.py
"""

import os
import sys
import json
import torch
import io
from pathlib import Path
from pymongo import MongoClient
from bson import Binary
from dotenv import load_dotenv
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 환경 변수 로드
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# MongoDB 연결
MONGODB_URI = os.getenv("MONGODB_URI", "MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "MONGODB_DB_NAME")  # 실제 사용 중인 DB

# 로컬 경로
EMBEDDINGS_DIR = BASE_DIR / "embeddings"
CHARACTERS_JSON = EMBEDDINGS_DIR / "characters.json"

def migrate_characters():
    """
    로컬 캐릭터 임베딩을 MongoDB로 마이그레이션
    """
    print("=" * 60)
    print("🔄 캐릭터 임베딩 MongoDB 마이그레이션")
    print("=" * 60)

    # MongoDB 연결
    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        characters_collection = db["characters"]
        print(f"✅ MongoDB 연결 성공: {MONGODB_URI}")
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}")
        return

    # characters.json 로드
    if not CHARACTERS_JSON.exists():
        print(f"❌ characters.json 파일을 찾을 수 없습니다: {CHARACTERS_JSON}")
        return

    with open(CHARACTERS_JSON, 'r', encoding='utf-8') as f:
        characters_db = json.load(f)

    print(f"\n📚 로컬 캐릭터 수: {len(characters_db)}")

    # 각 캐릭터 마이그레이션
    migrated_count = 0
    skipped_count = 0

    for character_id, char_info in characters_db.items():
        print(f"\n🔄 처리 중: {char_info.get('name', character_id)}")

        # 이미 MongoDB에 있는지 확인
        existing = characters_collection.find_one({"character_id": character_id})
        if existing:
            print(f"⏭️  이미 존재함, 스킵: {character_id}")
            skipped_count += 1
            continue

        # 임베딩 파일 로드
        embedding_path = EMBEDDINGS_DIR / f"{character_id}.pt"
        if not embedding_path.exists():
            print(f"⚠️  임베딩 파일 없음: {embedding_path}")
            continue

        try:
            # 1. 임베딩 로드
            embedding = torch.load(embedding_path, map_location='cpu')

            # 임베딩을 바이너리로 변환
            buffer = io.BytesIO()
            torch.save(embedding, buffer)
            embedding_bytes = buffer.getvalue()

            # 2. 참조 오디오 로드 (있으면)
            audio_binary = None
            audio_filename = None
            reference_audio_path = char_info.get("reference_audio")

            if reference_audio_path:
                # 상대 경로를 절대 경로로 변환
                audio_abs_path = BASE_DIR.parent / reference_audio_path  # service/.. = 프로젝트 루트

                if audio_abs_path.exists():
                    print(f"  📁 오디오 파일 발견: {audio_abs_path.name}")
                    with open(audio_abs_path, 'rb') as audio_file:
                        audio_binary = Binary(audio_file.read())
                        audio_filename = audio_abs_path.name
                    print(f"  ✅ 오디오 로드 완료 ({len(audio_binary) / 1024:.1f} KB)")
                else:
                    print(f"  ⚠️  오디오 파일 없음: {audio_abs_path}")

            # 3. MongoDB 문서 생성
            mongo_doc = {
                "character_id": character_id,
                "name": char_info.get("name", ""),
                "description": char_info.get("description"),
                "language": char_info.get("language", "ko"),
                "created_at": datetime.fromisoformat(char_info["created_at"]) if "created_at" in char_info else datetime.now(),
                "reference_audio_path": reference_audio_path,  # 원본 경로 (참고용)
                "embedding": Binary(embedding_bytes),
            }

            # 오디오가 있으면 추가
            if audio_binary:
                mongo_doc["reference_audio_binary"] = audio_binary
                mongo_doc["audio_filename"] = audio_filename

            # 4. MongoDB에 삽입
            characters_collection.insert_one(mongo_doc)

            audio_info = f" + 오디오 ({audio_filename})" if audio_binary else ""
            print(f"✅ 마이그레이션 완료: {char_info.get('name', character_id)}{audio_info}")
            migrated_count += 1

        except Exception as e:
            print(f"❌ 마이그레이션 실패: {e}")

    print("\n" + "=" * 60)
    print(f"✨ 마이그레이션 완료!")
    print(f"✅ 성공: {migrated_count}개")
    print(f"⏭️  스킵: {skipped_count}개")
    print("=" * 60)

if __name__ == "__main__":
    migrate_characters()
