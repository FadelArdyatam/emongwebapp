#!/usr/bin/env python3
"""
Script untuk testing sistem notifikasi session ke parent
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def test_login(role, username, password):
    """Test login untuk mendapatkan token"""
    print(f"\n🔐 Testing login untuk {role}...")
    
    response = requests.post(f"{API_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"✅ Login berhasil untuk {role}")
        return token
    else:
        print(f"❌ Login gagal untuk {role}: {response.text}")
        return None

def test_create_session(guru_token, session_name="Test Session"):
    """Test membuat session baru"""
    print(f"\n📝 Testing create session...")
    
    headers = {"Authorization": f"Bearer {guru_token}"}
    response = requests.post(f"{API_URL}/sessions", json={
        "session_name": session_name,
        "student_id": 0,  # Session kelas
        "notes": "Test session untuk debugging"
    }, headers=headers)
    
    if response.status_code == 201:
        session_data = response.json()
        print(f"✅ Session berhasil dibuat: {session_data['session_name']} (ID: {session_data['id']})")
        return session_data
    else:
        print(f"❌ Gagal membuat session: {response.text}")
        return None

def test_stop_session(guru_token, session_id):
    """Test menghentikan session"""
    print(f"\n🛑 Testing stop session...")
    
    headers = {"Authorization": f"Bearer {guru_token}"}
    response = requests.post(f"{API_URL}/sessions/{session_id}/stop", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Session berhasil dihentikan")
        return True
    else:
        print(f"❌ Gagal menghentikan session: {response.text}")
        return False

def test_parent_dashboard(parent_token):
    """Test akses dashboard parent"""
    print(f"\n📊 Testing parent dashboard...")
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    response = requests.get(f"{API_URL}/dashboard/parent/stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard parent berhasil diakses")
        print(f"   - Total anak: {data.get('total_children', 0)}")
        print(f"   - Rata-rata emosi: {data.get('avg_emotion', 'N/A')}")
        print(f"   - Sesi minggu ini: {data.get('weekly_sessions', 0)}")
        return True
    else:
        print(f"❌ Gagal akses dashboard parent: {response.text}")
        return False

def main():
    print("🧪 Testing Sistem Notifikasi Session ke Parent")
    print("=" * 50)
    
    # Test login guru
    guru_token = test_login("guru", "guru1", "password123")
    if not guru_token:
        print("❌ Tidak bisa melanjutkan tanpa token guru")
        return
    
    # Test login parent
    parent_token = test_login("parent", "parent1", "password123")
    if not parent_token:
        print("❌ Tidak bisa melanjutkan tanpa token parent")
        return
    
    # Test dashboard parent
    test_parent_dashboard(parent_token)
    
    # Test create session
    session = test_create_session(guru_token, "Debug Session " + str(int(time.time())))
    if not session:
        print("❌ Tidak bisa melanjutkan tanpa session")
        return
    
    print(f"\n⏳ Menunggu 3 detik untuk melihat notifikasi...")
    time.sleep(3)
    
    # Test stop session
    test_stop_session(guru_token, session['id'])
    
    print(f"\n⏳ Menunggu 3 detik untuk melihat notifikasi stop...")
    time.sleep(3)
    
    print(f"\n✅ Testing selesai!")
    print(f"📝 Periksa log server untuk melihat notifikasi yang dikirim")
    print(f"📱 Periksa browser parent untuk melihat notifikasi yang diterima")

if __name__ == "__main__":
    main()