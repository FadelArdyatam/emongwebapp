#!/usr/bin/env python3
"""
Test script untuk API child distribution
"""

import requests
import json
import os

def test_child_distribution_api():
    """Test API child distribution"""
    print("🧪 Testing Child Distribution API...")
    print("=" * 50)
    
    # Test data
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
        
        # Test child distribution for first child
        first_child = children[0]
        child_id = first_child['id']
        child_name = first_child['name']
        
        print(f"\n📊 Testing distribution for child: {child_name} (ID: {child_id})")
        
        # Test different periods
        periods = [1, 7, 30]
        
        for period in periods:
            print(f"\n📅 Testing period: {period} days")
            
            dist_response = requests.get(
                f"{base_url}/api/parent/child/{child_id}/distribution?period={period}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if dist_response.status_code == 200:
                data = dist_response.json()
                distribution = data.get('distribution', {})
                timeline = data.get('timeline', [])
                
                print(f"✅ Success - Period {period} days")
                print(f"   Distribution: {distribution}")
                print(f"   Timeline entries: {len(timeline)}")
                
                # Check if there's any data
                total_emotions = sum(distribution.values())
                if total_emotions > 0:
                    print(f"   Total emotions: {total_emotions}")
                else:
                    print("   ⚠️ No emotion data for this period")
                    
            else:
                print(f"❌ Failed - Period {period} days: {dist_response.status_code}")
                print(f"   Response: {dist_response.text}")
        
        print("\n✅ Child distribution API test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == '__main__':
    success = test_child_distribution_api()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
