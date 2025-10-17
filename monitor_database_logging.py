#!/usr/bin/env python3
"""
Script untuk memonitor logging database real-time
"""

import sys
import os
import time
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def monitor_database_logging():
    """Monitor logging database real-time"""
    try:
        from app import app, db
        from models import EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("🔍 Monitoring Database Logging...")
            print("=" * 60)
            
            # Ambil data baseline
            initial_session_count = EmotionSession.query.count()
            initial_log_count = EmotionLog.query.count()
            
            print(f"📊 Baseline Data:")
            print(f"   Sessions: {initial_session_count}")
            print(f"   Emotion logs: {initial_log_count}")
            
            # Monitor selama 30 detik
            print(f"\n⏱️  Monitoring for 30 seconds...")
            print("   (Start emotion detection to see real-time logging)")
            
            start_time = time.time()
            last_session_count = initial_session_count
            last_log_count = initial_log_count
            
            while time.time() - start_time < 30:
                current_session_count = EmotionSession.query.count()
                current_log_count = EmotionLog.query.count()
                
                # Cek perubahan
                if current_session_count > last_session_count:
                    new_sessions = current_session_count - last_session_count
                    print(f"✅ {new_sessions} new session(s) created!")
                    
                    # Tampilkan detail sesi baru
                    recent_sessions = EmotionSession.query.order_by(
                        EmotionSession.created_at.desc()
                    ).limit(new_sessions).all()
                    
                    for session in recent_sessions:
                        student_name = "Unknown"
                        if session.student_id:
                            student = Student.query.get(session.student_id)
                            if student:
                                student_name = student.full_name
                        
                        print(f"   - Session {session.id}: {session.session_name} (Student: {student_name})")
                
                if current_log_count > last_log_count:
                    new_logs = current_log_count - last_log_count
                    print(f"📝 {new_logs} new emotion log(s) recorded!")
                    
                    # Tampilkan detail log baru
                    recent_logs = EmotionLog.query.order_by(
                        EmotionLog.detected_at.desc()
                    ).limit(new_logs).all()
                    
                    for log in recent_logs:
                        student_name = "Unknown"
                        if log.student_id:
                            student = Student.query.get(log.student_id)
                            if student:
                                student_name = student.full_name
                        
                        print(f"   - {log.emotion} ({log.confidence_score:.3f}) - {student_name}")
                
                last_session_count = current_session_count
                last_log_count = current_log_count
                
                time.sleep(1)  # Check every second
            
            # Final summary
            final_session_count = EmotionSession.query.count()
            final_log_count = EmotionLog.query.count()
            
            print(f"\n📈 Final Results:")
            print(f"   Sessions: {initial_session_count} → {final_session_count} (+{final_session_count - initial_session_count})")
            print(f"   Emotion logs: {initial_log_count} → {final_log_count} (+{final_log_count - initial_log_count})")
            
            # Cek distribusi emosi hari ini
            today = date.today()
            today_logs = EmotionLog.query.filter(
                db.func.date(EmotionLog.detected_at) == today
            ).all()
            
            if today_logs:
                from collections import Counter
                emotion_counts = Counter(log.emotion for log in today_logs)
                
                print(f"\n😊 Today's Emotion Distribution:")
                for emotion, count in emotion_counts.most_common():
                    percentage = (count / len(today_logs)) * 100
                    print(f"   - {emotion}: {count} ({percentage:.1f}%)")
            
            return True
            
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        return False

def check_recent_activity():
    """Check recent activity in database"""
    try:
        from app import app, db
        from models import EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("🔍 Checking Recent Activity...")
            print("=" * 60)
            
            # Cek aktivitas 1 jam terakhir
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            recent_sessions = EmotionSession.query.filter(
                EmotionSession.created_at >= one_hour_ago
            ).all()
            
            recent_logs = EmotionLog.query.filter(
                EmotionLog.detected_at >= one_hour_ago
            ).all()
            
            print(f"📊 Last 1 Hour Activity:")
            print(f"   Sessions created: {len(recent_sessions)}")
            print(f"   Emotion logs: {len(recent_logs)}")
            
            if recent_sessions:
                print(f"\n📅 Recent Sessions:")
                for session in recent_sessions:
                    student_name = "Unknown"
                    if session.student_id:
                        student = Student.query.get(session.student_id)
                        if student:
                            student_name = student.full_name
                    
                    print(f"   - {session.session_name} (Student: {student_name}) at {session.created_at}")
            
            if recent_logs:
                print(f"\n😊 Recent Emotion Logs:")
                # Group by student
                student_logs = {}
                for log in recent_logs:
                    if log.student_id not in student_logs:
                        student_logs[log.student_id] = []
                    student_logs[log.student_id].append(log)
                
                for student_id, logs in student_logs.items():
                    student_name = "Unknown"
                    if student_id:
                        student = Student.query.get(student_id)
                        if student:
                            student_name = student.full_name
                    
                    print(f"   - {student_name}: {len(logs)} logs")
                    for log in logs[-3:]:  # Show last 3 logs
                        print(f"     * {log.emotion} ({log.confidence_score:.3f}) at {log.detected_at}")
            
            return True
            
    except Exception as e:
        print(f"❌ Activity check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Logging Monitor")
    print("=" * 60)
    
    # Check recent activity first
    check_recent_activity()
    
    print("\n" + "=" * 60)
    
    # Start monitoring
    success = monitor_database_logging()
    
    if success:
        print("\n✅ Database logging is working correctly!")
    else:
        print("\n❌ Database logging issues detected!")
    
    sys.exit(0 if success else 1)
