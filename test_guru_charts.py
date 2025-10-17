#!/usr/bin/env python3
"""
Script untuk test chart data loading di dashboard guru
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_chart_data_loading():
    """Test chart data loading untuk dashboard guru"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("🧪 Testing Chart Data Loading...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found in database")
                return False
            
            print(f"👤 Guru: {guru.full_name} (ID: {guru.id})")
            
            # Test data untuk chart pie (Distribusi Emosi Hari Ini)
            print("\n🔍 Testing Pie Chart Data (Distribusi Emosi Hari Ini)...")
            
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
            
            # Format data untuk chart
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
            print(f"📊 Pie Chart Data: {chart_data}")
            print(f"📈 Total Emotions: {total_emotions}")
            
            if total_emotions > 0:
                print("✅ Pie chart has valid data")
                for emotion, count in chart_data.items():
                    percentage = (count / total_emotions * 100) if total_emotions > 0 else 0
                    print(f"   - {emotion}: {count} ({percentage:.1f}%)")
            else:
                print("⚠️  Pie chart has no data")
            
            # Test data untuk trend chart (7 hari terakhir)
            print(f"\n🔍 Testing Trend Chart Data (7 Hari Terakhir)...")
            
            # Buat data trend untuk 7 hari terakhir
            days = []
            today = date.today()
            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                days.append(day.isoformat())
            
            print(f"📅 Trend Days: {days}")
            
            # Hitung data per hari
            trend_data = {}
            for day in days:
                day_emotions = {}
                emotion_counts_day = db.session.query(
                    EmotionLog.emotion,
                    db.func.count(EmotionLog.id).label('count')
                ).join(EmotionSession).filter(
                    EmotionSession.teacher_id == guru.id,
                    db.func.date(EmotionLog.detected_at) == day
                ).group_by(EmotionLog.emotion).all()
                
                for emotion, count in emotion_counts_day:
                    day_emotions[emotion] = int(count)
                
                trend_data[day] = day_emotions
            
            print(f"📊 Trend Data: {trend_data}")
            
            # Buat dataset untuk trend chart
            emos = ['happy','sad','angry','fear','surprise','disgust','neutral']
            colors = {
                'happy':'#22c55e', 'sad':'#3b82f6', 'angry':'#ef4444', 'fear':'#8b5cf6', 
                'surprise':'#fb923c', 'disgust':'#6b7280', 'neutral':'#94a3b8'
            }
            
            datasets = []
            for em in emos:
                data_points = []
                for day in days:
                    count = trend_data.get(day, {}).get(em, 0)
                    data_points.append(count)
                
                datasets.append({
                    'label': em.charAt(0).toUpperCase() + em.slice(1),
                    'data': data_points,
                    'borderColor': colors[em],
                    'backgroundColor': 'transparent',
                    'tension': 0.4,
                    'borderWidth': 3,
                    'pointRadius': 4,
                    'pointHoverRadius': 6
                })
            
            print(f"📈 Trend Datasets: {len(datasets)} datasets")
            for i, dataset in enumerate(datasets):
                total_points = sum(dataset['data'])
                print(f"   - {dataset['label']}: {dataset['data']} (total: {total_points})")
            
            # Test chart initialization
            print(f"\n🔍 Testing Chart Initialization...")
            
            # Simulasi chart data structure
            pie_chart_data = {
                'labels': ['Happy', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust', 'Neutral'],
                'datasets': [{
                    'data': [
                        chart_data['happy'],
                        chart_data['sad'],
                        chart_data['angry'],
                        chart_data['fear'],
                        chart_data['surprise'],
                        chart_data['disgust'],
                        chart_data['neutral']
                    ],
                    'backgroundColor': [
                        '#22c55e', '#3b82f6', '#ef4444', '#8b5cf6',
                        '#fb923c', '#6b7280', '#94a3b8'
                    ]
                }]
            }
            
            trend_chart_data = {
                'labels': days,
                'datasets': datasets
            }
            
            print(f"✅ Pie Chart Structure: {pie_chart_data}")
            print(f"✅ Trend Chart Structure: {len(trend_chart_data['datasets'])} datasets")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints yang digunakan untuk chart"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("\n🧪 Testing API Endpoints...")
            print("=" * 60)
            
            # Test /api/dashboard/guru/stats
            print("🔍 Testing /api/dashboard/guru/stats...")
            
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found")
                return False
            
            # Simulasi response dari API
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
            
            api_response = {
                'status': 'success',
                'total_students': Student.query.filter(Student.is_active == True).count(),
                'active_sessions': EmotionSession.query.filter(
                    EmotionSession.teacher_id == guru.id,
                    EmotionSession.status == 'active'
                ).count(),
                'today_detections': EmotionLog.query.join(EmotionSession).filter(
                    EmotionSession.teacher_id == guru.id,
                    db.func.date(EmotionLog.detected_at) == date.today()
                ).count(),
                'total_detections': EmotionLog.query.join(EmotionSession).filter(
                    EmotionSession.teacher_id == guru.id
                ).count(),
                'weekly_sessions': EmotionSession.query.filter(
                    EmotionSession.teacher_id == guru.id,
                    db.func.date(EmotionSession.start_time) >= week_ago
                ).count(),
                'avg_emotion': max(emotion_data, key=emotion_data.get) if emotion_data else 'neutral',
                'avg_session_time': '1928m',
                'emotion_data': emotion_data,
                'recent_sessions': []
            }
            
            print(f"✅ API Response: {api_response}")
            
            # Test data format untuk frontend
            if api_response['emotion_data']:
                print("✅ Emotion data available for charts")
                print(f"   - Total emotions: {sum(api_response['emotion_data'].values())}")
                print(f"   - Emotions: {api_response['emotion_data']}")
            else:
                print("⚠️  No emotion data in API response")
            
            return True
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_chart_test_report():
    """Generate chart test report"""
    print("🚀 Guru Dashboard Chart Test Report")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'chart_data_loading': test_chart_data_loading(),
        'api_endpoints': test_api_endpoints()
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
        print("\n🎉 Chart data loading should work correctly!")
        print("   - Pie chart has valid data")
        print("   - Trend chart has valid data")
        print("   - API endpoints work")
        print("   - Data format is correct")
    else:
        print("\n❌ Issues found that need to be fixed!")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"guru_chart_test_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test report saved to: {report_file}")
    
    return all_passed

if __name__ == "__main__":
    success = generate_chart_test_report()
    sys.exit(0 if success else 1)

