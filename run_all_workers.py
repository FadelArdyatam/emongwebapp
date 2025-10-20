#!/usr/bin/env python3
"""
Script untuk menjalankan semua worker secara bersamaan
"""

import os
import sys
import time
import signal
import logging
import threading
import subprocess
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("worker-manager")

# Worker configurations
WORKERS = [
    {
        'name': 'emotion-stream',
        'script': 'workers/emotion_stream_worker.py',
        'description': 'Process emotion detection data'
    },
    {
        'name': 'notification',
        'script': 'workers/notification_worker.py', 
        'description': 'Send email and push notifications'
    },
    {
        'name': 'report',
        'script': 'workers/report_worker.py',
        'description': 'Generate PDF/Excel reports'
    },
    {
        'name': 'scheduler',
        'script': 'workers/scheduler_worker.py',
        'description': 'Handle scheduled tasks'
    },
    {
        'name': 'image-processing',
        'script': 'workers/image_processing_worker.py',
        'description': 'Process images (resize, compress, crop)'
    }
]

class WorkerManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.start_time = datetime.now()
        
    def start_worker(self, worker_config):
        """Start individual worker"""
        try:
            worker_name = worker_config['name']
            script_path = worker_config['script']
            
            logger.info(f"Starting {worker_name} worker...")
            
            # Start worker process
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes[worker_name] = {
                'process': process,
                'config': worker_config,
                'started_at': datetime.now()
            }
            
            logger.info(f"✅ {worker_name} worker started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start {worker_name} worker: {e}")
            return False
    
    def stop_worker(self, worker_name):
        """Stop individual worker"""
        if worker_name in self.processes:
            try:
                process = self.processes[worker_name]['process']
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"✅ {worker_name} worker stopped")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to stop {worker_name} worker: {e}")
                return False
        return False
    
    def stop_all_workers(self):
        """Stop all workers"""
        logger.info("🛑 Stopping all workers...")
        self.running = False
        
        for worker_name in list(self.processes.keys()):
            self.stop_worker(worker_name)
        
        logger.info("✅ All workers stopped")
    
    def check_worker_health(self):
        """Check health of all workers"""
        healthy_workers = 0
        total_workers = len(self.processes)
        
        for worker_name, worker_info in self.processes.items():
            process = worker_info['process']
            if process.poll() is None:  # Process is still running
                healthy_workers += 1
            else:
                logger.warning(f"⚠️ {worker_name} worker is not running")
        
        return healthy_workers, total_workers
    
    def restart_worker(self, worker_name):
        """Restart individual worker"""
        logger.info(f"🔄 Restarting {worker_name} worker...")
        self.stop_worker(worker_name)
        time.sleep(2)
        return self.start_worker(self.processes[worker_name]['config'])
    
    def monitor_workers(self):
        """Monitor worker health and restart if needed"""
        while self.running:
            try:
                healthy, total = self.check_worker_health()
                
                if healthy < total:
                    logger.warning(f"⚠️ Only {healthy}/{total} workers are healthy")
                    
                    # Restart unhealthy workers
                    for worker_name, worker_info in self.processes.items():
                        process = worker_info['process']
                        if process.poll() is not None:  # Process is dead
                            logger.info(f"🔄 Restarting dead worker: {worker_name}")
                            self.restart_worker(worker_name)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")
                time.sleep(30)
    
    def start_all_workers(self):
        """Start all workers"""
        logger.info("🚀 Starting all workers...")
        
        # Start each worker
        for worker_config in WORKERS:
            self.start_worker(worker_config)
            time.sleep(1)  # Small delay between starts
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_workers, daemon=True)
        monitor_thread.start()
        
        logger.info("✅ All workers started and monitoring active")
    
    def show_status(self):
        """Show status of all workers"""
        print("\n" + "="*60)
        print("📊 WORKER STATUS REPORT")
        print("="*60)
        uptime = datetime.now() - self.start_time
        print(f"🕐 Uptime: {uptime}")
        print(f"📈 Total Workers: {len(self.processes)}")
        
        healthy, total = self.check_worker_health()
        print(f"✅ Healthy: {healthy}/{total}")
        
        print("\n📋 Worker Details:")
        print("-" * 60)
        
        for worker_name, worker_info in self.processes.items():
            process = worker_info['process']
            config = worker_info['config']
            started_at = worker_info['started_at']
            
            status = "🟢 Running" if process.poll() is None else "🔴 Stopped"
            uptime = datetime.now() - started_at
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            print(f"{worker_name:15} | {status:12} | {uptime_str:15} | {config['description']}")
        
        print("="*60)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    worker_manager.stop_all_workers()
    sys.exit(0)

def main():
    global worker_manager
    worker_manager = WorkerManager()
    
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
