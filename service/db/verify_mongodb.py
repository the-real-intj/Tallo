"""
MongoDB 캐릭터 마이그레이션 확인 스크립트
"""

import os
import sys
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 환경 변수 로드
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# MongoDB 연결
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "story_book")

def verify_characters():
    """MongoDB에 저장된 캐릭터 확인"""
    print("=" * 60)
    print("🔍 MongoDB 캐릭터 확인")
    print("=" * 60)

    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        characters_collection = db["characters"]

        # 모든 캐릭터 조회
        characters = list(characters_collection.find({}))

        print(f"\n✅ MongoDB 연결 성공: {MONGODB_DB_NAME}")
        print(f"📊 저장된 캐릭터 수: {len(characters)}")
        print("\n" + "=" * 60)

        for char in characters:
            print(f"\n🎭 캐릭터: {char.get('name', 'N/A')}")
            print(f"   ID: {char.get('character_id', 'N/A')}")
            print(f"   설명: {char.get('description', 'N/A')}")
            print(f"   언어: {char.get('language', 'N/A')}")
            print(f"   생성일: {char.get('created_at', 'N/A')}")

            # 임베딩 정보
            if 'embedding' in char:
                embedding_size = len(char['embedding'])
                print(f"   ✅ 임베딩: {embedding_size:,} bytes ({embedding_size / 1024:.1f} KB)")
            else:
                print(f"   ❌ 임베딩: 없음")

            # 오디오 정보
            if 'reference_audio_binary' in char:
                audio_size = len(char['reference_audio_binary'])
                audio_filename = char.get('audio_filename', 'N/A')
                print(f"   ✅ 오디오: {audio_filename} ({audio_size / 1024:.1f} KB)")
            else:
                print(f"   ⚠️  오디오: 없음")

        print("\n" + "=" * 60)
        print("✨ 확인 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_characters()
