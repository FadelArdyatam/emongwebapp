#!/usr/bin/env python3
"""
Script untuk testing API guru melihat detail sesi
"""

import requests
import json
import time
import sys
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def test_login(username, password):
    """Test login untuk mendapatkan token"""
    print(f"\n🔐 Testing login untuk {username}...")
    
    response = requests.post(f"{API_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"✅ Login berhasil untuk {username}")
        return token
    else:
        print(f"❌ Login gagal untuk {username}: {response.text}")
        return None

def test_guru_sessions(guru_token):
    """Test API guru melihat daftar sesi"""
    print(f"\n📋 Testing guru sessions list...")
    
    headers = {"Authorization": f"Bearer {guru_token}"}
    response = requests.get(f"{API_URL}/guru/sessions", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        sessions = data.get('sessions', [])
        print(f"✅ Guru sessions list berhasil diakses")
        print(f"   - Total sesi: {data.get('total_sessions', 0)}")
        print(f"   - Sesi aktif: {data.get('active_sessions', 0)}")
        
        for session in sessions[:3]:  # Tampilkan 3 sesi pertama
            print(f"   - Sesi {session['id']}: {session['session_name']}")
            print(f"     Status: {session['status']}")
            print(f"     Total deteksi: {session.get('total_detections', 0)}")
            print(f"     Siswa unik: {session.get('unique_students', 0)}")
            print(f"     Emosi dominan: {session.get('dominant_emotion', 'N/A')}")
        
        return sessions
    else:
        print(f"❌ Gagal akses guru sessions: {response.text}")
        return []

def test_guru_session_detail(guru_token, session_id):
    """Test API guru melihat detail sesi"""
    print(f"\n🔍 Testing guru session detail untuk ID {session_id}...")
    
    headers = {"Authorization": f"Bearer {guru_token}"}
    response = requests.get(f"{API_URL}/guru/sessions/{session_id}/detail", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Guru session detail berhasil diakses")
        
        session = data.get('session', {})
        print(f"   - Nama sesi: {session.get('session_name', 'N/A')}")
        print(f"   - Status: {session.get('status', 'N/A')}")
        print(f"   - Mulai: {session.get('start_time', 'N/A')}")
        print(f"   - Selesai: {session.get('end_time', 'N/A')}")
        
        print(f"   - Total deteksi: {data.get('total_logs', 0)}")
        print(f"   - Total siswa: {data.get('total_students', 0)}")
        
        # Tampilkan siswa yang terdeteksi
        students = data.get('students_detected', [])
        if students:
            print(f"   - Siswa yang terdeteksi:")
            for student in students:
                print(f"     * {student['name']} ({student['student_code']}) - {student['detection_count']} deteksi")
        
        # Tampilkan statistik emosi
        emotion_stats = data.get('emotion_stats', {})
        if emotion_stats:
            print(f"   - Statistik emosi:")
            for emotion, stats in emotion_stats.items():
                print(f"     * {emotion}: {stats['count']} deteksi (avg confidence: {stats['avg_confidence']:.2f})")
        
        return data
    else:
        print(f"❌ Gagal akses guru session detail: {response.text}")
        return None

def test_create_session(guru_token, session_name="Test Guru Session"):
    """Test membuat session baru"""
    print(f"\n📝 Testing create session...")
    
    headers = {"Authorization": f"Bearer {guru_token}"}
    response = requests.post(f"{API_URL}/sessions", json={
        "session_name": session_name,
        "student_id": 0,  # Session kelas
        "notes": "Test session untuk guru"
    }, headers=headers)
    
    if response.status_code == 201:
        session_data = response.json()
        print(f"✅ Session berhasil dibuat: {session_data['session_name']} (ID: {session_data['id']})")
        return session_data
    else:
        print(f"❌ Gagal membuat session: {response.text}")
        return None

def test_guru_api_flow():
    """Test alur API guru"""
    print("🧪 Testing Guru API Flow")
    print("=" * 50)
    
    # Test login guru
    guru_token = test_login("guru1@school.com", "guru123")
    if not guru_token:
        print("❌ Tidak bisa melanjutkan tanpa token guru")
        return
    
    # Test daftar sesi guru
    sessions = test_guru_sessions(guru_token)
    
    # Test detail sesi jika ada
    if sessions:
        first_session = sessions[0]
        session_id = first_session['id']
        test_guru_session_detail(guru_token, session_id)
    
    # Buat session baru
    new_session = test_create_session(guru_token, f"Test Guru Session {int(time.time())}")
    if new_session:
        session_id = new_session['id']
        print(f"\n⏳ Menunggu 2 detik...")
        time.sleep(2)
        
        # Test detail session baru
        test_guru_session_detail(guru_token, session_id)
    
    print(f"\n✅ Testing selesai!")
    print(f"📝 Periksa log server untuk debugging info")

if __name__ == "__main__":
    test_guru_api_flow()