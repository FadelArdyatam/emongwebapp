#!/usr/bin/env python3
"""
Service untuk mengirim jobs ke berbagai worker
"""

import redis
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class WorkerService:
    def __init__(self):
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
    
    def send_notification(self, notification_type: str, recipient: str, 
                         subject: str, message: str, data: Dict = None) -> str:
        """Kirim notifikasi (email/push)"""
        try:
            job_data = {
                'type': notification_type,  # 'email', 'push', 'both'
                'recipient': recipient,
                'subject': subject,
                'message': message,
                'data': json.dumps(data or {}),
                'created_at': datetime.utcnow().isoformat()
            }
            
            message_id = self.redis_client.xadd('notification-events', job_data)
            return message_id
            
        except Exception as e:
            print(f"Error sending notification: {e}")
            return None
    
    def request_report(self, report_type: str, student_id: str = None, 
                      start_date: str = None, end_date: str = None, 
                      format_type: str = 'pdf', user_id: str = None) -> str:
        """Request generate laporan"""
        try:
            job_data = {
                'type': report_type,  # 'emotion', 'daily_summary'
                'student_id': student_id or '',
                'start_date': start_date or datetime.now().strftime('%Y-%m-%d'),
                'end_date': end_date or datetime.now().strftime('%Y-%m-%d'),
                'format': format_type,  # 'pdf', 'excel'
                'user_id': user_id or '',
                'created_at': datetime.utcnow().isoformat()
            }
            
            message_id = self.redis_client.xadd('report-events', job_data)
            return message_id
            
        except Exception as e:
            print(f"Error requesting report: {e}")
            return None
    
    def schedule_task(self, task_type: str, task_data: Dict = None, 
                     delay_seconds: int = 0) -> str:
        """Schedule task untuk dijalankan"""
        try:
            job_data = {
                'task_type': task_type,  # 'cleanup_old_data', 'generate_daily_reports', dll
                'task_data': json.dumps(task_data or {}),
                'delay_seconds': delay_seconds,
                'created_at': datetime.utcnow().isoformat()
            }
            
            message_id = self.redis_client.xadd('scheduler-events', job_data)
            return message_id
            
        except Exception as e:
            print(f"Error scheduling task: {e}")
            return None
    
    def get_job_status(self, stream_name: str, message_id: str) -> Optional[Dict]:
        """Cek status job"""
        try:
            # Cek di result key
            result_key = f"{stream_name.split('-')[0]}:result:{message_id}"
            result = self.redis_client.hgetall(result_key)
            
            if result:
                return result
            
            # Cek di pending messages
            stream_info = self.redis_client.xinfo_stream(stream_name)
            if stream_info:
                # Cek apakah message masih pending
                return {'status': 'pending'}
            
            return {'status': 'not_found'}
            
        except Exception as e:
            print(f"Error checking job status: {e}")
            return None

# Helper functions untuk kemudahan penggunaan
def send_email_to_parent(parent_email: str, student_name: str, 
                        emotion_summary: Dict) -> str:
    """Kirim email ke parent tentang emosi anak"""
    worker_service = WorkerService()
    
    subject = f"Laporan Emosi {student_name} - {datetime.now().strftime('%d/%m/%Y')}"
    message = f"""
    <h2>Laporan Emosi {student_name}</h2>
    <p>Berikut adalah ringkasan emosi anak Anda hari ini:</p>
    <ul>
        <li>Happy: {emotion_summary.get('happy', 0)} deteksi</li>
        <li>Sad: {emotion_summary.get('sad', 0)} deteksi</li>
        <li>Neutral: {emotion_summary.get('neutral', 0)} deteksi</li>
        <li>Angry: {emotion_summary.get('angry', 0)} deteksi</li>
    </ul>
    <p>Silakan login ke dashboard untuk melihat detail lebih lengkap.</p>
    """
    
    return worker_service.send_notification('email', parent_email, subject, message)

def send_push_notification_to_parent(parent_id: str, title: str, 
                                   message: str, data: Dict = None) -> str:
    """Kirim push notification ke parent"""
    worker_service = WorkerService()
    return worker_service.send_notification('push', parent_id, title, message, data)

def generate_student_emotion_report(student_id: str, start_date: str, 
                                   end_date: str, user_id: str) -> str:
    """Generate laporan emosi siswa"""
    worker_service = WorkerService()
    return worker_service.request_report('emotion', student_id, start_date, end_date, 'pdf', user_id)

def schedule_daily_cleanup() -> str:
    """Schedule cleanup data harian"""
    worker_service = WorkerService()
    return worker_service.schedule_task('cleanup_old_data')

def schedule_weekly_reports() -> str:
    """Schedule laporan mingguan"""
    worker_service = WorkerService()
    return worker_service.schedule_task('send_weekly_summaries')

# Contoh penggunaan
if __name__ == '__main__':
    # Test send notification
    print("Testing notification worker...")
    message_id = send_email_to_parent(
        'parent@example.com', 
        'Andi Pratama', 
        {'happy': 15, 'sad': 3, 'neutral': 8, 'angry': 1}
    )
    print(f"Notification sent: {message_id}")
    
    # Test request report
    print("Testing report worker...")
    report_id = generate_student_emotion_report(
        '1', 
        '2025-10-01', 
        '2025-10-14', 
        'parent123'
    )
    print(f"Report requested: {report_id}")
    
    # Test schedule task
    print("Testing scheduler worker...")
    task_id = schedule_daily_cleanup()
    print(f"Task scheduled: {task_id}")
