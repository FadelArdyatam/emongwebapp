#!/usr/bin/env python3
"""
Safe worker starter dengan error handling dan monitoring
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("worker-starter")

class SafeWorkerManager:
    def __init__(self):
        self.workers = {}
        self.running = True
        self.monitor_thread = None
        
    def start_worker(self, name, script_path):
        """Start individual worker with error handling"""
        try:
            logger.info(f"🚀 Starting {name} worker...")
            
            # Start worker process
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Store worker info
            self.workers[name] = {
                'process': process,
                'script': script_path,
                'started_at': datetime.now(),
                'restart_count': 0
            }
            
            # Wait a bit to check if it starts successfully
            time.sleep(1)
            
            if process.poll() is None:
                logger.info(f"✅ {name} worker started (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ {name} worker failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting {name} worker: {e}")
            return False
    
    def check_worker_health(self):
        """Check health of all workers"""
        healthy = 0
        total = len(self.workers)
        
        for name, info in self.workers.items():
            process = info['process']
            if process.poll() is None:
                healthy += 1
            else:
                logger.warning(f"⚠️ {name} worker is not running")
        
        return healthy, total
    
    def restart_dead_workers(self):
        """Restart dead workers"""
        for name, info in list(self.workers.items()):
            process = info['process']
            if process.poll() is not None:  # Process is dead
                logger.info(f"🔄 Restarting dead worker: {name}")
                
                # Increment restart count
                info['restart_count'] += 1
                
                # Don't restart too many times
                if info['restart_count'] > 5:
                    logger.error(f"❌ {name} worker failed too many times, giving up")
                    del self.workers[name]
                    continue
                
                # Restart worker
                if self.start_worker(name, info['script']):
                    logger.info(f"✅ {name} worker restarted successfully")
                else:
                    logger.error(f"❌ Failed to restart {name} worker")
    
    def monitor_workers(self):
        """Monitor workers in background thread"""
        while self.running:
            try:
                healthy, total = self.check_worker_health()
                
                if healthy < total:
                    logger.warning(f"⚠️ Only {healthy}/{total} workers are healthy")
                    self.restart_dead_workers()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")
                time.sleep(10)
    
    def start_all_workers(self):
        """Start all workers"""
        worker_configs = [
            ("emotion-stream", "workers/emotion_stream_worker.py"),
            ("notification", "workers/notification_worker.py"),
            ("report", "workers/report_worker.py"),
            ("scheduler", "workers/scheduler_worker.py"),
            ("image-processing", "workers/image_processing_worker.py")
        ]
        
        logger.info("🚀 Starting all EMONG workers...")
        
        # Start each worker
        for name, script in worker_configs:
            if os.path.exists(script):
                self.start_worker(name, script)
                time.sleep(1)  # Small delay between starts
            else:
                logger.error(f"❌ Worker script not found: {script}")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_workers, daemon=True)
        self.monitor_thread.start()
        
        logger.info("✅ All workers started and monitoring active")
    
    def stop_all_workers(self):
        """Stop all workers"""
        logger.info("🛑 Stopping all workers...")
        self.running = False
        
        for name, info in self.workers.items():
            try:
                process = info['process']
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ {name} worker stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping {name} worker: {e}")
        
        logger.info("✅ All workers stopped")
    
    def show_status(self):
        """Show worker status"""
        print("\n" + "="*60)
        print("📊 WORKER STATUS REPORT")
        print("="*60)
        
        healthy, total = self.check_worker_health()
        print(f"✅ Healthy: {healthy}/{total}")
        print(f"🕐 Uptime: {datetime.now() - self.start_time if hasattr(self, 'start_time') else 'N/A'}")
        
        print("\n📋 Worker Details:")
        print("-" * 60)
        
        for name, info in self.workers.items():
            process = info['process']
            started_at = info['started_at']
            restart_count = info['restart_count']
            
            status = "🟢 Running" if process.poll() is None else "🔴 Stopped"
            uptime = datetime.now() - started_at
            uptime_str = str(uptime).split('.')[0]
            
            print(f"{name:20} | {status:12} | {uptime_str:15} | Restarts: {restart_count}")
        
        print("="*60)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    worker_manager.stop_all_workers()
    sys.exit(0)

def main():
    global worker_manager
    worker_manager = SafeWorkerManager()
    
    # Set start time
    worker_manager.start_time = datetime.now()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all workers
        worker_manager.start_all_workers()
        
        # Show initial status
        worker_manager.show_status()
        
        # Keep running and show status periodically
        while True:
            time.sleep(60)  # Show status every minute
            worker_manager.show_status()
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        worker_manager.stop_all_workers()

if __name__ == '__main__':
    main()
