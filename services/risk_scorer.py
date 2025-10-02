from typing import Dict, Any


NEGATIVE_EMOTIONS = {"sad", "angry", "fear", "disgust"}
NEUTRAL_EMOTIONS = {"neutral"}


def compute_daily_risk_score(emotion_counts: Dict[str, int]) -> Dict[str, Any]:
    """Compute a simple interpretable daily risk score from emotion counts.

    Returns a dict with score [0..100], band (low|medium|high), and components.
    """
    total = max(1, sum(int(v) for v in emotion_counts.values()))
    negative = sum(int(emotion_counts.get(e, 0)) for e in NEGATIVE_EMOTIONS)
    neutral = sum(int(emotion_counts.get(e, 0)) for e in NEUTRAL_EMOTIONS)
    positive = total - negative - neutral

    ratio_negative = negative / total
    ratio_neutral = neutral / total
    ratio_positive = positive / total

    # Simple weighted score (tunable):
    # negative heavily increases, neutral slight, positive decreases
    raw = (ratio_negative * 0.75 + ratio_neutral * 0.25 - ratio_positive * 0.5)
    raw = max(0.0, min(1.0, raw))
    score = round(raw * 100, 1)

    if score >= 70:
        band = 'high'
    elif score >= 40:
        band = 'medium'
    else:
        band = 'low'

    return {
        'score': score,
        'band': band,
        'components': {
            'ratio_negative': round(ratio_negative, 3),
            'ratio_neutral': round(ratio_neutral, 3),
            'ratio_positive': round(ratio_positive, 3),
            'total': total,
        }
    }

