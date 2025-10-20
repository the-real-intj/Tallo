# -*- coding: utf-8 -*-
"""
특정 화자 음성 추출
기준 샘플(퉁퉁이 목소리)을 사용해서 섞인 파일에서 같은 목소리만 추출
"""

import os
import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_similar_voice(
    mixed_audio_path,
    reference_audio_path,
    output_path,
    similarity_threshold=0.6
):
    """
    기준 샘플과 비슷한 목소리만 추출

    Args:
        mixed_audio_path: 여러 목소리 섞인 파일
        reference_audio_path: 기준 목소리 샘플 (퉁퉁이)
        output_path: 출력 파일
        similarity_threshold: 유사도 기준 (0-1)
    """
    print("\n" + "=" * 70)
    print("  특정 화자 음성 추출")
    print("=" * 70)
    print()

    print(f"📂 섞인 파일: {mixed_audio_path}")
    print(f"🎯 기준 샘플: {reference_audio_path}")
    print(f"💾 출력 파일: {output_path}")
    print()

    # 필요한 라이브러리 확인
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
        from pydub import AudioSegment
        import librosa
    except ImportError as e:
        print(f"❌ 필요한 패키지가 없습니다: {e}")
        print()
        print("설치 방법:")
        print("  pip install resemblyzer pydub librosa")
        return False

    print("⏳ 처리 중... (시간이 걸릴 수 있습니다)")
    print()

    try:
        # 1. 음성 인코더 초기화
        print("1️⃣  음성 인코더 로딩...")
        encoder = VoiceEncoder()

        # 2. 기준 샘플 임베딩 생성
        print("2️⃣  기준 샘플 분석 중...")

        # 기준 오디오 로드
        ref_wav = preprocess_wav(reference_audio_path)
        ref_embedding = encoder.embed_utterance(ref_wav)

        print(f"   ✅ 기준 임베딩 생성 완료")

        # 3. 섞인 파일을 작은 구간으로 나누기
        print("3️⃣  섞인 파일 분석 중...")

        # 오디오 로드
        audio = AudioSegment.from_wav(mixed_audio_path)

        # 5초씩 분할
        segment_length = 5000  # ms
        segments = []
        similarities = []

        for i in range(0, len(audio), segment_length):
            segment = audio[i:i+segment_length]

            # 너무 짧은 구간 제외
            if len(segment) < 2000:
                continue

            # 임시 파일로 저장
            temp_path = f"temp_segment_{i}.wav"
            segment.export(temp_path, format="wav")

            try:
                # 임베딩 생성
                seg_wav = preprocess_wav(temp_path)
                seg_embedding = encoder.embed_utterance(seg_wav)

                # 유사도 계산 (코사인 유사도)
                similarity = np.dot(ref_embedding, seg_embedding)

                segments.append(segment)
                similarities.append(similarity)

            except Exception as e:
                # 문제 있는 세그먼트는 건너뛰기
                pass
            finally:
                # 임시 파일 삭제
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        print(f"   ✅ {len(segments)}개 구간 분석 완료")
        print()

        # 4. 유사도 높은 구간만 선택
        print("4️⃣  유사 음성 추출 중...")
        print(f"   유사도 기준: {similarity_threshold} 이상")

        selected_segments = []
        for i, (segment, similarity) in enumerate(zip(segments, similarities)):
            if similarity >= similarity_threshold:
                selected_segments.append(segment)
                print(f"   ✅ 구간 {i}: 유사도 {similarity:.2f}")

        print()
        print(f"   선택된 구간: {len(selected_segments)}/{len(segments)}개")

        if not selected_segments:
            print()
            print("⚠️  유사한 음성을 찾지 못했습니다.")
            print()
            print("💡 해결 방법:")
            print("   1. similarity_threshold를 낮추기 (0.5 시도)")
            print("   2. 기준 샘플 확인 (퉁퉁이 목소리 맞는지)")
            print("   3. 섞인 파일에 퉁퉁이 있는지 확인")
            return False

        # 5. 선택된 구간 합치기
        print("5️⃣  추출된 음성 합치는 중...")

        result = AudioSegment.empty()
        for segment in selected_segments:
            result += segment

        # 6. 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result.export(str(output_path), format="wav")

        # 결과 정보
        duration_sec = len(result) / 1000
        size_mb = output_path.stat().st_size / 1024 / 1024

        print()
        print("=" * 70)
        print("✅ 완료!")
        print("=" * 70)
        print()
        print(f"📁 출력: {output_path}")
        print(f"⏱️  길이: {duration_sec // 60:.0f}분 {duration_sec % 60:.0f}초")
        print(f"💾 크기: {size_mb:.1f}MB")
        print()
        print("🎧 듣어보기:")
        print(f"   start {output_path}")
        print()

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("\n🎯 특정 화자 음성 추출 도구")
    print()

    # 기본 경로 설정
    mixed_file = "data/raw/tongtong_20251019_191406.wav"
    reference_file = "data/raw/tongtong_custom_tongtong_voice_01.wav"
    output_file = "data/processed/tongtong_only_extracted.wav"

    # 파일 존재 확인
    if not Path(mixed_file).exists():
        print(f"❌ 섞인 파일을 찾을 수 없습니다: {mixed_file}")
        return

    if not Path(reference_file).exists():
        print(f"❌ 기준 샘플을 찾을 수 없습니다: {reference_file}")
        return

    print("📋 설정:")
    print(f"   섞인 파일: {mixed_file}")
    print(f"   기준 샘플: {reference_file}")
    print(f"   출력 파일: {output_file}")
    print()

    # 유사도 기준 선택
    print("유사도 기준 선택:")
    print("   1. 엄격 (0.7) - 확실한 것만")
    print("   2. 보통 (0.6) - 권장")
    print("   3. 관대 (0.5) - 많이 포함")
    print()

    choice = input("선택 (1-3, Enter=2): ").strip()

    if choice == "1":
        threshold = 0.7
    elif choice == "3":
        threshold = 0.5
    else:
        threshold = 0.6

    print()

    # 실행
    success = extract_similar_voice(
        mixed_audio_path=mixed_file,
        reference_audio_path=reference_file,
        output_path=output_file,
        similarity_threshold=threshold
    )

    if success:
        print("🎉 성공!")
        print()
        print("다음 단계:")
        print("   1. 추출된 파일 듣어보기:")
        print(f"      start {output_file}")
        print()
        print("   2. 만족스러우면 학습에 사용:")
        print("      - data/raw/tongtong_only_extracted.wav 복사")
        print("      - python scripts/train_single_audio.py 실행")
    else:
        print("❌ 실패")
        print()
        print("💡 시도해볼 것:")
        print("   1. 다른 유사도 기준으로 재시도")
        print("   2. 기준 샘플 확인 (퉁퉁이 목소리 맞는지)")
        print("   3. 수동으로 편집 (Audacity 사용)")


if __name__ == "__main__":
    main()
