"""긴 텍스트를 청크로 나눠 TTS 생성 후 병합하는 유틸리티."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import List

import torchaudio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, model_validator

from Zonos.tts import get_tts


router = APIRouter(prefix="/tts", tags=["tts"])

OUTPUT_DIR = Path("outputs/tts")
TEXT_ASSET_DIR = Path("Zonos/assets")


class LongTTSRequest(BaseModel):
    """긴 텍스트 TTS 요청 본문."""

    text: str | None = Field(
        default=None,
        description="합성할 텍스트 (직접 입력)",
    )
    text_asset: str | None = Field(
        default=None,
        description="`Zonos/assets`에 위치한 텍스트 파일 이름",
    )
    language: str = Field(
        default="ko",
        description="언어 코드 (기본값: ko)",
    )
    chunk_sentences: int = Field(
        default=3,
        description="한 청크당 문장 수 (기본값: 3문장씩)",
    )

    @model_validator(mode='after')
    def _at_least_one_text(self) -> 'LongTTSRequest':
        if not (self.text and self.text.strip()) and not self.text_asset:
            raise ValueError("텍스트(text) 또는 text_asset 중 하나를 지정해 주세요.")
        return self


def split_text_by_sentences(text: str, chunk_size: int = 3) -> List[str]:
    """텍스트를 문장 단위로 나눠 청크로 묶습니다."""
    import re
    # 한국어 문장 구분: 마침표, 느낌표, 물음표 뒤
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = ' '.join(sentences[i:i+chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def merge_wav_files(file_paths: List[Path], output_path: Path) -> None:
    """여러 WAV 파일을 하나로 병합합니다."""
    waveforms = []
    sample_rate = None
    
    for path in file_paths:
        wav, sr = torchaudio.load(str(path))
        if sample_rate is None:
            sample_rate = sr
        elif sample_rate != sr:
            raise ValueError(f"샘플레이트가 일치하지 않습니다: {sr} vs {sample_rate}")
        waveforms.append(wav)
    
    merged = torchaudio.functional.concatenate(waveforms, dim=1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(output_path), merged, sample_rate)


@router.post(
    "/synthesize-long",
    summary="긴 텍스트를 청크로 나눠 음성 합성",
    description="긴 텍스트를 문장 단위로 나눠 여러 번 합성 후 하나의 WAV로 병합합니다.",
)
async def synthesize_long_tts(
    payload: LongTTSRequest,
    background_tasks: BackgroundTasks,
):
    text = payload.text

    # text_asset에서 읽기
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
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"텍스트 파일을 읽는 중 오류가 발생했습니다: {exc}",
            ) from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="텍스트를 입력해 주세요.")

    # 텍스트를 청크로 분할
    chunks = split_text_by_sentences(text, chunk_size=payload.chunk_sentences)
    
    if len(chunks) == 0:
        raise HTTPException(status_code=400, detail="유효한 문장을 찾을 수 없습니다.")

    tts = get_tts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    temp_files = []
    try:
        # 각 청크를 개별 합성
        for i, chunk in enumerate(chunks):
            temp_path = OUTPUT_DIR / f"chunk_{uuid.uuid4().hex}_{i}.wav"
            tts.synthesize(text=chunk, language=payload.language, output_path=temp_path)
            temp_files.append(temp_path)
        
        # 병합
        final_path = OUTPUT_DIR / f"{uuid.uuid4().hex}.wav"
        merge_wav_files(temp_files, final_path)
        
        # 임시 파일 정리
        for temp_file in temp_files:
            background_tasks.add_task(_cleanup_file, temp_file)
        background_tasks.add_task(_cleanup_file, final_path)
        
        from fastapi.responses import FileResponse
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

