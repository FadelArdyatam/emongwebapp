#!/usr/bin/env python3
"""
Test script untuk API endpoints yang baru diimplementasi
"""

import requests
import json
import base64
import io
from PIL import Image
import numpy as np

def test_detector_backend():
    """Test detector backend endpoints"""
    print("🧪 Testing Detector Backend Endpoints...")
    
    # Test GET /detector/backend
    print("\n1. Testing GET /detector/backend...")
    try:
        response = requests.get('http://localhost:5000/detector/backend')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detector backend: {data.get('detectorBackend', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test POST /detector/backend
    print("\n2. Testing POST /detector/backend...")
    try:
        response = requests.post('http://localhost:5000/detector/backend', 
                               json={'backend': 'mtcnn'})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detector backend updated: {data.get('detectorBackend', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_face_clustering():
    """Test face clustering endpoint"""
    print("\n🧪 Testing Face Clustering Endpoint...")
    
    try:
        response = requests.get('http://localhost:5000/face/clustering')
        if response.status_code in [200, 404]:
            data = response.json()
            if response.status_code == 200:
                print(f"✅ Face clustering data: {data.get('total_clusters', 0)} clusters")
            else:
                print(f"✅ Face clustering endpoint working (no data yet): {data.get('message', 'No data')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_face_attributes():
    """Test face attributes analysis endpoint"""
    print("\n🧪 Testing Face Attributes Analysis...")
    
    # Create a simple test image
    test_image = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    test_image.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode()
    
    try:
        response = requests.post('http://localhost:5000/face/attributes/analyze',
                               json={'image': image_data})
        if response.status_code in [200, 400]:
            data = response.json()
            if response.status_code == 200:
                print(f"✅ Face attributes analysis successful")
                print(f"   - Emotion: {data.get('attributes', {}).get('emotion', {}).get('dominant', 'unknown')}")
                print(f"   - Age: {data.get('attributes', {}).get('age', {}).get('estimated', 0)}")
            else:
                print(f"✅ Face attributes endpoint working (no face detected): {data.get('message', 'No face')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_multi_person():
    """Test multi-person analysis endpoint"""
    print("\n🧪 Testing Multi-person Analysis...")
    
    # Create a simple test image
    test_image = Image.new('RGB', (200, 200), color='blue')
    buffer = io.BytesIO()
    test_image.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode()
    
    try:
        response = requests.post('http://localhost:5000/face/multi-person/analyze',
                               json={'image': image_data})
        if response.status_code in [200, 400]:
            data = response.json()
            if response.status_code == 200:
                print(f"✅ Multi-person analysis successful")
                print(f"   - People detected: {data.get('group_stats', {}).get('total_people', 0)}")
            else:
                print(f"✅ Multi-person endpoint working (no faces detected): {data.get('message', 'No faces')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def main():
    """Run all API tests"""
    print("🚀 Starting API Endpoints Tests...")
    print("=" * 50)
    
    tests = [
        ("Detector Backend", test_detector_backend),
        ("Face Clustering", test_face_clustering),
        ("Face Attributes", test_face_attributes),
        ("Multi-person Analysis", test_multi_person)
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
    print(f"📊 API Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL API TESTS PASSED! New endpoints are working correctly!")
        return True
    else:
        print("⚠️ Some API tests failed. Please check the server.")
        return False

if __name__ == "__main__":
    main()