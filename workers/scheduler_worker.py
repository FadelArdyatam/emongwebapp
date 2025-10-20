#!/usr/bin/env python3
"""
Worker untuk scheduled tasks (tugas terjadwal)
"""

import os
import time
import json
import signal
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("scheduler-worker")

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
SCHEDULER_STREAM = 'scheduler-events'
GROUP = 'scheduler-workers'
CONSUMER = f"worker-{os.getpid()}"

_stop = False
_processed = 0
_failed = 0

def _handle_stop(signum, frame):
    global _stop
    _stop = True

def _ensure_group(r: redis.Redis) -> None:
    try:
        r.xgroup_create(SCHEDULER_STREAM, GROUP, id='0', mkstream=True)
        logger.info("Created scheduler stream group %s", GROUP)
    except redis.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise

def cleanup_old_data() -> Dict[str, Any]:
    """Hapus data lama dari database"""
    try:
        # Simulasi cleanup data
        cleanup_stats = {
            'deleted_old_sessions': 15,
            'deleted_old_logs': 2500,
            'archived_reports': 8,
            'cleaned_temp_files': 45,
            'cleanup_time': datetime.utcnow().isoformat()
        }
        
        logger.info("Data cleanup completed: %s", cleanup_stats)
        return cleanup_stats
        
    except Exception as e:
        logger.error("Data cleanup failed: %s", str(e))
        return {'status': 'failed', 'error': str(e)}

def generate_daily_reports() -> Dict[str, Any]:
    """Generate laporan harian otomatis"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Simulasi generate laporan harian
        report_stats = {
            'date': yesterday,
            'emotion_summary': {
                'total_detections': 1200,
                'happy_percentage': 25.5,
                'sad_percentage': 35.2,
                'neutral_percentage': 20.1,
                'other_percentage': 19.2
            },
            'student_activity': {
                'active_students': 18,
                'total_sessions': 32,
                'avg_session_duration': '25 minutes'
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info("Daily reports generated for %s", yesterday)
        return report_stats
        
    except Exception as e:
        logger.error("Daily report generation failed: %s", str(e))
        return {'status': 'failed', 'error': str(e)}

def send_weekly_summaries() -> Dict[str, Any]:
    """Kirim ringkasan mingguan ke parent"""
    try:
        # Simulasi kirim ringkasan mingguan
        summary_stats = {
            'week_start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'week_end': datetime.now().strftime('%Y-%m-%d'),
            'parents_notified': 25,
            'emails_sent': 25,
            'push_notifications': 18,
            'sent_at': datetime.utcnow().isoformat()
        }
        
        logger.info("Weekly summaries sent: %s", summary_stats)
        return summary_stats
        
    except Exception as e:
        logger.error("Weekly summary sending failed: %s", str(e))
        return {'status': 'failed', 'error': str(e)}

def backup_database() -> Dict[str, Any]:
    """Backup database"""
    try:
        # Simulasi backup database
        backup_stats = {
            'backup_file': f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
            'file_size': '45.2MB',
            'tables_backed_up': 12,
            'backup_duration': '2.5 minutes',
            'backup_time': datetime.utcnow().isoformat()
        }
        
        logger.info("Database backup completed: %s", backup_stats)
        return backup_stats
        
    except Exception as e:
        logger.error("Database backup failed: %s", str(e))
        return {'status': 'failed', 'error': str(e)}

def _process_scheduled_task(r: redis.Redis, message_id: str, fields: dict) -> None:
    """Process scheduled task"""
    global _processed, _failed
    
    try:
        task_type = fields.get('task_type')
        task_data = json.loads(fields.get('task_data', '{}'))
        
        logger.info("Processing scheduled task %s: %s", message_id, task_type)
        
        result = None
        
        if task_type == 'cleanup_old_data':
            result = cleanup_old_data()
        elif task_type == 'generate_daily_reports':
            result = generate_daily_reports()
        elif task_type == 'send_weekly_summaries':
            result = send_weekly_summaries()
        elif task_type == 'backup_database':
            result = backup_database()
        
        if result and result.get('status') != 'failed':
            # Simpan hasil ke Redis
            result_key = f"scheduled_task:result:{message_id}"
            r.hset(result_key, mapping=result)
            r.expire(result_key, 7 * 24 * 3600)  # 7 hari
            
            _processed += 1
            logger.info("Scheduled task completed: %s", message_id)
        else:
            _failed += 1
            logger.error("Scheduled task failed: %s", message_id)
            
    except Exception as e:
        _failed += 1
        logger.exception("Error processing scheduled task %s: %s", message_id, str(e))

def main() -> None:
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)
    
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    _ensure_group(r)
    
    logger.info("Scheduler worker started")
    
    # Process pending tasks
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {SCHEDULER_STREAM: '0'}, count=50, block=100)
        if not resp:
            break
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_scheduled_task(r, mid, fields)
                    r.xack(SCHEDULER_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing pending task %s", mid)
    
    # Process new tasks
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {SCHEDULER_STREAM: '>'}, count=50, block=5000)
        if not resp:
            continue
            
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_scheduled_task(r, mid, fields)
                    r.xack(SCHEDULER_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing scheduled task %s", mid)
    
    logger.info("Scheduler worker shutting down")

if __name__ == '__main__':
    main()
