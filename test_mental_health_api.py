#!/usr/bin/env python3
"""
Test script untuk Mental Health API
"""

import requests
import json
import os

def test_mental_health_api():
    """Test Mental Health API endpoints"""
    print("🧠 Testing Mental Health API...")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Login first to get token
    login_data = {
        "username": "parent@example.com",  # Ganti dengan username parent yang valid
        "password": "password123"  # Ganti dengan password yang valid
    }
    
    try:
        # Login
        print("🔐 Logging in...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        token = login_response.json().get('access_token')
        if not token:
            print("❌ No access token received")
            return False
        
        print("✅ Login successful")
        
        # Get children list
        print("\n👶 Getting children list...")
        children_response = requests.get(
            f"{base_url}/api/parent/children",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if children_response.status_code != 200:
            print(f"❌ Failed to get children: {children_response.status_code}")
            return False
        
        children_data = children_response.json()
        children = children_data.get('children', [])
        
        if not children:
            print("⚠️ No children found")
            return False
        
        print(f"✅ Found {len(children)} children")
        
        # Test mental health analysis for first child
        first_child = children[0]
        child_id = first_child['id']
        child_name = first_child['name']
        
        print(f"\n🧠 Testing mental health analysis for child: {child_name} (ID: {child_id})")
        
        # Test mental health analysis
        print("\n📊 Testing mental health analysis...")
        analysis_response = requests.get(
            f"{base_url}/mental-health/analysis/{child_id}?days=7",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if analysis_response.status_code == 200:
            analysis_data = analysis_response.json()
            print("✅ Mental health analysis successful")
            print(f"   Status: {analysis_data.get('status')}")
            print(f"   Risk Level: {analysis_data.get('risk_level', 'unknown')}")
            print(f"   Total Detections: {analysis_data.get('total_detections', 0)}")
            print(f"   Emotional Score: {analysis_data.get('weighted_emotional_score', 0)}")
            print(f"   Recommendations: {len(analysis_data.get('recommendations', []))}")
        else:
            print(f"❌ Mental health analysis failed: {analysis_response.status_code}")
            print(f"   Response: {analysis_response.text}")
        
        # Test mental health progress
        print("\n📈 Testing mental health progress...")
        progress_response = requests.get(
            f"{base_url}/mental-health/progress/{child_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            print("✅ Mental health progress successful")
            print(f"   Status: {progress_data.get('status')}")
            if progress_data.get('status') == 'success':
                print(f"   Current Score: {progress_data.get('current_score', 0)}")
                print(f"   Progress: {progress_data.get('progress', 0)}")
                print(f"   Trend: {progress_data.get('trend', 'unknown')}")
        else:
            print(f"❌ Mental health progress failed: {progress_response.status_code}")
            print(f"   Response: {progress_response.text}")
        
        # Test mental health recommendations
        print("\n💡 Testing mental health recommendations...")
        recommendations_response = requests.get(
            f"{base_url}/mental-health/recommendations/{child_id}?days=7",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if recommendations_response.status_code == 200:
            recommendations_data = recommendations_response.json()
            print("✅ Mental health recommendations successful")
            print(f"   Status: {recommendations_data.get('status')}")
            print(f"   Risk Level: {recommendations_data.get('risk_level', 'unknown')}")
            print(f"   Recommendations: {len(recommendations_data.get('recommendations', []))}")
            print(f"   Interventions: {len(recommendations_data.get('interventions', []))}")
        else:
            print(f"❌ Mental health recommendations failed: {recommendations_response.status_code}")
            print(f"   Response: {recommendations_response.text}")
        
        print("\n✅ Mental Health API test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == '__main__':
    success = test_mental_health_api()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")

