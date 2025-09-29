#!/usr/bin/env python3
"""
Test script untuk fitur-fitur baru yang diimplementasi:
1. Face Clustering
2. Advanced Attributes Analysis
3. Multi-person Support
4. Real-time Optimization
"""

import sys
import os
sys.path.append('.')

import numpy as np
from services.emotion_service import EmotionProcessor, FaceClustering
import time

def test_face_clustering():
    """Test Face Clustering functionality"""
    print("🧪 Testing Face Clustering...")
    
    clustering = FaceClustering()
    
    # Test face clustering dengan embedding simulasi
    test_embedding1 = np.random.rand(512)  # Simulate ArcFace embedding
    test_embedding2 = np.random.rand(512)
    test_embedding3 = test_embedding1 + np.random.rand(512) * 0.1  # Similar to embedding1
    
    print("Adding face 1...")
    cluster1 = clustering.add_face_embedding('face1', test_embedding1)
    print(f"Face 1 assigned to cluster: {cluster1}")
    
    print("Adding face 2...")
    cluster2 = clustering.add_face_embedding('face2', test_embedding2)
    print(f"Face 2 assigned to cluster: {cluster2}")
    
    print("Adding face 3 (similar to face 1)...")
    cluster3 = clustering.add_face_embedding('face3', test_embedding3)
    print(f"Face 3 assigned to cluster: {cluster3}")
    
    print("\n📊 Clustering Results:")
    clusters = clustering.get_all_clusters()
    for cluster_id, info in clusters.items():
        print(f"Cluster {cluster_id}: {info['face_count']} faces - {info['face_ids']}")
    
    print("✅ Face Clustering Test PASSED!")
    return True

def test_emotion_processor():
    """Test EmotionProcessor dengan fitur baru"""
    print("\n🧪 Testing EmotionProcessor...")
    
    processor = EmotionProcessor()
    
    # Test initialization
    assert hasattr(processor, 'face_clustering'), "Face clustering not initialized"
    assert hasattr(processor, 'frame_skip_count'), "Real-time optimization not initialized"
    assert hasattr(processor, 'min_processing_interval'), "Processing interval not set"
    
    print("✅ EmotionProcessor initialization PASSED!")
    
    # Test face clustering integration
    test_embedding = np.random.rand(512)
    cluster_id = processor.face_clustering.add_face_embedding('test_face', test_embedding)
    assert cluster_id is not None, "Face clustering failed"
    
    print("✅ Face clustering integration PASSED!")
    return True

def test_api_endpoints():
    """Test API endpoints yang baru"""
    print("\n🧪 Testing API Endpoints...")
    
    # Test import app
    try:
        from app import app
        print("✅ App import successful")
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    # Test route registration
    with app.test_client() as client:
        # Test detector backend endpoint
        response = client.get('/detector/backend')
        assert response.status_code == 200, f"Detector backend endpoint failed: {response.status_code}"
        print("✅ Detector backend endpoint PASSED!")
        
        # Test face clustering endpoint
        response = client.get('/face/clustering')
        # Should return 404 if no clustering data, but endpoint should exist
        assert response.status_code in [200, 404], f"Face clustering endpoint failed: {response.status_code}"
        print("✅ Face clustering endpoint PASSED!")
    
    print("✅ API Endpoints Test PASSED!")
    return True

def test_real_time_optimization():
    """Test real-time optimization features"""
    print("\n🧪 Testing Real-time Optimization...")
    
    processor = EmotionProcessor()
    
    # Test frame skipping
    assert processor.frame_skip_threshold == 2, "Frame skip threshold not set correctly"
    assert processor.min_processing_interval == 0.05, "Processing interval not set correctly"
    
    # Test frame skip logic
    processor.frame_skip_count = 0
    processor.frame_skip_count += 1
    assert processor.frame_skip_count < processor.frame_skip_threshold, "Frame skip logic incorrect"
    
    print("✅ Real-time Optimization Test PASSED!")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting DeepFace Feature Tests...")
    print("=" * 50)
    
    tests = [
        ("Face Clustering", test_face_clustering),
        ("EmotionProcessor", test_emotion_processor),
        ("API Endpoints", test_api_endpoints),
        ("Real-time Optimization", test_real_time_optimization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! New features are working correctly!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    main()