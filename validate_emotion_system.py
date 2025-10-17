#!/usr/bin/env python3
"""
Script untuk memvalidasi sistem deteksi emosi yang telah diperbaiki
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def validate_bias_correction():
    """Validasi bias correction service"""
    try:
        from services.emotion_bias_correction import EmotionBiasCorrection
        print("✅ EmotionBiasCorrection berhasil diimport")
        
        # Test bias correction
        bias_correction = EmotionBiasCorrection()
        print("✅ EmotionBiasCorrection berhasil diinisialisasi")
        
        # Test dengan skenario yang berbeda
        test_cases = [
            {
                'name': 'Low Angry Score',
                'scores': {
                    'happy': 0.3, 'sad': 0.2, 'angry': 0.1, 'fear': 0.1,
                    'surprise': 0.1, 'disgust': 0.2, 'neutral': 0.4
                }
            },
            {
                'name': 'Low Fear Score',
                'scores': {
                    'happy': 0.3, 'sad': 0.2, 'angry': 0.1, 'fear': 0.05,
                    'surprise': 0.1, 'disgust': 0.2, 'neutral': 0.4
                }
            },
            {
                'name': 'Low Surprised Score',
                'scores': {
                    'happy': 0.3, 'sad': 0.2, 'angry': 0.1, 'fear': 0.1,
                    'surprise': 0.05, 'disgust': 0.2, 'neutral': 0.4
                }
            }
        ]
        
        print("\n🧪 Testing Bias Correction...")
        for test_case in test_cases:
            result = bias_correction.correct_emotion_bias(
                test_case['scores'], 
                context='classroom'
            )
            print(f"   {test_case['name']}: {test_case['scores']} -> {result['emotion']} (confidence: {result['confidence']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating bias correction: {e}")
        return False

def validate_app_endpoints():
    """Validasi endpoint aplikasi"""
    try:
        from app import app
        print("✅ Flask app berhasil diimport")
        
        # Test beberapa endpoint
        with app.test_client() as client:
            # Test health check
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Root endpoint berfungsi")
            else:
                print(f"⚠️  Root endpoint status: {response.status_code}")
            
            # Test API endpoints
            api_endpoints = [
                '/api/parent/children',
                '/api/parent/distribution',
                '/parent/children/summary'
            ]
            
            for endpoint in api_endpoints:
                response = client.get(endpoint)
                if response.status_code in [200, 401, 403]:  # 401/403 expected tanpa auth
                    print(f"✅ {endpoint} endpoint accessible")
                else:
                    print(f"⚠️  {endpoint} status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating app endpoints: {e}")
        return False

def validate_emotion_services():
    """Validasi emotion services"""
    try:
        from services.emotion_service import EmotionProcessor
        print("✅ EmotionProcessor berhasil diimport")
        
        from services.emotion_prediction_service import EmotionPredictionService
        print("✅ EmotionPredictionService berhasil diimport")
        
        from services.advanced_temporal_service import AdvancedTemporalService
        print("✅ AdvancedTemporalService berhasil diimport")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating emotion services: {e}")
        return False

def generate_validation_report():
    """Generate validation report"""
    print("🚀 Starting Emotion System Validation...")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'bias_correction': validate_bias_correction(),
        'app_endpoints': validate_app_endpoints(),
        'emotion_services': validate_emotion_services()
    }
    
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for service, status in results.items():
        if service == 'timestamp':
            continue
        status_text = "✅ PASS" if status else "❌ FAIL"
        print(f"   {service}: {status_text}")
        if not status:
            all_passed = False
    
    print(f"\n🎯 Overall Status: {'✅ ALL SYSTEMS OK' if all_passed else '⚠️  SOME ISSUES FOUND'}")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"validation_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Validation report saved to: {report_file}")
    
    return all_passed

if __name__ == "__main__":
    success = generate_validation_report()
    sys.exit(0 if success else 1)
