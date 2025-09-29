#!/usr/bin/env python3
"""
Script untuk testing kalkulasi sesi per anak
"""

import requests
import json
import time
import sys
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def test_login(role, username, password):
    """Test login untuk mendapatkan token"""
    print(f"\n🔐 Testing login untuk {role}...")
    
    response = requests.post(f"{API_URL}/auth/login", json={
        "username": "guru1@school.com",
        "password": "guru123"
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"✅ Login berhasil untuk {role}")
        return token
    else:
        print(f"❌ Login gagal untuk {role}: {response.text}")
        return None

def test_dashboard_stats(parent_token):
    """Test dashboard stats untuk melihat kalkulasi sesi"""
    print(f"\n📊 Testing dashboard stats...")
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    response = requests.get(f"{API_URL}/dashboard/parent/stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard stats berhasil diakses")
        print(f"   - Total anak: {data.get('total_children', 0)}")
        print(f"   - Sesi minggu ini: {data.get('weekly_sessions', 0)}")
        print(f"   - Rata-rata emosi: {data.get('avg_emotion', 'N/A')}")
        print(f"   - Trend positif: {data.get('positive_trend', 0)}%")
        return data
    else:
        print(f"❌ Gagal akses dashboard stats: {response.text}")
        return None

def test_children_list(parent_token):
    """Test children list untuk melihat sesi per anak"""
    print(f"\n👶 Testing children list...")
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    response = requests.get(f"{API_URL}/parent/children", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        children = data.get('children', [])
        print(f"✅ Children list berhasil diakses ({len(children)} anak)")
        
        for child in children:
            print(f"   - {child.get('name', 'N/A')}: {child.get('weekly_sessions', 0)} sesi minggu ini")
        
        return children
    else:
        print(f"❌ Gagal akses children list: {response.text}")
        return []

def test_child_details(parent_token, child_id):
    """Test child details untuk melihat sesi spesifik"""
    print(f"\n🔍 Testing child details untuk ID {child_id}...")
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    response = requests.get(f"{API_URL}/parent/children/{child_id}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Child details berhasil diakses")
        print(f"   - Nama: {data.get('name', 'N/A')}")
        print(f"   - Sesi minggu ini: {data.get('weekly_sessions', 0)}")
        print(f"   - Total deteksi: {data.get('total_detections', 0)}")
        print(f"   - Emosi terakhir: {data.get('last_emotion', 'N/A')}")
        print(f"   - Sesi terakhir: {data.get('last_session', 'N/A')}")
        return data
    else:
        print(f"❌ Gagal akses child details: {response.text}")
        return None

def test_create_session(guru_token, session_name="Test Session Calculation"):
    """Test membuat session baru"""
    print(f"\n📝 Testing create session...")
    
    headers = {"Authorization": f"Bearer {guru_token}"}
    response = requests.post(f"{API_URL}/sessions", json={
        "session_name": session_name,
        "student_id": 0,  # Session kelas
        "notes": "Test session untuk kalkulasi"
    }, headers=headers)
    
    if response.status_code == 201:
        session_data = response.json()
        print(f"✅ Session berhasil dibuat: {session_data['session_name']} (ID: {session_data['id']})")
        return session_data
    else:
        print(f"❌ Gagal membuat session: {response.text}")
        return None

def test_session_calculation_flow():
    """Test alur kalkulasi sesi"""
    print("🧪 Testing Session Calculation Flow")
    print("=" * 50)
    
    # Test login
    guru_token = test_login("guru", "guru1", "password123")
    if not guru_token:
        print("❌ Tidak bisa melanjutkan tanpa token guru")
        return
    
    parent_token = test_login("parent", "parent1", "password123")
    if not parent_token:
        print("❌ Tidak bisa melanjutkan tanpa token parent")
        return
    
    # Test dashboard stats sebelum session
    print(f"\n📊 Dashboard stats SEBELUM session:")
    stats_before = test_dashboard_stats(parent_token)
    
    # Test children list sebelum session
    print(f"\n👶 Children list SEBELUM session:")
    children_before = test_children_list(parent_token)
    
    # Buat session baru
    session = test_create_session(guru_token, f"Test Session {int(time.time())}")
    if not session:
        print("❌ Tidak bisa melanjutkan tanpa session")
        return
    
    print(f"\n⏳ Menunggu 3 detik untuk notifikasi...")
    time.sleep(3)
    
    # Test dashboard stats setelah session
    print(f"\n📊 Dashboard stats SETELAH session:")
    stats_after = test_dashboard_stats(parent_token)
    
    # Test children list setelah session
    print(f"\n👶 Children list SETELAH session:")
    children_after = test_children_list(parent_token)
    
    # Bandingkan hasil
    print(f"\n📈 PERBANDINGAN HASIL:")
    if stats_before and stats_after:
        sessions_before = stats_before.get('weekly_sessions', 0)
        sessions_after = stats_after.get('weekly_sessions', 0)
        print(f"   - Sesi sebelum: {sessions_before}")
        print(f"   - Sesi setelah: {sessions_after}")
        print(f"   - Peningkatan: {sessions_after - sessions_before}")
    
    # Test child details untuk anak pertama
    if children_after:
        first_child = children_after[0]
        child_id = first_child.get('id')
        if child_id:
            test_child_details(parent_token, child_id)
    
    print(f"\n✅ Testing selesai!")
    print(f"📝 Periksa log server untuk debugging info")

if __name__ == "__main__":
    test_session_calculation_flow()