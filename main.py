from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.tts import router as tts_router
from api.tts_long import router as tts_long_router


app = FastAPI()

# CORS 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tts_router)
app.include_router(tts_long_router)