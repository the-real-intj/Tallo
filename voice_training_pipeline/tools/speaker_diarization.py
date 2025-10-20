# -*- coding: utf-8 -*-
"""
화자 분리 도구 (Speaker Diarization)
여러 사람 목소리가 섞인 오디오에서 특정 화자만 추출합니다.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class SpeakerDiarization:
    """
    화자 분리 및 특정 화자 추출

    주의: 이 방법은 완벽하지 않습니다!
    가장 좋은 방법은 퉁퉁이만 나오는 영상을 사용하는 것입니다.
    """

    def __init__(self):
        """화자 분리 도구 초기화"""
        self.method = "pyannote"  # 또는 "resemblyzer"

    def separate_speakers(
        self,
        audio_path: str,
        num_speakers: int = 5,
        output_dir: str = "./data/separated"
    ) -> List[Tuple[float, float, int]]:
        """
        오디오에서 화자별로 분리

        Args:
            audio_path: 오디오 파일 경로
            num_speakers: 예상 화자 수
            output_dir: 출력 디렉토리

        Returns:
            [(시작시간, 종료시간, 화자ID), ...]
        """
        print("\n⚠️  화자 분리는 실험적 기능입니다!")
        print("💡 권장: 퉁퉁이만 나오는 유튜브 영상을 사용하세요.\n")

        try:
            from pyannote.audio import Pipeline
        except ImportError:
            print("❌ pyannote.audio가 설치되지 않았습니다.")
            print("\n설치 방법:")
            print("1. pip install pyannote.audio")
            print("2. Hugging Face 토큰 필요: https://huggingface.co/settings/tokens")
            print("3. 모델 액세스 승인: https://huggingface.co/pyannote/speaker-diarization")
            return []

        # Hugging Face 토큰 확인
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            print("❌ HUGGINGFACE_TOKEN이 설정되지 않았습니다.")
            print("\n.env 파일에 추가하세요:")
            print("HUGGINGFACE_TOKEN=your_token_here")
            return []

        print("🎤 화자 분리 시작...")
        print(f"   오디오: {audio_path}")
        print(f"   예상 화자 수: {num_speakers}")

        # Pipeline 로드
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization",
            use_auth_token=hf_token
        )

        # 화자 분리 실행
        diarization = pipeline(audio_path, num_speakers=num_speakers)

        # 결과 정리
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append((turn.start, turn.end, speaker))

        print(f"✅ 화자 분리 완료: {len(segments)}개 세그먼트")

        # 화자별 통계
        speakers = {}
        for start, end, speaker in segments:
            duration = end - start
            if speaker not in speakers:
                speakers[speaker] = 0
            speakers[speaker] += duration

        print("\n화자별 시간:")
        for speaker, duration in sorted(speakers.items(), key=lambda x: x[1], reverse=True):
            print(f"   {speaker}: {duration:.1f}초 ({duration/60:.1f}분)")

        return segments

    def extract_speaker(
        self,
        audio_path: str,
        segments: List[Tuple[float, float, int]],
        target_speaker: str,
        output_path: str
    ):
        """
        특정 화자의 음성만 추출

        Args:
            audio_path: 원본 오디오
            segments: 화자 분리 결과
            target_speaker: 추출할 화자 ID
            output_path: 출력 파일
        """
        try:
            from pydub import AudioSegment
        except ImportError:
            print("❌ pydub가 설치되지 않았습니다.")
            print("설치: pip install pydub")
            return

        print(f"\n🎵 화자 {target_speaker} 추출 중...")

        # 오디오 로드
        audio = AudioSegment.from_wav(audio_path)

        # 해당 화자 구간만 추출
        target_segments = [
            (start, end) for start, end, speaker in segments
            if speaker == target_speaker
        ]

        if not target_segments:
            print(f"❌ 화자 {target_speaker}를 찾을 수 없습니다.")
            return

        # 구간 합치기
        result = AudioSegment.empty()
        for start, end in target_segments:
            segment = audio[start*1000:end*1000]  # ms 단위
            result += segment

        # 저장
        result.export(output_path, format="wav")

        print(f"✅ 추출 완료: {output_path}")
        print(f"   총 길이: {len(result)/1000:.1f}초")


# 간단한 사용 예제
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("화자 분리 도구")
    print("=" * 70)
    print()
    print("⚠️  주의사항:")
    print("1. 이 방법은 100% 정확하지 않습니다.")
    print("2. 퉁퉁이만 나오는 영상을 사용하는 것이 가장 좋습니다.")
    print("3. Hugging Face 토큰이 필요합니다.")
    print()

    # 예제
    audio_file = "data/raw/tongtong_20251019_191501.wav"

    if not os.path.exists(audio_file):
        print(f"❌ 파일 없음: {audio_file}")
    else:
        diarizer = SpeakerDiarization()

        # 화자 분리
        segments = diarizer.separate_speakers(
            audio_file,
            num_speakers=5  # 뽀로로, 퉁퉁이, 크롱, 루피, 에디
        )

        if segments:
            # 가장 많이 나오는 화자 (아마 퉁퉁이?)
            speakers = {}
            for start, end, speaker in segments:
                if speaker not in speakers:
                    speakers[speaker] = 0
                speakers[speaker] += (end - start)

            main_speaker = max(speakers.items(), key=lambda x: x[1])[0]

            print(f"\n💡 가장 많이 나오는 화자: {main_speaker}")
            print(f"   (퉁퉁이일 가능성 높음)")
            print()

            choice = input(f"이 화자를 추출하시겠습니까? (y/n): ")

            if choice.lower() == 'y':
                output_file = "data/processed/tongtong_only.wav"
                diarizer.extract_speaker(
                    audio_file,
                    segments,
                    main_speaker,
                    output_file
                )
