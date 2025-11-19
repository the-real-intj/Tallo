"""
MongoDB 연결 및 GridFS 관리
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:port")
DATABASE_NAME = os.getenv("MONGO_DB_NAME", "Tallo")

# Async 클라이언트 (FastAPI용)
class MongoDatabase:
    client: AsyncIOMotorClient = None
    database = None
    gridfs_bucket: AsyncIOMotorGridFSBucket = None

async def connect_to_mongo():
    """MongoDB 연결"""
    MongoDatabase.client = AsyncIOMotorClient(MONGO_URI)
    MongoDatabase.database = MongoDatabase.client[DATABASE_NAME]
    MongoDatabase.gridfs_bucket = AsyncIOMotorGridFSBucket(MongoDatabase.database)
    print(f"✅ Connected to MongoDB: {DATABASE_NAME}")

async def close_mongo_connection():
    """MongoDB 연결 종료"""
    MongoDatabase.client.close()
    print("❌ Closed MongoDB connection")

def get_database():
    """데이터베이스 인스턴스 반환"""
    return MongoDatabase.database

def get_gridfs():
    """GridFS 버킷 반환"""
    return MongoDatabase.gridfs_bucket