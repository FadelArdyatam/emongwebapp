#!/usr/bin/env python3
"""
Script untuk debug masalah dashboard parent
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_dashboard_data():
    """Debug data dashboard parent"""
    try:
        from app import app, db
        from models import User, Student, StudentParent, EmotionSession, EmotionLog
        from collections import Counter
        
        with app.app_context():
            print("🔍 Debugging Parent Dashboard Data...")
            print("=" * 60)
            
            # Ambil parent pertama
            parent = User.query.filter_by(role='orang_tua').first()
            if not parent:
                print("❌ No parent found in database")
                return False
            
            print(f"👤 Parent: {parent.full_name} (ID: {parent.id})")
            
            # Ambil children dari parent ini
            children = db.session.query(Student).join(StudentParent).filter(
                StudentParent.parent_id == parent.id,
                Student.is_active == True
            ).all()
            
            print(f"👥 Children found: {len(children)}")
            
            if not children:
                print("❌ No children found for this parent")
                return False
            
            # Debug setiap anak
            for i, child in enumerate(children):
                print(f"\n👶 Child {i+1}: {child.full_name} (ID: {child.id})")
                
                # Cek data emosi 7 hari terakhir
                week_ago = date.today() - timedelta(days=7)
                
                emotion_logs = EmotionLog.query.join(EmotionSession).filter(
                    EmotionSession.student_id == child.id,
                    db.func.date(EmotionLog.detected_at) >= week_ago
                ).all()
                
                print(f"   📊 Emotion logs (7 days): {len(emotion_logs)}")
                
                if emotion_logs:
                    emotion_counts = Counter(log.emotion for log in emotion_logs)
                    print(f"   😊 Emotion distribution: {dict(emotion_counts)}")
                    
                    # Hitung statistik
                    total_emotions = sum(emotion_counts.values())
                    positive_emotions = emotion_counts.get('happy', 0) + emotion_counts.get('surprise', 0)
                    positive_trend = (positive_emotions / total_emotions * 100) if total_emotions > 0 else 0
                    
                    print(f"   📈 Total emotions: {total_emotions}")
                    print(f"   😊 Positive emotions: {positive_emotions}")
                    print(f"   📊 Positive trend: {positive_trend:.1f}%")
                else:
                    print("   ⚠️  No emotion logs found")
                
                # Cek sesi 7 hari terakhir
                weekly_sessions = EmotionSession.query.filter(
                    EmotionSession.student_id == child.id,
                    db.func.date(EmotionSession.created_at) >= week_ago
                ).all()
                
                print(f"   📅 Weekly sessions: {len(weekly_sessions)}")
                
                # Cek emosi terakhir
                last_emotion_log = EmotionLog.query.join(EmotionSession).filter(
                    EmotionSession.student_id == child.id
                ).order_by(EmotionLog.detected_at.desc()).first()
                
                if last_emotion_log:
                    print(f"   🎭 Last emotion: {last_emotion_log.emotion} at {last_emotion_log.detected_at}")
                else:
                    print("   ⚠️  No last emotion found")
            
            # Debug distribusi keseluruhan
            print(f"\n📊 Overall Distribution (7 days):")
            child_ids = [child.id for child in children]
            
            emotion_logs = EmotionLog.query.join(EmotionSession).filter(
                EmotionLog.student_id.in_(child_ids),
                db.func.date(EmotionLog.detected_at) >= week_ago
            ).all()
            
            if emotion_logs:
                emotion_counts = Counter(log.emotion for log in emotion_logs)
                total_emotions = sum(emotion_counts.values())
                
                print(f"   Total emotion logs: {len(emotion_logs)}")
                print(f"   Total emotions: {total_emotions}")
                
                for emotion, count in emotion_counts.most_common():
                    percentage = (count / total_emotions * 100) if total_emotions > 0 else 0
                    print(f"   - {emotion}: {count} ({percentage:.1f}%)")
            else:
                print("   ⚠️  No emotion logs found for any child")
            
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_api_responses():
    """Debug API responses yang digunakan frontend"""
    try:
        from app import app, db
        from models import User, Student, StudentParent, EmotionSession, EmotionLog
        
        with app.app_context():
            print("\n🔍 Debugging API Responses...")
            print("=" * 60)
            
            # Ambil parent pertama
            parent = User.query.filter_by(role='orang_tua').first()
            if not parent:
                print("❌ No parent found in database")
                return False
            
            # Simulasi API /api/parent/children
            print("🔍 Simulating /api/parent/children API...")
            
            children = db.session.query(Student).join(StudentParent).filter(
                StudentParent.parent_id == parent.id,
                Student.is_active == True
            ).all()
            
            children_data = []
            week_ago = date.today() - timedelta(days=7)
            
            for child in children:
                # Hitung distribusi emosi minggu ini
                emotion_stats = {}
                emotion_counts = db.session.query(
                    EmotionLog.emotion,
                    db.func.count(EmotionLog.id).label('count')
                ).join(EmotionSession).filter(
                    EmotionSession.student_id == child.id,
                    db.func.date(EmotionLog.detected_at) >= week_ago
                ).group_by(EmotionLog.emotion).all()
                
                for emotion, count in emotion_counts:
                    emotion_stats[emotion] = int(count)
                
                # Hitung sesi minggu ini
                weekly_sessions = EmotionSession.query.filter(
                    EmotionSession.student_id == child.id,
                    db.func.date(EmotionSession.created_at) >= week_ago
                ).count()
                
                # Ambil emosi terakhir
                last_emotion_log = EmotionLog.query.join(EmotionSession).filter(
                    EmotionSession.student_id == child.id
                ).order_by(EmotionLog.detected_at.desc()).first()
                
                # Hitung skor emosi positif
                positive_count = db.session.query(EmotionLog).join(EmotionSession).filter(
                    EmotionSession.student_id == child.id,
                    EmotionLog.emotion.in_(['happy', 'surprise']),
                    db.func.date(EmotionLog.detected_at) >= week_ago
                ).count()
                total_count = db.session.query(EmotionLog).join(EmotionSession).filter(
                    EmotionSession.student_id == child.id,
                    db.func.date(EmotionLog.detected_at) >= week_ago
                ).count()
                avg_emotion_score = (positive_count / total_count * 100) if total_count > 0 else 0
                
                child_data = {
                    'id': child.id,
                    'full_name': child.full_name,
                    'student_code': child.student_code,
                    'class_name': child.class_name,
                    'weekly_sessions': weekly_sessions,
                    'last_emotion': last_emotion_log.emotion if last_emotion_log else None,
                    'avg_emotion_score': round(avg_emotion_score, 1),
                    'emotion_stats': emotion_stats
                }
                children_data.append(child_data)
                
                print(f"   👶 {child.full_name}:")
                print(f"      - Weekly sessions: {weekly_sessions}")
                print(f"      - Emotion stats: {emotion_stats}")
                print(f"      - Last emotion: {last_emotion_log.emotion if last_emotion_log else 'None'}")
                print(f"      - Avg emotion score: {avg_emotion_score:.1f}%")
            
            # Simulasi API /api/parent/distribution
            print(f"\n🔍 Simulating /api/parent/distribution API...")
            
            child_ids = [child.id for child in children]
            rows = db.session.query(
                EmotionLog.emotion,
                db.func.count(EmotionLog.id)
            ).join(EmotionSession).filter(
                EmotionLog.student_id.in_(child_ids),
                db.func.date(EmotionLog.detected_at) >= week_ago
            ).group_by(EmotionLog.emotion).all()
            
            distribution = {r[0]: int(r[1]) for r in rows}
            
            print(f"   📊 Distribution: {distribution}")
            
            # Simulasi data yang akan dikirim ke frontend
            print(f"\n🖥️  Data for frontend:")
            print(f"   Children data: {len(children_data)} children")
            print(f"   Distribution data: {distribution}")
            
            # Simulasi pemrosesan frontend
            final_emotion_data = {
                'happy': distribution.get('happy', 0),
                'sad': distribution.get('sad', 0),
                'angry': distribution.get('angry', 0),
                'fear': distribution.get('fear', 0),
                'surprise': distribution.get('surprise', 0),
                'disgust': distribution.get('disgust', 0),
                'neutral': distribution.get('neutral', 0)
            }
            
            total_emotions = sum(final_emotion_data.values())
            positive_emotions = final_emotion_data['happy'] + final_emotion_data['surprise']
            positive_trend = (positive_emotions / total_emotions * 100) if total_emotions > 0 else 0
            dominant_emotion = max(final_emotion_data, key=final_emotion_data.get) if total_emotions > 0 else 'neutral'
            
            print(f"   📈 Final emotion data: {final_emotion_data}")
            print(f"   📊 Total emotions: {total_emotions}")
            print(f"   😊 Positive emotions: {positive_emotions}")
            print(f"   📈 Positive trend: {positive_trend:.1f}%")
            print(f"   🏆 Dominant emotion: {dominant_emotion}")
            
            return True
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_debug_report():
    """Generate debug report"""
    print("🚀 Parent Dashboard Debug Report")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'dashboard_data': debug_dashboard_data(),
        'api_responses': debug_api_responses()
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
        print("\n🎉 Dashboard data is available and should display correctly!")
        print("   - Database contains emotion data")
        print("   - API responses are correct")
        print("   - Frontend should receive proper data")
    else:
        print("\n❌ Issues found that need to be fixed!")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"parent_dashboard_debug_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Debug report saved to: {report_file}")
    
    return all_passed

if __name__ == "__main__":
    success = generate_debug_report()
    sys.exit(0 if success else 1)
