#!/usr/bin/env python3
"""
Script untuk membersihkan sesi lama dan memastikan sistem siap untuk logging yang lebih baik
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def cleanup_old_sessions():
    """Cleanup old sessions and logs"""
    try:
        from app import app, db
        from models import EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("🧹 Cleaning up old sessions and logs...")
            print("=" * 60)
            
            # Ambil data sebelum cleanup
            total_sessions = EmotionSession.query.count()
            total_logs = EmotionLog.query.count()
            
            print(f"📊 Before cleanup:")
            print(f"   Total sessions: {total_sessions}")
            print(f"   Total emotion logs: {total_logs}")
            
            # Hapus sesi yang sudah completed lebih dari 7 hari
            week_ago = datetime.utcnow() - timedelta(days=7)
            old_completed_sessions = EmotionSession.query.filter(
                EmotionSession.status == 'completed',
                EmotionSession.end_time < week_ago
            ).all()
            
            print(f"\n🗑️  Found {len(old_completed_sessions)} old completed sessions")
            
            deleted_sessions = 0
            deleted_logs = 0
            
            for session in old_completed_sessions:
                # Hapus logs dulu
                session_logs = EmotionLog.query.filter_by(session_id=session.id).all()
                for log in session_logs:
                    db.session.delete(log)
                    deleted_logs += 1
                
                # Hapus session
                db.session.delete(session)
                deleted_sessions += 1
            
            # Hapus sesi auto monitoring yang tidak aktif lebih dari 3 hari
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            old_auto_sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id.is_(None),
                EmotionSession.status == 'active',
                EmotionSession.created_at < three_days_ago
            ).all()
            
            print(f"🗑️  Found {len(old_auto_sessions)} old auto monitoring sessions")
            
            for session in old_auto_sessions:
                # Hapus logs dulu
                session_logs = EmotionLog.query.filter_by(session_id=session.id).all()
                for log in session_logs:
                    db.session.delete(log)
                    deleted_logs += 1
                
                # Hapus session
                db.session.delete(session)
                deleted_sessions += 1
            
            # Commit changes
            db.session.commit()
            
            # Ambil data setelah cleanup
            new_total_sessions = EmotionSession.query.count()
            new_total_logs = EmotionLog.query.count()
            
            print(f"\n✅ Cleanup completed:")
            print(f"   Deleted sessions: {deleted_sessions}")
            print(f"   Deleted logs: {deleted_logs}")
            print(f"   Remaining sessions: {new_total_sessions}")
            print(f"   Remaining logs: {new_total_logs}")
            
            return True
            
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def create_daily_sessions():
    """Create daily auto monitoring sessions for all students"""
    try:
        from app import app, db
        from models import EmotionSession, Student
        
        with app.app_context():
            print("📅 Creating daily auto monitoring sessions...")
            print("=" * 60)
            
            # Ambil semua siswa
            students = Student.query.all()
            today = date.today()
            
            print(f"👥 Found {len(students)} students")
            
            created_sessions = 0
            
            for student in students:
                # Cek apakah sudah ada sesi auto monitoring hari ini
                existing_session = EmotionSession.query.filter(
                    EmotionSession.student_id == student.id,
                    EmotionSession.teacher_id.is_(None),
                    db.func.date(EmotionSession.created_at) == today
                ).first()
                
                if not existing_session:
                    # Buat sesi auto monitoring baru
                    session_name = f'Auto Monitoring - {today.strftime("%Y-%m-%d")} - {student.full_name}'
                    new_session = EmotionSession(
                        student_id=student.id,
                        teacher_id=None,
                        session_name=session_name,
                        status='active'
                    )
                    
                    db.session.add(new_session)
                    created_sessions += 1
                    print(f"   ✅ Created session for {student.full_name}")
                else:
                    print(f"   ⏭️  Session already exists for {student.full_name}")
            
            db.session.commit()
            
            print(f"\n✅ Created {created_sessions} new daily sessions")
            
            return True
            
    except Exception as e:
        print(f"❌ Daily session creation failed: {e}")
        return False

def show_current_status():
    """Show current database status"""
    try:
        from app import app, db
        from models import EmotionSession, EmotionLog, Student
        from collections import Counter
        
        with app.app_context():
            print("📊 Current Database Status")
            print("=" * 60)
            
            # Basic counts
            total_sessions = EmotionSession.query.count()
            total_logs = EmotionLog.query.count()
            total_students = Student.query.count()
            
            print(f"📈 Basic Statistics:")
            print(f"   Students: {total_students}")
            print(f"   Sessions: {total_sessions}")
            print(f"   Emotion logs: {total_logs}")
            
            # Active sessions
            active_sessions = EmotionSession.query.filter(
                EmotionSession.status == 'active'
            ).all()
            
            print(f"\n🟢 Active Sessions: {len(active_sessions)}")
            for session in active_sessions:
                student_name = "Unknown"
                if session.student_id:
                    student = Student.query.get(session.student_id)
                    if student:
                        student_name = student.full_name
                
                print(f"   - {session.session_name} (Student: {student_name})")
            
            # Today's activity
            today = date.today()
            today_logs = EmotionLog.query.filter(
                db.func.date(EmotionLog.detected_at) == today
            ).all()
            
            print(f"\n📅 Today's Activity:")
            print(f"   Emotion logs: {len(today_logs)}")
            
            if today_logs:
                emotion_counts = Counter(log.emotion for log in today_logs)
                print(f"   Emotion distribution:")
                for emotion, count in emotion_counts.most_common():
                    percentage = (count / len(today_logs)) * 100
                    print(f"     - {emotion}: {count} ({percentage:.1f}%)")
            
            # Weekly activity
            week_ago = date.today() - timedelta(days=7)
            weekly_sessions = EmotionSession.query.filter(
                db.func.date(EmotionSession.created_at) >= week_ago
            ).count()
            
            weekly_logs = EmotionLog.query.filter(
                db.func.date(EmotionLog.detected_at) >= week_ago
            ).count()
            
            print(f"\n📊 Weekly Activity:")
            print(f"   Sessions: {weekly_sessions}")
            print(f"   Emotion logs: {weekly_logs}")
            
            return True
            
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Cleanup and Optimization")
    print("=" * 60)
    
    # Show current status
    show_current_status()
    
    print("\n" + "=" * 60)
    
    # Cleanup old data
    cleanup_old_sessions()
    
    print("\n" + "=" * 60)
    
    # Create daily sessions
    create_daily_sessions()
    
    print("\n" + "=" * 60)
    
    # Show final status
    show_current_status()
    
    print("\n✅ Database optimization completed!")
    print("🎯 System is now ready for better emotion logging!")
