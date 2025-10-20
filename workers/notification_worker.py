#!/usr/bin/env python3
"""
Worker untuk mengirim notifikasi email dan push notification
"""

import os
import time
import json
import signal
import logging
import redis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("notification-worker")

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
NOTIFICATION_STREAM = 'notification-events'
GROUP = 'notification-workers'
CONSUMER = f"worker-{os.getpid()}"

_stop = False
_processed = 0
_failed = 0

def _handle_stop(signum, frame):
    global _stop
    _stop = True

def _ensure_group(r: redis.Redis) -> None:
    try:
        r.xgroup_create(NOTIFICATION_STREAM, GROUP, id='0', mkstream=True)
        logger.info("Created notification stream group %s", GROUP)
    except redis.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise

def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """Kirim email notification"""
    try:
        # Email configuration (sesuaikan dengan SMTP server Anda)
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        if not smtp_username or not smtp_password:
            logger.warning("SMTP credentials not configured, skipping email")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
        
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, str(e))
        return False

def send_push_notification(user_id: str, title: str, message: str, data: dict = None) -> bool:
    """Kirim push notification (contoh menggunakan Firebase)"""
    try:
        # Implementasi push notification sesuai platform yang digunakan
        # Contoh: Firebase Cloud Messaging, OneSignal, dll
        
        notification_data = {
            'user_id': user_id,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Simpan ke Redis untuk diproses oleh frontend
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        r.lpush(f"notifications:{user_id}", json.dumps(notification_data))
        r.expire(f"notifications:{user_id}", 7 * 24 * 3600)  # 7 hari
        
        logger.info("Push notification queued for user %s: %s", user_id, title)
        return True
        
    except Exception as e:
        logger.error("Failed to send push notification to %s: %s", user_id, str(e))
        return False

def _process_notification(r: redis.Redis, message_id: str, fields: dict) -> None:
    """Process notification message"""
    global _processed, _failed
    
    try:
        notification_type = fields.get('type', 'email')
        recipient = fields.get('recipient')
        subject = fields.get('subject', 'EMONG Notification')
        message = fields.get('message', '')
        data = json.loads(fields.get('data', '{}'))
        
        logger.info("Processing notification %s: %s -> %s", 
                   message_id, notification_type, recipient)
        
        success = False
        
        if notification_type == 'email':
            success = send_email_notification(recipient, subject, message)
        elif notification_type == 'push':
            success = send_push_notification(recipient, subject, message, data)
        elif notification_type == 'both':
            email_success = send_email_notification(recipient, subject, message)
            push_success = send_push_notification(recipient, subject, message, data)
            success = email_success or push_success
        
        if success:
            _processed += 1
            logger.info("Notification processed successfully: %s", message_id)
        else:
            _failed += 1
            logger.error("Notification failed: %s", message_id)
            
    except Exception as e:
        _failed += 1
        logger.exception("Error processing notification %s: %s", message_id, str(e))

def main() -> None:
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)
    
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    _ensure_group(r)
    
    logger.info("Notification worker started")
    
    # Process pending notifications
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {NOTIFICATION_STREAM: '0'}, count=50, block=100)
        if not resp:
            break
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_notification(r, mid, fields)
                    r.xack(NOTIFICATION_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing pending notification %s", mid)
    
    # Process new notifications
    while not _stop:
        resp = r.xreadgroup(GROUP, CONSUMER, {NOTIFICATION_STREAM: '>'}, count=50, block=5000)
        if not resp:
            continue
            
        for _stream, messages in resp:
            for mid, fields in messages:
                try:
                    _process_notification(r, mid, fields)
                    r.xack(NOTIFICATION_STREAM, GROUP, mid)
                except Exception:
                    logger.exception("Error processing notification %s", mid)
    
    logger.info("Notification worker shutting down")

if __name__ == '__main__':
    main()
