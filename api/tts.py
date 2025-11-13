from __future__ import annotations

import uuid
from pathlib import Path

import torch
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, model_validator

from Zonos.tts import get_tts


router = APIRouter(prefix="/tts", tags=["tts"])

OUTPUT_DIR = Path("outputs/tts")
TEXT_ASSET_DIR = Path("Zonos/assets")


class TTSRequest(BaseModel):
    """TTS 요청 본문."""

    text: str | None = Field(
        default=None,
        description="합성할 한국어 텍스트 (직접 입력)",
    )
    text_asset: str | None = Field(
        default=None,
        description="`Zonos/assets`에 위치한 텍스트 파일 이름 (예: 아기돼지삼형제.txt)",
    )
    language: str = Field(
        default="ko",
        description="언어 코드 (기본값: ko)",
    )
    as_file: bool = Field(
        default=True,
        description="True면 파일로 응답, False면 스트리밍으로 반환",
    )
    emotion: list[float] | None = Field(
        default=None,
        description="감정 벡터 [기쁨, 슬픔, 혐오, 공포, 놀람, 분노, 기타, 중립]. 예: 공포 강조 [0.1, 0.1, 0.0, 0.7, 0.0, 0.0, 0.1, 0.0]",
    )
    auto_emotion: bool = Field(
        default=False,
        description="True면 텍스트 내용을 분석해 자동으로 감정 적용 (emotion보다 우선순위 낮음)",
    )
    speaker_wav: str | None = Field(
        default=None,
        description="스피커 샘플 파일 이름 (예: 'Ana_20sec.wav'). Zonos/assets/ 디렉터리에 있어야 합니다.",
    )

    @model_validator(mode='after')
    def _at_least_one_text(self) -> 'TTSRequest':
        text = self.text
        text_asset = self.text_asset
        if not (text and text.strip()) and not text_asset:
            raise ValueError("텍스트(text) 또는 text_asset 중 하나를 지정해 주세요.")
        return self


