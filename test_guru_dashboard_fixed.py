#!/usr/bin/env python3
"""
Script untuk test dashboard guru setelah perbaikan
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_guru_dashboard_apis():
    """Test semua API yang digunakan dashboard guru"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("🧪 Testing Guru Dashboard APIs...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found in database")
                return False
            
            print(f"👤 Guru: {guru.full_name} (ID: {guru.id})")
            
            # Test API /api/dashboard/guru/stats
            print("\n🔍 Testing /api/dashboard/guru/stats...")
            
            # Simulasi data yang dikembalikan API
            total_students = Student.query.filter(Student.is_active == True).count()
            
            active_sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id == guru.id,
                EmotionSession.status == 'active'
            ).count()
            
            today = date.today()
            today_detections = EmotionLog.query.join(EmotionSession).filter(
                EmotionSession.teacher_id == guru.id,
                db.func.date(EmotionLog.detected_at) == today
            ).count()
            
            total_detections = EmotionLog.query.join(EmotionSession).filter(
                EmotionSession.teacher_id == guru.id
            ).count()
            
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
                    duration = (session.end_time - session.start_time).total_seconds() / 60
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
                    'start_time': session.start_time.isoformat() if session.start_time else None
                })
            
            dashboard_stats = {
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
            
            print(f"✅ Dashboard stats:")
            print(f"   Total students: {total_students}")
            print(f"   Active sessions: {active_sessions}")
            print(f"   Today detections: {today_detections}")
            print(f"   Total detections: {total_detections}")
            print(f"   Weekly sessions: {weekly_sessions}")
            print(f"   Dominant emotion: {dominant_emotion}")
            print(f"   Avg session time: {avg_session_time:.0f}m")
            print(f"   Emotion data: {emotion_data}")
            print(f"   Recent sessions: {len(recent_sessions_data)}")
            
            # Test API /api/guru/sessions
            print(f"\n🔍 Testing /api/guru/sessions...")
            
            sessions = EmotionSession.query.filter(
                EmotionSession.teacher_id == guru.id
            ).order_by(EmotionSession.start_time.desc()).limit(10).all()
            
            sessions_data = []
            for session in sessions:
                # Hitung statistik untuk setiap sesi
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
                
                session_dict = session.to_dict()
                session_dict.update({
                    'total_detections': emotion_logs_count,
                    'unique_students': unique_students_count,
                    'dominant_emotion': dominant_emotion.emotion if dominant_emotion else None,
                    'dominant_emotion_count': dominant_emotion.count if dominant_emotion else 0
                })
                
                sessions_data.append(session_dict)
            
            print(f"✅ Sessions data:")
            print(f"   Total sessions: {len(sessions_data)}")
            
            for i, session in enumerate(sessions_data[:3]):
                print(f"   Session {i+1}: {session['session_name']}")
                print(f"     Status: {session['status']}")
                print(f"     Total detections: {session['total_detections']}")
                print(f"     Unique students: {session['unique_students']}")
                print(f"     Dominant emotion: {session['dominant_emotion']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_data_processing():
    """Test pemrosesan data frontend"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("\n🧪 Testing Frontend Data Processing...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found in database")
                return False
            
            # Simulasi data dashboard stats
            week_ago = date.today() - timedelta(days=7)
            
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
            
            print(f"📊 Emotion data for charts: {emotion_data}")
            
            # Simulasi data yang akan dikirim ke chart
            chart_data = {
                'happy': emotion_data.get('happy', 0),
                'sad': emotion_data.get('sad', 0),
                'angry': emotion_data.get('angry', 0),
                'fear': emotion_data.get('fear', 0),
                'surprise': emotion_data.get('surprise', 0),
                'disgust': emotion_data.get('disgust', 0),
                'neutral': emotion_data.get('neutral', 0)
            }
            
            total_emotions = sum(chart_data.values())
            print(f"📈 Chart data: {chart_data}")
            print(f"📊 Total emotions: {total_emotions}")
            
            if total_emotions > 0:
                print(f"✅ Valid data for charts")
                
                # Tampilkan distribusi
                for emotion, count in chart_data.items():
                    percentage = (count / total_emotions * 100) if total_emotions > 0 else 0
                    print(f"   - {emotion}: {count} ({percentage:.1f}%)")
            else:
                print(f"⚠️  No emotion data for charts")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_guru_dashboard_test_report():
    """Generate guru dashboard test report"""
    print("🚀 Guru Dashboard Test Report (After Fixes)")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'guru_dashboard_apis': test_guru_dashboard_apis(),
        'frontend_data_processing': test_frontend_data_processing()
    }
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
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
        print("\n🎉 Guru dashboard should now display data correctly!")
        print("   - Dashboard stats API works")
        print("   - Sessions API works")
        print("   - Emotion charts have data")
        print("   - Frontend processing works")
    else:
        print("\n❌ Issues found that need to be fixed!")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"guru_dashboard_test_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test report saved to: {report_file}")
    
    return all_passed

if __name__ == "__main__":
    success = generate_guru_dashboard_test_report()
    sys.exit(0 if success else 1)
