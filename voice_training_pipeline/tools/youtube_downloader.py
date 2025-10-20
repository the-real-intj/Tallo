"""
유튜브에서 음성 데이터를 다운로드하는 모듈

주요 기능:
1. 유튜브 URL에서 오디오 추출
2. 여러 URL 배치 다운로드
3. 다운로드 진행상황 표시
4. 에러 처리 및 재시도
5. 메타데이터 저장
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import yt_dlp
from pydub import AudioSegment
from tqdm import tqdm
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubeAudioDownloader:
    """유튜브 오디오 다운로더 클래스"""

    def __init__(
        self,
        output_dir: str = "./data/raw",
        audio_format: str = "wav",
        audio_quality: str = "192",
        sample_rate: int = 22050
    ):
        """
        Args:
            output_dir: 다운로드 파일 저장 경로
            audio_format: 출력 오디오 포맷 (wav, mp3, flac)
            audio_quality: 오디오 품질 (kbps)
            sample_rate: 샘플링 레이트 (Hz)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.audio_format = audio_format
        self.audio_quality = audio_quality
        self.sample_rate = sample_rate

        # 메타데이터 저장 경로
        self.metadata_file = self.output_dir / "download_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """이전 다운로드 메타데이터 로드"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """메타데이터 저장"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def download_audio(
        self,
        youtube_url: str,
        character_name: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        유튜브 URL에서 오디오 다운로드

        Args:
            youtube_url: 유튜브 URL
            character_name: 캐릭터 이름 (파일명에 사용)
            max_retries: 최대 재시도 횟수

        Returns:
            다운로드된 파일 경로 (실패시 None)
        """
        logger.info(f"다운로드 시작: {youtube_url}")

        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{character_name}_{timestamp}"
        output_path = self.output_dir / f"{output_filename}.{self.audio_format}"

        # yt-dlp 옵션 설정
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.audio_format,
                'preferredquality': self.audio_quality,
            }],
            'outtmpl': str(self.output_dir / output_filename),
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
            # 진행상황 표시
            'progress_hooks': [self._progress_hook],
        }

        # 다운로드 시도 (재시도 로직)
        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # 비디오 정보 추출
                    info = ydl.extract_info(youtube_url, download=True)

                    # 메타데이터 저장
                    video_id = info.get('id', 'unknown')
                    self.metadata[video_id] = {
                        'url': youtube_url,
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                        'upload_date': info.get('upload_date', 'Unknown'),
                        'character_name': character_name,
                        'download_date': datetime.now().isoformat(),
                        'output_file': str(output_path),
                    }
                    self._save_metadata()

                    logger.info(f"✓ 다운로드 완료: {output_path}")

                    # 샘플레이트 변환
                    if self.sample_rate != 44100:  # 기본값이 아닌 경우
                        self._convert_sample_rate(output_path)

                    return str(output_path)

            except Exception as e:
                logger.error(f"다운로드 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    logger.error(f"✗ 최종 실패: {youtube_url}")
                    return None

    def _progress_hook(self, d):
        """다운로드 진행상황 표시"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"\r다운로드 중: {percent} | 속도: {speed} | 남은 시간: {eta}", end='')
        elif d['status'] == 'finished':
            print("\n다운로드 완료! 변환 중...")

    def _convert_sample_rate(self, audio_path: Path):
        """샘플레이트 변환"""
        try:
            logger.info(f"샘플레이트 변환 중: {self.sample_rate}Hz")
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_frame_rate(self.sample_rate)
            audio.export(audio_path, format=self.audio_format)
            logger.info("✓ 샘플레이트 변환 완료")
        except Exception as e:
            logger.error(f"샘플레이트 변환 실패: {e}")

    def download_batch(
        self,
        character_name: str,
        youtube_urls: List[str],
        delay_between_downloads: int = 2
    ) -> List[str]:
        """
        여러 URL 배치 다운로드

        Args:
            character_name: 캐릭터 이름
            youtube_urls: 유튜브 URL 리스트
            delay_between_downloads: 다운로드 간 대기 시간 (초)

        Returns:
            다운로드 성공한 파일 경로 리스트
        """
        logger.info(f"배치 다운로드 시작: {len(youtube_urls)}개 URL")

        downloaded_files = []

        for idx, url in enumerate(tqdm(youtube_urls, desc="배치 다운로드")):
            logger.info(f"\n[{idx + 1}/{len(youtube_urls)}] 처리 중...")

            file_path = self.download_audio(url, character_name)

            if file_path:
                downloaded_files.append(file_path)

            # 마지막 항목이 아니면 대기
            if idx < len(youtube_urls) - 1:
                time.sleep(delay_between_downloads)

        logger.info(f"\n배치 다운로드 완료: {len(downloaded_files)}/{len(youtube_urls)} 성공")
        return downloaded_files

    def get_audio_info(self, audio_path: str) -> Dict:
        """오디오 파일 정보 추출"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return {
                'duration': len(audio) / 1000.0,  # 초 단위
                'channels': audio.channels,
                'sample_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'frame_count': audio.frame_count(),
                'file_size': os.path.getsize(audio_path),
            }
        except Exception as e:
            logger.error(f"오디오 정보 추출 실패: {e}")
            return {}

    def validate_audio(self, audio_path: str, min_duration: float = 5.0) -> bool:
        """
        오디오 파일 유효성 검사

        Args:
            audio_path: 오디오 파일 경로
            min_duration: 최소 길이 (초)

        Returns:
            유효 여부
        """
        info = self.get_audio_info(audio_path)

        if not info:
            return False

        duration = info.get('duration', 0)

        if duration < min_duration:
            logger.warning(f"오디오가 너무 짧음: {duration:.2f}초 (최소: {min_duration}초)")
            return False

        logger.info(f"✓ 오디오 유효: {duration:.2f}초")
        return True


def main():
    """테스트 및 예제"""

    # 다운로더 초기화
    downloader = YouTubeAudioDownloader(
        output_dir="./data/raw",
        audio_format="wav",
        audio_quality="192",
        sample_rate=22050
    )

    # 단일 다운로드 예제
    # url = "https://www.youtube.com/watch?v=EXAMPLE"
    # file_path = downloader.download_audio(url, "pororo")

    # 배치 다운로드 예제
    urls = [
        # "https://www.youtube.com/watch?v=EXAMPLE1",
        # "https://www.youtube.com/watch?v=EXAMPLE2",
    ]

    # downloaded_files = downloader.download_batch("pororo", urls)

    # print(f"\n다운로드 완료: {len(downloaded_files)}개 파일")
    # for file in downloaded_files:
    #     print(f"  - {file}")

    print("다운로더 준비 완료!")
    print("실제 URL을 추가하여 사용하세요.")


if __name__ == "__main__":
    main()