def _split_text_by_sentences(text: str) -> list[str]:
    """텍스트를 문장 단위로 분리합니다."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s.strip()]


@router.post(
    "/synthesize",
    summary="텍스트를 음성으로 합성 (자동 긴/짧은 텍스트 처리)",
    description="입력된 텍스트를 Zonos TTS로 합성하여 WAV 파일 또는 스트림으로 반환합니다. 긴 텍스트는 자동으로 청크로 나눠 처리합니다.",
)
async def synthesize_tts(
    payload: TTSRequest,
    background_tasks: BackgroundTasks,
):
    text = payload.text

    if text is None or not text.strip():
        if payload.text_asset is None:
            raise HTTPException(status_code=400, detail="텍스트를 입력해 주세요.")

        asset_path = TEXT_ASSET_DIR / payload.text_asset
        if not asset_path.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"텍스트 파일을 찾을 수 없습니다: {payload.text_asset}",
            )

        try:
            text = asset_path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - 파일 읽기 실패
            raise HTTPException(
                status_code=500,
                detail=f"텍스트 파일을 읽는 중 오류가 발생했습니다: {exc}",
            ) from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="텍스트를 입력해 주세요.")

    # 자동 분기: 문장 수가 5개 이상이면 긴 텍스트로 처리
    sentences = _split_text_by_sentences(text)
    if len(sentences) >= 5:
        return await _synthesize_long_text(text, payload, background_tasks)
    else:
        return await _synthesize_short_text(text, payload, background_tasks)


async def _synthesize_short_text(
    text: str,
    payload: TTSRequest,
    background_tasks: BackgroundTasks,
):
    from utils.emotion_detector import detect_emotion_from_text
    
    # 감정 결정 우선순위: 명시적 emotion > auto_emotion > 기본값
    emotion = payload.emotion
    if emotion is None and payload.auto_emotion:
        emotion = detect_emotion_from_text(text)

    # speaker_wav 파일명을 get_tts에 전달
    speaker_wav = payload.speaker_wav
    tts = get_tts(speaker_wav=speaker_wav)

    if payload.as_file:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        file_path = OUTPUT_DIR / f"{uuid.uuid4().hex}.wav"
        tts.synthesize(
            text=text,
            language=payload.language,
            output_path=file_path,
            emotion=emotion,
        )

        background_tasks.add_task(_cleanup_file, file_path)
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=file_path.name,
        )

    audio_tensor, metadata = tts.synthesize_to_memory(
        text=text,
        language=payload.language,
    )
    # torchaudio.save로 메모리에 직접 쓰기 힘드니 streaming 처리 (WAV 헤더 직접 작성 필요)
    # 여기서는 간단히 파일 방식만 지원하도록 안내.
    raise HTTPException(
        status_code=501,
        detail="현재는 파일 응답만 지원합니다. as_file=True로 요청해 주세요.",
    )


async def _synthesize_long_text(
    text: str,
    payload: TTSRequest,
    background_tasks: BackgroundTasks,
):
    """긴 텍스트를 청크로 나눠 병렬 합성 후 병합합니다."""
    import asyncio
    import torchaudio
    from concurrent.futures import ThreadPoolExecutor
    from utils.emotion_detector import detect_emotion_from_text
    
    # 텍스트를 3문장씩 청크로 분할
    sentences = _split_text_by_sentences(text)
    chunk_size = 3
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = ' '.join(sentences[i:i+chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    if len(chunks) == 0:
        raise HTTPException(status_code=400, detail="유효한 문장을 찾을 수 없습니다.")

    # speaker_wav 파일명을 get_tts에 전달
    speaker_wav = payload.speaker_wav
    tts = get_tts(speaker_wav=speaker_wav)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def synthesize_chunk(i: int, chunk: str):
        """개별 청크를 합성하는 함수 (병렬 실행용)"""
        # 청크별로 자동 감정 분석 (auto_emotion이 True일 때)
        chunk_emotion = payload.emotion
        if chunk_emotion is None and payload.auto_emotion:
            chunk_emotion = detect_emotion_from_text(chunk)
        
        temp_path = OUTPUT_DIR / f"chunk_{uuid.uuid4().hex}_{i}.wav"
        tts.synthesize(
            text=chunk,
            language=payload.language,
            output_path=temp_path,
            emotion=chunk_emotion,
        )
        return temp_path
    
    temp_files = []
    try:
        # 병렬 처리: CPU 환경에만 권장 (GPU는 max_workers=1 권장)
        # GPU 환경: max_workers=1, CPU 환경: max_workers=2~3
        import torch
        max_workers = 1 if torch.cuda.is_available() else 3
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, synthesize_chunk, i, chunk)
                for i, chunk in enumerate(chunks)
            ]
            temp_files = await asyncio.gather(*tasks)
        
        # 병합
        waveforms = []
        sample_rate = None
        for path in temp_files:
            wav, sr = torchaudio.load(str(path))
            if sample_rate is None:
                sample_rate = sr
            waveforms.append(wav)
        
        merged = torch.cat(waveforms, dim=1)
        final_path = OUTPUT_DIR / f"{uuid.uuid4().hex}.wav"
        torchaudio.save(str(final_path), merged, sample_rate)
        
        # 임시 파일 정리
        for temp_file in temp_files:
            background_tasks.add_task(_cleanup_file, temp_file)
        background_tasks.add_task(_cleanup_file, final_path)
        
        return FileResponse(
            path=final_path,
            media_type="audio/wav",
            filename=final_path.name,
        )
    
    except Exception as exc:
        # 에러 발생 시 임시 파일 정리
        for temp_file in temp_files:
            temp_file.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"TTS 합성 중 오류가 발생했습니다: {exc}",
        ) from exc


def _cleanup_file(path: Path) -> None:
    """응답 이후 생성된 파일을 정리합니다."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass

