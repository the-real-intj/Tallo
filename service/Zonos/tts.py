from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import NamedTuple, Optional, Union

import torch  # type: ignore
import torchaudio  # type: ignore

from zonos.conditioning import make_cond_dict
from zonos.model import Zonos
from zonos.utils import DEFAULT_DEVICE as device


class AudioMetaData(NamedTuple):
    """오디오 메타데이터를 담는 컨테이너."""
    sample_rate: int
    num_frames: int
    num_channels: int
    bits_per_sample: int


class ZonosTTS:
    """
    Zonos 기반 TTS 유틸리티.

    모델은 애플리케이션 시작 시 한 번만 로드하고,
    `synthesize` 메서드로 텍스트를 음성으로 변환합니다.
    """

    def __init__(
        self,
        model_id: str = "Zyphra/Zonos-v0.1-transformer",
        speaker_wav: Union[str, Path] = Path("assets/Ana_20sec.wav"),
        manual_seed: Optional[int] = 421,
    ) -> None:
        self.model_id = model_id
        self.manual_seed = manual_seed
        self.model = Zonos.from_pretrained(model_id, device=device)

        self.speaker_wav_path = Path(speaker_wav)
        # 상대 경로인 경우 이 파일의 위치를 기준으로 변환
        if not self.speaker_wav_path.is_absolute():
            base_dir = Path(__file__).parent
            # 파일명만 전달된 경우 (예: "Ana_20sec.wav") assets/ 디렉터리에서 찾기
            if not self.speaker_wav_path.parent or self.speaker_wav_path.parent == Path('.'):
                # 파일명만 있는 경우 assets/ 디렉터리 추가
                self.speaker_wav_path = base_dir / "assets" / self.speaker_wav_path
            else:
                # 상대 경로가 포함된 경우 (예: "assets/Ana_20sec.wav")
                self.speaker_wav_path = base_dir / self.speaker_wav_path
        
        if not self.speaker_wav_path.exists():
            raise FileNotFoundError(
                f"Speaker WAV 파일을 찾을 수 없습니다: {self.speaker_wav_path}"
            )

        wav, sampling_rate = torchaudio.load(str(self.speaker_wav_path))
        self.speaker_embedding = self.model.make_speaker_embedding(wav, sampling_rate)

    def synthesize(
        self,
        text: str,
        language: str = "ko",
        output_path: Optional[Union[str, Path]] = None,
        speaking_rate: float = 13.0,
        pitch_std: float = 35.0,
        emotion: Optional[list[float]] = None,
    ) -> Path:
        """
        텍스트를 음성으로 변환해 파일로 저장하고 경로를 반환합니다.
        
        Args:
            speaking_rate: 말하기 속도 (10=느림, 15=보통, 30=매우 빠름)
            pitch_std: 억양 변화 (20-45=자연스러움, 60-150=표현력 강함)
            emotion: 감정 벡터 [기쁨, 슬픔, 혐오, 공포, 놀람, 분노, 기타, 중립]
                     각 값은 0.0~1.0, 합계는 1.0에 가깝게
                     예: [0.1, 0.1, 0.0, 0.7, 0.0, 0.0, 0.1, 0.0] = 공포 강조
        """
        if self.manual_seed is not None:
            torch.manual_seed(self.manual_seed)

        # 기본 감정: 약간의 기쁨과 중립
        if emotion is None:
            emotion = [0.3077, 0.0256, 0.0256, 0.0256, 0.0256, 0.0256, 0.2564, 0.3077]

        cond_dict = make_cond_dict(
            text=text,
            speaker=self.speaker_embedding,
            language=language,
            speaking_rate=speaking_rate,
            pitch_std=pitch_std,
            fmax=22050.0,  # 음성 복제 권장값
            emotion=emotion,
        )
        conditioning = self.model.prepare_conditioning(cond_dict)
        codes = self.model.generate(conditioning)
        wavs = self.model.autoencoder.decode(codes).cpu()

        if output_path is None:
            output_path = Path("sample.wav")
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(output_path), wavs[0], self.model.autoencoder.sampling_rate)

        return output_path

    def synthesize_to_memory(
        self,
        text: str,
        language: str = "ko-kr",
    ) -> tuple[torch.Tensor, AudioMetaData]:
        """
        텍스트를 음성으로 변환하고, 파일로 저장하지 않고 메모리로 반환합니다.
        FastAPI에서 스트리밍으로 내려줄 때 사용할 수 있습니다.
        """
        if self.manual_seed is not None:
            torch.manual_seed(self.manual_seed)

        cond_dict = make_cond_dict(
            text=text,
            speaker=self.speaker_embedding,
            language=language,
        )
        conditioning = self.model.prepare_conditioning(cond_dict)
        codes = self.model.generate(conditioning)
        wavs = self.model.autoencoder.decode(codes).cpu()

        metadata = AudioMetaData(
            sample_rate=self.model.autoencoder.sampling_rate,
            num_frames=wavs[0].size(-1),
            num_channels=wavs[0].size(0),
            bits_per_sample=16,
        )

        return wavs[0], metadata


@lru_cache(maxsize=10)
def get_tts(speaker_wav: str | None = None) -> ZonosTTS:
    """
    애플리케이션 전체에서 공유할 ZonosTTS 인스턴스를 반환합니다.
    speaker_wav가 None이면 기본값(Ana_20sec.wav)을 사용합니다.
    """
    if speaker_wav is None:
        return ZonosTTS()
    return ZonosTTS(speaker_wav=speaker_wav)

