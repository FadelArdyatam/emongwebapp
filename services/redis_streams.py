import os
import json
from typing import Any, Dict, Optional


STREAM_NAME = os.environ.get('EMOTION_STREAM', 'emotion-events')
STREAM_MAXLEN = int(os.environ.get('EMOTION_MAXLEN', '50000'))


def publish_emotion_event(
    redis_client: Any,
    *,
    student_id: int,
    emotion: str,
    confidence: Optional[float],
    detected_at_iso: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Publish an emotion event into Redis Streams.

    This function is safe to call even if redis_client is None.
    """
    if not redis_client:
        return
    if not student_id or not emotion:
        return

    fields: Dict[str, str] = {
        'student_id': str(student_id),
        'emotion': str(emotion),
        'confidence': '' if confidence is None else str(confidence),
        'detected_at': detected_at_iso,
        'extra': json.dumps(extra or {}),
    }

    try:
        redis_client.xadd(
            STREAM_NAME,
            fields,
            maxlen=STREAM_MAXLEN,
            approximate=True,
        )
    except Exception:
        # Non-fatal: do not break request flow
        pass

