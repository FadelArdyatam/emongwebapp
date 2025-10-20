#!/usr/bin/env python3
"""
Worker untuk generate laporan PDF/Excel
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
logger = logging.getLogger("report-worker")

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
REPORT_STREAM = 'report-events'
GROUP = 'report-workers'
CONSUMER = f"worker-{os.getpid()}"

_stop = False
_processed = 0
_failed = 0

def _handle_stop(signum, frame):
    global _stop
    _stop = True

def _ensure_group(r: redis.Redis) -> None:
    try:
        r.xgroup_create(REPORT_STREAM, GROUP, id='0', mkstream=True)
        logger.info("Created report stream group %s", GROUP)
    except redis.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise

def generate_emotion_report(student_id: str, start_date: str, end_date: str, 
                          report_type: str = 'pdf') -> Dict[str, Any]:
    """Generate laporan emosi untuk siswa"""
    try:
        # Simulasi generate report (implementasi sesuai kebutuhan)
        report_data = {
            'student_id': student_id,
            'start_date': start_date,
            'end_date': end_date,
            'report_type': report_type,
            'generated_at': datetime.utcnow().isoformat(),
            'status': 'completed'
        }
        
        # Simulasi data laporan
        if report_type == 'pdf':
            report_data.update({
                'file_path': f"/reports/emotion_report_{student_id}_{start_date}_{end_date}.pdf",
                'file_size': '2.5MB',
                'pages': 5
            })
        elif report_type == 'excel':
            report_data.update({
                'file_path': f"/reports/emotion_report_{student_id}_{start_date}_{end_date}.xlsx",
                'file_size': '1.2MB',
                'sheets': 3
            })
        
        logger.info("Report generated: %s", report_data['file_path'])
        return report_data
        
    except Exception as e:
        logger.error("Failed to generate report: %s", str(e))
        return {'status': 'failed', 'error': str(e)}

def generate_daily_summary_report(date: str) -> Dict[str, Any]:
    """Generate laporan ringkasan harian"""
    try:
        # Simulasi data ringkasan harian
        summary_data = {
            'date': date,
            'total_students': 25,
            'total_sessions': 45,
            'total_detections': 1200,
            'emotion_distribution': {
                'happy': 300,
                'sad': 400,
                'neutral': 200,
                'angry': 150,
                'fear': 100,
                'surprise': 50
            },
            'high_risk_students': 3,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        logger.info("Daily summary generated for %s", date)
        return summary_data
        
    except Exception as e:
        logger.error("Failed to generate daily summary: %s", str(e))
        return {'status': 'failed', 'error': str(e)}

def _process_report(r: redis.Redis, message_id: str, fields: dict) -> None:
    """Process report generation request"""
    global _processed, _failed
    
    try:
        report_type = fields.get('type', 'emotion')
        student_id = fields.get('student_id')
        start_date = fields.get('start_date')
        end_date = fields.get('end_date')
        format_type = fields.get('format', 'pdf')
        
        logger.info("Processing report %s: %s for student %s", 
                   message_id, report_type, student_id)
        
        result = None
        
        if report_type == 'emotion' and student_id:
            result = generate_emotion_report(student_id, start_date, end_date, format_type)
        elif report_type == 'daily_summary':
            result = generate_daily_summary_report(start_date)
        
        if result and result.get('status') == 'completed':
            # Simpan hasil ke Redis
            result_key = f"report:result:{message_id}"
            r.hset(result_key, mapping=result)
            r.expire(result_key, 24 * 3600)  # 24 jam
            
            # Notify completion
            r.xadd('notification-events', {
                'type': 'push',
                'recipient': fields.get('user_id', ''),
                'subject': 'Laporan Siap',
                'message': f'Laporan {report_type} telah selesai dibuat',
                'data': json.dumps({'report_id': message_id, 'file_path': result.get('file_path')})
            })
            
            _processed += 1
            logger.info("Report completed: %s", message_id)
        else:
            _failed += 1
            logger.error("Report failed: %s", message_id)
            
    except Exception as e:
        _failed += 1
        logger.exception("Error processing report %s: %s", message_id, str(e))

def main() -> None:
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)
    
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    _ensure_group(r)
    
    logger.info("Report worker started")
    
    # Process pending reports
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {REPORT_STREAM: '0'}, count=50, block=100)
        if not resp:
            break
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_report(r, mid, fields)
                    r.xack(REPORT_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing pending report %s", mid)
    
    # Process new reports
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {REPORT_STREAM: '>'}, count=50, block=5000)
        if not resp:
            continue
            
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_report(r, mid, fields)
                    r.xack(REPORT_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing report %s", mid)
    
    logger.info("Report worker shutting down")

if __name__ == '__main__':
    main()
