#!/usr/bin/env python3
"""
Script untuk monitoring worker status secara real-time
"""

import redis
import json
import time
import os
from datetime import datetime

def check_redis_connection():
    """Check Redis connection"""
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.Redis.from_url(redis_url, decode_responses=True)
        r.ping()
        return True, r
    except Exception as e:
        return False, str(e)

def check_worker_streams(r):
    """Check Redis streams for worker activity"""
    streams = [
        'emotion-events',
        'notification-events', 
        'report-events',
        'scheduler-events',
        'image-processing-events'
    ]
    
    print("📊 Redis Streams Status:")
    print("-" * 40)
    
    for stream in streams:
        try:
            info = r.xinfo_stream(stream)
            length = info.get('length', 0)
            groups = info.get('groups', 0)
            print(f"{stream:25} | Messages: {length:6} | Groups: {groups}")
        except Exception as e:
            print(f"{stream:25} | Error: {str(e)[:30]}")
    
    print()

def check_worker_groups(r):
    """Check worker groups and pending messages"""
    streams = [
        'emotion-events',
        'notification-events',
        'report-events', 
        'scheduler-events',
        'image-processing-events'
    ]
    
    print("👥 Worker Groups Status:")
    print("-" * 40)
    
    for stream in streams:
        try:
            # Get stream groups
            groups = r.xinfo_groups(stream)
            for group in groups:
                group_name = group['name']
                consumers = group['consumers']
                pending = group['pending']
                last_delivered = group['last-delivered-id']
                
                print(f"{stream:20} | {group_name:15} | Consumers: {consumers:2} | Pending: {pending:3}")
                
                # Check pending messages
                if pending > 0:
                    pending_msgs = r.xpending_range(stream, group_name, '-', '+', 5)
                    print(f"{'':20} | {'':15} | Pending details: {len(pending_msgs)} messages")
                    
        except Exception as e:
            print(f"{stream:20} | Error: {str(e)[:30]}")
    
    print()

def check_cache_status(r):
    """Check cache status"""
    print("🗄️ Cache Status:")
    print("-" * 40)
    
    try:
        # Check dashboard cache keys
        dashboard_keys = r.keys("dashboard:*")
        print(f"Dashboard cache keys: {len(dashboard_keys)}")
        
        # Check worker result keys
        result_keys = r.keys("*:result:*")
        print(f"Worker result keys: {len(result_keys)}")
        
        # Check notification keys
        notification_keys = r.keys("notifications:*")
        print(f"Notification keys: {len(notification_keys)}")
        
        # Show some sample keys
        if dashboard_keys:
            print(f"Sample dashboard key: {dashboard_keys[0]}")
        if result_keys:
            print(f"Sample result key: {result_keys[0]}")
            
    except Exception as e:
        print(f"Error checking cache: {e}")
    
    print()

def main():
    """Main monitoring function"""
    print("🔍 EMONG Worker Monitor")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check Redis connection
    redis_ok, redis_client = check_redis_connection()
    if not redis_ok:
        print(f"❌ Redis connection failed: {redis_client}")
        return 1
    
    print("✅ Redis connection successful")
    print()
    
    # Check worker streams
    check_worker_streams(redis_client)
    
    # Check worker groups
    check_worker_groups(redis_client)
    
    # Check cache status
    check_cache_status(redis_client)
    
    print("✅ Monitoring complete")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
