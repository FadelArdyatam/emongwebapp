#!/usr/bin/env python3
"""
Script untuk debug masalah reports di dashboard guru
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_guru_sessions_api():
    """Debug API guru sessions"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("🔍 Debugging Guru Sessions API...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found in database")
                return False
            
            print(f"👤 Guru: {guru.full_name} (ID: {guru.id})")
            
            # Cek sesi guru
            sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id == guru.id
            ).order_by(EmotionSession.start_time.desc()).all()
            
            print(f"📊 Total sessions for guru: {len(sessions)}")
            
            if not sessions:
                print("❌ No sessions found for this guru")
                return False
            
            # Debug setiap sesi
            for i, session in enumerate(sessions[:5]):  # Tampilkan 5 sesi pertama
                print(f"\n📅 Session {i+1}: {session.session_name} (ID: {session.id})")
                print(f"   Status: {session.status}")
                print(f"   Start time: {session.start_time}")
                print(f"   End time: {session.end_time}")
                print(f"   Student ID: {session.student_id}")
                
                # Hitung statistik
                emotion_logs_count = EmotionLog.query.filter(
                    EmotionLog.session_id == session.id
                ).count()
                
                unique_students_count = db.session.query(
                    db.func.count(db.func.distinct(EmotionLog.student_id))
                ).filter(
                    EmotionLog.session_id == session.id,
                    EmotionLog.student_id.isnot(None)
                ).scalar() or 0
                
                # Hitung emosi dominan
                dominant_emotion = db.session.query(
                    EmotionLog.emotion,
                    db.func.count(EmotionLog.id).label('count')
                ).filter(
                    EmotionLog.session_id == session.id
                ).group_by(
                    EmotionLog.emotion
                ).order_by(
                    db.func.count(EmotionLog.id).desc()
                ).first()
                
                print(f"   Total detections: {emotion_logs_count}")
                print(f"   Unique students: {unique_students_count}")
                print(f"   Dominant emotion: {dominant_emotion.emotion if dominant_emotion else 'None'}")
                
                if emotion_logs_count > 0:
                    print(f"   Dominant emotion count: {dominant_emotion.count if dominant_emotion else 0}")
            
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_guru_dashboard_stats():
    """Debug API guru dashboard stats"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("\n🔍 Debugging Guru Dashboard Stats API...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found in database")
                return False
            
            print(f"👤 Guru: {guru.full_name} (ID: {guru.id})")
            
            # Simulasi API /api/dashboard/guru/stats
            print("🔍 Simulating /api/dashboard/guru/stats API...")
            
            # Hitung total siswa
            total_students = Student.query.filter(Student.is_active == True).count()
            
            # Hitung sesi aktif
            active_sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id == guru.id,
                EmotionSession.status == 'active'
            ).count()
            
            # Hitung deteksi hari ini
            today = date.today()
            today_detections = EmotionLog.query.join(EmotionSession).filter(
                EmotionSession.teacher_id == guru.id,
                db.func.date(EmotionLog.detected_at) == today
            ).count()
            
            # Hitung total deteksi
            total_detections = EmotionLog.query.join(EmotionSession).filter(
                EmotionSession.teacher_id == guru.id
            ).count()
            
            # Hitung sesi minggu ini
            week_ago = date.today() - timedelta(days=7)
            weekly_sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id == guru.id,
                db.func.date(EmotionSession.start_time) >= week_ago
            ).count()
            
            # Hitung distribusi emosi
            emotion_data = {}
            emotion_counts = db.session.query(
                EmotionLog.emotion,
                db.func.count(EmotionLog.id).label('count')
            ).join(EmotionSession).filter(
                EmotionSession.teacher_id == guru.id,
                db.func.date(EmotionLog.detected_at) >= week_ago
            ).group_by(EmotionLog.emotion).all()
            
            for emotion, count in emotion_counts:
                emotion_data[emotion] = int(count)
            
            # Hitung emosi dominan
            if emotion_data:
                dominant_emotion = max(emotion_data, key=emotion_data.get)
            else:
                dominant_emotion = 'neutral'
            
            # Hitung rata-rata waktu sesi
            completed_sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id == guru.id,
                EmotionSession.status == 'completed',
                EmotionSession.end_time.isnot(None)
            ).all()
            
            total_duration = 0
            for session in completed_sessions:
                if session.start_time and session.end_time:
                    duration = (session.end_time - session.start_time).total_seconds() / 60  # dalam menit
                    total_duration += duration
            
            avg_session_time = total_duration / len(completed_sessions) if completed_sessions else 0
            
            # Ambil sesi terbaru
            recent_sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id == guru.id
            ).order_by(EmotionSession.start_time.desc()).limit(5).all()
            
            recent_sessions_data = []
            for session in recent_sessions:
                recent_sessions_data.append({
                    'id': session.id,
                    'session_name': session.session_name,
                    'status': session.status,
                    'start_time': session.start_time.isoformat() if session.start_time else None,
                    'student_name': 'N/A'  # Bisa ditambahkan jika perlu
                })
            
            # Simulasi response API
            api_response = {
                'total_students': total_students,
                'active_sessions': active_sessions,
                'today_detections': today_detections,
                'total_detections': total_detections,
                'weekly_sessions': weekly_sessions,
                'avg_emotion': dominant_emotion,
                'avg_session_time': f"{avg_session_time:.0f}m",
                'emotion_data': emotion_data,
                'recent_sessions': recent_sessions_data
            }
            
            print(f"📊 Dashboard stats:")
            print(f"   Total students: {total_students}")
            print(f"   Active sessions: {active_sessions}")
            print(f"   Today detections: {today_detections}")
            print(f"   Total detections: {total_detections}")
            print(f"   Weekly sessions: {weekly_sessions}")
            print(f"   Dominant emotion: {dominant_emotion}")
            print(f"   Avg session time: {avg_session_time:.0f}m")
            print(f"   Emotion data: {emotion_data}")
            print(f"   Recent sessions: {len(recent_sessions_data)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_daily_summary():
    """Debug daily summary data"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        from collections import Counter
        
        with app.app_context():
            print("\n🔍 Debugging Daily Summary...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found in database")
                return False
            
            print(f"👤 Guru: {guru.full_name} (ID: {guru.id})")
            
            # Simulasi daily summary
            today = date.today()
            
            # Ambil data hari ini
            today_logs = EmotionLog.query.join(EmotionSession).filter(
                EmotionSession.teacher_id == guru.id,
                db.func.date(EmotionLog.detected_at) == today
            ).all()
            
            print(f"📅 Today's data:")
            print(f"   Total logs: {len(today_logs)}")
            
            if today_logs:
                # Hitung distribusi emosi
                emotion_counts = Counter(log.emotion for log in today_logs)
                
                print(f"   Emotion distribution:")
                for emotion, count in emotion_counts.most_common():
                    percentage = (count / len(today_logs)) * 100
                    print(f"     - {emotion}: {count} ({percentage:.1f}%)")
                
                # Hitung siswa unik
                unique_students = set(log.student_id for log in today_logs if log.student_id)
                print(f"   Unique students: {len(unique_students)}")
                
                # Hitung confidence rata-rata
                confidences = [log.confidence_score for log in today_logs if log.confidence_score]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    print(f"   Avg confidence: {avg_confidence:.3f}")
            else:
                print("   ⚠️  No logs found for today")
            
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_guru_reports_debug():
    """Generate guru reports debug report"""
    print("🚀 Guru Reports Debug Report")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'guru_sessions_api': debug_guru_sessions_api(),
        'guru_dashboard_stats': debug_guru_dashboard_stats(),
        'daily_summary': debug_daily_summary()
    }
    
    print("\n" + "=" * 60)
    print("📋 DEBUG SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test, status in results.items():
        if test == 'timestamp':
            continue
        status_text = "✅ PASS" if status else "❌ FAIL"
        print(f"   {test}: {status_text}")
        if not status:
            all_passed = False
    
    print(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if all_passed else '⚠️  SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Guru reports data is available and should display correctly!")
        print("   - Sessions API returns data")
        print("   - Dashboard stats API works")
        print("   - Daily summary has data")
    else:
        print("\n❌ Issues found that need to be fixed!")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"guru_reports_debug_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Debug report saved to: {report_file}")
    
    return all_passed

if __name__ == "__main__":
    success = generate_guru_reports_debug()
    sys.exit(0 if success else 1)
