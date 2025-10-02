import os
import time
import json
import signal
import logging
import redis


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("emotion-worker")


REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
STREAM = os.environ.get('EMOTION_STREAM', 'emotion-events')
GROUP = os.environ.get('EMOTION_GROUP', 'emotion-workers')
CONSUMER = os.environ.get('EMOTION_CONSUMER', f"worker-{os.getpid()}")


_stop = False
_processed = 0
_failed = 0
_last_heartbeat = 0.0


def _handle_stop(signum, frame):
    global _stop
    _stop = True


def _ensure_group(r: redis.Redis) -> None:
    try:
        r.xgroup_create(STREAM, GROUP, id='0', mkstream=True)
        logger.info("Created stream group %s for %s", GROUP, STREAM)
    except redis.ResponseError as e:
        if 'BUSYGROUP' in str(e):
            # group already exists
            pass
        else:
            raise


def _process_message(r: redis.Redis, message_id: str, fields: dict) -> None:
    """Process single message.

    TODO: integrate DB write, Redis aggregation, websocket emit as needed.
    """
    # Example: log content and do light aggregation counter
    try:
        student_id = fields.get('student_id')
        emotion = fields.get('emotion')
        detected_at = fields.get('detected_at')
        logger.info(
            "event.process start id=%s student_id=%s emotion=%s detected_at=%s",
            message_id, student_id, emotion, detected_at
        )

        # Lightweight aggregation hash per day per student
        from datetime import datetime
        today = datetime.utcnow().date().isoformat()
        if student_id and emotion:
            key = f"agg:student:{student_id}:{today}"
            r.hincrby(key, emotion, 1)
            r.expire(key, 3 * 24 * 3600)

            # Compute and store daily risk score
            try:
                counts = r.hgetall(key)
                # convert values to int
                counts = {k: int(v) for k, v in counts.items()}
                from services.risk_scorer import compute_daily_risk_score
                risk = compute_daily_risk_score(counts)
                risk_key = f"risk:student:{student_id}:{today}"
                r.hset(risk_key, mapping={
                    'score': risk['score'],
                    'band': risk['band'],
                    'ratio_negative': risk['components']['ratio_negative'],
                    'ratio_neutral': risk['components']['ratio_neutral'],
                    'ratio_positive': risk['components']['ratio_positive'],
                    'total': risk['components']['total'],
                })
                r.expire(risk_key, 7 * 24 * 3600)
            except Exception:
                logger.exception("risk scoring error for %s", message_id)
        global _processed
        _processed += 1
        logger.info("event.process done id=%s total_processed=%s", message_id, _processed)
    except Exception:
        global _failed
        _failed += 1
        logger.exception("event.process error id=%s total_failed=%s", message_id, _failed)


def main() -> None:
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    _ensure_group(r)

    # 1) recover pending
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {STREAM: '0'}, count=50, block=100)
        if not resp:
            break
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_message(r, mid, fields)
                    r.xack(STREAM, GROUP, mid)
                except Exception:
                    logger.exception("pending.recover error id=%s", mid)

    # 2) consume new
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {STREAM: '>'}, count=50, block=5000)
        if not resp:
            # heartbeat
            import time as _t
            now = _t.time()
            global _last_heartbeat
            if now - _last_heartbeat > 15:
                _last_heartbeat = now
                try:
                    pending = r.xpending_range(STREAM, GROUP, '-', '+', 1)
                except Exception:
                    pending = []
                logger.info(
                    "heartbeat consumer=%s processed=%s failed=%s pending=%s",
                    CONSUMER, _processed, _failed, len(pending)
                )
            continue
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_message(r, mid, fields)
                    r.xack(STREAM, GROUP, mid)
                except Exception:
                    # Send to DLQ for later inspection
                    try:
                        r.xadd('emotion-dlq', {
                            'original_id': mid,
                            'fields': json.dumps(fields),
                            'error': 'processing_failed'
                        })
                    except Exception:
                        logger.exception("dlq append failed for %s", mid)
                    logger.exception("failed processing %s", mid)

    logger.info("Worker shutting down")


if __name__ == '__main__':
    main()

