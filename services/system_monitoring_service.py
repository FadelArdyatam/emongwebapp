"""
System Monitoring Service untuk real-time monitoring dan alerting
"""
import psutil
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
import os
import json

logger = logging.getLogger(__name__)

class SystemMonitoringService:
    def __init__(self):
        self.monitoring_active = False
        self.monitoring_thread = None
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 data points
        self.alerts = deque(maxlen=100)
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'response_time': 2.0,
            'error_rate': 5.0
        }
        self.start_time = time.time()
        
    def start_monitoring(self):
        """Start system monitoring in background thread"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Sleep for 5 seconds
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
            top_processes = sorted(processes, key=lambda x: x.info.get('cpu_percent', 0), reverse=True)[:5]
            
            # System uptime
            uptime = time.time() - self.start_time
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': uptime,
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'usage_percent': memory.percent,
                    'swap_total_gb': round(swap.total / (1024**3), 2),
                    'swap_used_gb': round(swap.used / (1024**3), 2),
                    'swap_percent': swap.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'usage_percent': round((disk.used / disk.total) * 100, 2),
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': {
                    'total_count': len(processes),
                    'top_cpu': [
                        {
                            'pid': p.info.get('pid'),
                            'name': p.info.get('name'),
                            'cpu_percent': p.info.get('cpu_percent', 0)
                        }
                        for p in top_processes
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        try:
            if 'error' in metrics:
                return
                
            alerts = []
            
            # CPU alert
            if metrics['cpu']['usage_percent'] > self.alert_thresholds['cpu_usage']:
                alerts.append({
                    'type': 'cpu_high',
                    'severity': 'warning',
                    'message': f"CPU usage high: {metrics['cpu']['usage_percent']:.1f}%",
                    'value': metrics['cpu']['usage_percent'],
                    'threshold': self.alert_thresholds['cpu_usage']
                })
            
            # Memory alert
            if metrics['memory']['usage_percent'] > self.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'memory_high',
                    'severity': 'warning',
                    'message': f"Memory usage high: {metrics['memory']['usage_percent']:.1f}%",
                    'value': metrics['memory']['usage_percent'],
                    'threshold': self.alert_thresholds['memory_usage']
                })
            
            # Disk alert
            if metrics['disk']['usage_percent'] > self.alert_thresholds['disk_usage']:
                alerts.append({
                    'type': 'disk_high',
                    'severity': 'critical',
                    'message': f"Disk usage high: {metrics['disk']['usage_percent']:.1f}%",
                    'value': metrics['disk']['usage_percent'],
                    'threshold': self.alert_thresholds['disk_usage']
                })
            
            # Add alerts to history
            for alert in alerts:
                alert['timestamp'] = metrics['timestamp']
                self.alerts.append(alert)
                logger.warning(f"System alert: {alert['message']}")
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        if not self.metrics_history:
            return {'error': 'No metrics available'}
        
        latest = self.metrics_history[-1]
        
        # Calculate trends
        trends = self._calculate_trends()
        
        return {
            'current': latest,
            'trends': trends,
            'alerts': list(self.alerts)[-10:],  # Last 10 alerts
            'monitoring_active': self.monitoring_active
        }
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate trends from historical data"""
        if len(self.metrics_history) < 2:
            return {}
        
        recent = list(self.metrics_history)[-10:]  # Last 10 data points
        
        try:
            # CPU trend
            cpu_values = [m['cpu']['usage_percent'] for m in recent if 'cpu' in m]
            cpu_trend = self._calculate_trend_direction(cpu_values)
            
            # Memory trend
            memory_values = [m['memory']['usage_percent'] for m in recent if 'memory' in m]
            memory_trend = self._calculate_trend_direction(memory_values)
            
            # Disk trend
            disk_values = [m['disk']['usage_percent'] for m in recent if 'disk' in m]
            disk_trend = self._calculate_trend_direction(disk_values)
            
            return {
                'cpu': cpu_trend,
                'memory': memory_trend,
                'disk': disk_trend
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {}
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return 'stable'
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        diff = second_avg - first_avg
        
        if diff > 5:
            return 'increasing'
        elif diff < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_historical_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get historical metrics for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        historical = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) >= cutoff_time
        ]
        
        if not historical:
            return {'error': 'No historical data available'}
        
        # Calculate averages
        cpu_avg = sum(m['cpu']['usage_percent'] for m in historical) / len(historical)
        memory_avg = sum(m['memory']['usage_percent'] for m in historical) / len(historical)
        disk_avg = sum(m['disk']['usage_percent'] for m in historical) / len(historical)
        
        return {
            'period_hours': hours,
            'data_points': len(historical),
            'averages': {
                'cpu_percent': round(cpu_avg, 2),
                'memory_percent': round(memory_avg, 2),
                'disk_percent': round(disk_avg, 2)
            },
            'metrics': historical
        }
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary"""
        if not self.alerts:
            return {'total': 0, 'by_type': {}, 'by_severity': {}}
        
        alerts = list(self.alerts)
        
        # Count by type
        by_type = {}
        for alert in alerts:
            alert_type = alert['type']
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
        
        # Count by severity
        by_severity = {}
        for alert in alerts:
            severity = alert['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total': len(alerts),
            'by_type': by_type,
            'by_severity': by_severity,
            'recent_alerts': alerts[-10:]
        }
    
    def update_alert_thresholds(self, new_thresholds: Dict[str, float]):
        """Update alert thresholds"""
        self.alert_thresholds.update(new_thresholds)
        logger.info(f"Alert thresholds updated: {new_thresholds}")
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
        logger.info("All alerts cleared")

# Global instance
system_monitoring_service = SystemMonitoringService()