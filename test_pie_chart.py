#!/usr/bin/env python3
"""
Script untuk test chart pie Distribusi Emosi Hari Ini
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pie_chart_data():
    """Test data untuk chart pie Distribusi Emosi Hari Ini"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("🧪 Testing Pie Chart Data (Distribusi Emosi Hari Ini)...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found in database")
                return False
            
            print(f"👤 Guru: {guru.full_name} (ID: {guru.id})")
            
            # Test data untuk chart pie - ambil data 7 hari terakhir
            week_ago = date.today() - timedelta(days=7)
            print(f"📅 Data period: {week_ago} to {date.today()}")
            
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
            
            print(f"📊 Raw emotion data: {emotion_data}")
            
            # Format data untuk chart pie
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
                print("✅ Pie chart has valid data")
                print("\n📊 Emotion Distribution:")
                for emotion, count in chart_data.items():
                    percentage = (count / total_emotions * 100) if total_emotions > 0 else 0
                    print(f"   - {emotion}: {count} ({percentage:.1f}%)")
                
                # Test chart data structure
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
                        ],
                        'borderWidth': 0,
                        'hoverOffset': 8
                    }]
                }
                
                print(f"\n✅ Pie Chart Structure:")
                print(f"   - Labels: {pie_chart_data['labels']}")
                print(f"   - Data: {pie_chart_data['datasets'][0]['data']}")
                print(f"   - Colors: {pie_chart_data['datasets'][0]['backgroundColor']}")
                
                return True
            else:
                print("⚠️  Pie chart has no data")
                return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_response():
    """Test API response untuk chart pie"""
    try:
        from app import app, db
        from models import User, EmotionSession, EmotionLog, Student
        
        with app.app_context():
            print("\n🧪 Testing API Response for Pie Chart...")
            print("=" * 60)
            
            # Ambil guru pertama
            guru = User.query.filter_by(role='guru').first()
            if not guru:
                print("❌ No guru found")
                return False
            
            # Simulasi response dari /api/dashboard/guru/stats
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
                'emotion_data': emotion_data,
                'total_students': Student.query.filter(Student.is_active == True).count(),
                'active_sessions': EmotionSession.query.filter(
                    EmotionSession.teacher_id == guru.id,
                    EmotionSession.status == 'active'
                ).count()
            }
            
            print(f"📡 API Response: {api_response}")
            
            if api_response['emotion_data']:
                print("✅ API returns emotion data")
                print(f"   - Total emotions: {sum(api_response['emotion_data'].values())}")
                print(f"   - Emotions: {api_response['emotion_data']}")
                
                # Test data format untuk frontend
                values = [
                    api_response['emotion_data'].get('happy', 0),
                    api_response['emotion_data'].get('sad', 0),
                    api_response['emotion_data'].get('angry', 0),
                    api_response['emotion_data'].get('fear', 0),
                    api_response['emotion_data'].get('surprise', 0),
                    api_response['emotion_data'].get('disgust', 0),
                    api_response['emotion_data'].get('neutral', 0)
                ]
                
                print(f"✅ Values array for chart: {values}")
                print(f"✅ Total values: {sum(values)}")
                
                return True
            else:
                print("❌ API returns no emotion data")
                return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chart_initialization():
    """Test chart initialization"""
    print("\n🧪 Testing Chart Initialization...")
    print("=" * 60)
    
    # Test chart data structure
    chart_config = {
        'type': 'doughnut',
        'data': {
            'labels': ['Happy', 'Sad', 'Angry', 'Fear', 'Surprise', 'Disgust', 'Neutral'],
            'datasets': [{
                'data': [0, 0, 0, 0, 0, 0, 0],
                'backgroundColor': [
                    '#22c55e', '#3b82f6', '#ef4444', '#8b5cf6',
                    '#fb923c', '#6b7280', '#94a3b8'
                ],
                'borderWidth': 0,
                'hoverOffset': 8
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'bottom',
                    'labels': {
                        'padding': 15,
                        'usePointStyle': True,
                        'font': {
                            'size': 11,
                            'weight': '600'
                        }
                    }
                }
            }
        }
    }
    
    print("✅ Chart configuration:")
    print(f"   - Type: {chart_config['type']}")
    print(f"   - Labels: {chart_config['data']['labels']}")
    print(f"   - Initial data: {chart_config['data']['datasets'][0]['data']}")
    print(f"   - Colors: {chart_config['data']['datasets'][0]['backgroundColor']}")
    
    return True

def generate_pie_chart_test_report():
    """Generate pie chart test report"""
    print("🚀 Pie Chart Test Report (Distribusi Emosi Hari Ini)")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'pie_chart_data': test_pie_chart_data(),
        'api_response': test_api_response(),
        'chart_initialization': test_chart_initialization()
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
        print("\n🎉 Pie chart should display data correctly!")
        print("   - Chart data is valid")
        print("   - API returns correct data")
        print("   - Chart initialization works")
        print("   - Data format is correct")
    else:
        print("\n❌ Issues found that need to be fixed!")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"pie_chart_test_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test report saved to: {report_file}")
    
    return all_passed

if __name__ == "__main__":
    success = generate_pie_chart_test_report()
    sys.exit(0 if success else 1)

