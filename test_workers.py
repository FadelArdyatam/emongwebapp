#!/usr/bin/env python3
"""
Test script untuk memastikan semua worker berjalan dengan baik
"""

import subprocess
import time
import sys
import os

def test_worker(worker_name, script_path):
    """Test individual worker"""
    print(f"🧪 Testing {worker_name} worker...")
    
    try:
        # Start worker process
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for startup
        time.sleep(2)
        
        # Check if still running
        if process.poll() is None:
            print(f"✅ {worker_name} worker started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {worker_name} worker failed to start")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing {worker_name} worker: {e}")
        return False

def main():
    """Test all workers"""
    print("🚀 Testing all EMONG workers...")
    print("=" * 50)
    
    workers = [
        ("emotion-stream", "workers/emotion_stream_worker.py"),
        ("notification", "workers/notification_worker.py"),
        ("report", "workers/report_worker.py"),
        ("scheduler", "workers/scheduler_worker.py"),
        ("image-processing", "workers/image_processing_worker.py")
    ]
    
    results = []
    
    for worker_name, script_path in workers:
        if os.path.exists(script_path):
            success = test_worker(worker_name, script_path)
            results.append((worker_name, success))
        else:
            print(f"❌ {worker_name} worker script not found: {script_path}")
            results.append((worker_name, False))
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for worker_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{worker_name:20} | {status}")
        if success:
            passed += 1
    
    print("=" * 50)
    print(f"Total: {passed}/{total} workers passed")
    
    if passed == total:
        print("🎉 All workers are working correctly!")
        return 0
    else:
        print("⚠️ Some workers have issues. Check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
