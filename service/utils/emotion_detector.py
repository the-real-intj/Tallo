"""문장에서 감정을 자동으로 감지하는 유틸리티."""

import re


def detect_emotion_from_text(text: str) -> list[float]:
    """
    텍스트 내용을 분석해 적절한 감정 벡터를 반환합니다.
    
    Returns:
        [기쁨, 슬픔, 혐오, 공포, 놀람, 분노, 기타, 중립]
    """
    text_lower = text.lower()
    
    # 감정 키워드 매칭
    joy_keywords = ['웃', '기쁨', '행복', '좋', '신나', '즐거', '하하', '히히']
    sad_keywords = ['슬프', '울', '눈물', '아프', '힘들', '외로']
    fear_keywords = ['무서', '두렵', '겁', '살려', '도망', '위험']
    anger_keywords = ['화', '짜증', '싫어', '미워', '나쁜']
    surprise_keywords = ['놀라', '깜짝', '어머', '세상에', '!', '?']
    
    # 점수 계산
    joy_score = sum(1 for kw in joy_keywords if kw in text_lower)
    sad_score = sum(1 for kw in sad_keywords if kw in text_lower)
    fear_score = sum(1 for kw in fear_keywords if kw in text_lower)
    anger_score = sum(1 for kw in anger_keywords if kw in text_lower)
    surprise_score = sum(1 for kw in surprise_keywords if kw in text_lower)
    
    # 느낌표/물음표 카운트
    exclaim_count = text.count('!')
    question_count = text.count('?')
    
    if exclaim_count >= 2:
        surprise_score += 2
    if fear_score > 0 and exclaim_count > 0:
        fear_score += 1
    
    # 가장 높은 점수의 감정 선택
    total = joy_score + sad_score + fear_score + anger_score + surprise_score
    
    if total == 0:
        # 감정 키워드 없음 → 중립
        return [0.3077, 0.0256, 0.0256, 0.0256, 0.0256, 0.0256, 0.2564, 0.3077]
    
    # 정규화
    emotions = [
        joy_score / total if total > 0 else 0.0,      # 기쁨
        sad_score / total if total > 0 else 0.0,      # 슬픔
        0.05,                                          # 혐오 (기본 낮음)
        fear_score / total if total > 0 else 0.0,     # 공포
        surprise_score / total if total > 0 else 0.0, # 놀람
        anger_score / total if total > 0 else 0.0,    # 분노
        0.1,                                           # 기타
        0.1,                                           # 중립
    ]
    
    # 합계가 1.0에 가깝게 조정
    total_sum = sum(emotions)
    if total_sum > 0:
        emotions = [e / total_sum for e in emotions]
    
    return emotions


def get_emotion_preset(emotion_name: str) -> list[float]:
    """감정 이름으로 프리셋 벡터 반환."""
    presets = {
        "neutral": [0.3077, 0.0256, 0.0256, 0.0256, 0.0256, 0.0256, 0.2564, 0.3077],
        "joy": [0.8, 0.0, 0.0, 0.0, 0.1, 0.0, 0.05, 0.05],
        "sad": [0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.1, 0.1],
        "fear": [0.0, 0.1, 0.0, 0.7, 0.1, 0.0, 0.05, 0.05],
        "anger": [0.0, 0.0, 0.1, 0.0, 0.0, 0.7, 0.1, 0.1],
        "surprise": [0.1, 0.0, 0.0, 0.0, 0.7, 0.0, 0.1, 0.1],
    }
    return presets.get(emotion_name.lower(), presets["neutral"])

