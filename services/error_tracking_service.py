"""
Error Tracking & Logging Service untuk monitoring dan debugging
"""
import logging
import traceback
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import os
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ErrorEvent:
    """Data class untuk error event"""
    timestamp: str
    error_type: str
    error_message: str
    stack_trace: str
    user_id: Optional[int]
    endpoint: Optional[str]
    request_data: Optional[Dict]
    severity: str  # 'low', 'medium', 'high', 'critical'
    component: str  # 'api', 'emotion_detection', 'database', 'websocket', etc.
    session_id: Optional[str]
    student_id: Optional[int]
    additional_context: Optional[Dict]

class ErrorTrackingService:
    def __init__(self, max_errors_in_memory=1000):
        self.max_errors_in_memory = max_errors_in_memory
        self.errors = deque(maxlen=max_errors_in_memory)
        self.error_counts = defaultdict(int)
        self.error_patterns = defaultdict(list)
        self.lock = threading.Lock()
        
        # Error severity levels
        self.severity_levels = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        # Component error thresholds
        self.component_thresholds = {
            'emotion_detection': {'medium': 10, 'high': 25, 'critical': 50},
            'database': {'medium': 5, 'high': 15, 'critical': 30},
            'api': {'medium': 20, 'high': 50, 'critical': 100},
            'websocket': {'medium': 15, 'high': 35, 'critical': 70}
        }

    def log_error(self, error: Exception, component: str, 
                  user_id: Optional[int] = None, endpoint: Optional[str] = None,
                  request_data: Optional[Dict] = None, session_id: Optional[str] = None,
                  student_id: Optional[int] = None, additional_context: Optional[Dict] = None,
                  severity: str = 'medium') -> str:
        """Log an error event with improved error handling"""
        try:
            # Sanitize request data to avoid logging sensitive information
            sanitized_request_data = None
            if request_data:
                sanitized_request_data = self._sanitize_request_data(request_data)
            
            error_event = ErrorEvent(
                timestamp=datetime.utcnow().isoformat(),
                error_type=type(error).__name__,
                error_message=str(error)[:500],  # Limit message length
                stack_trace=traceback.format_exc(),
                user_id=user_id,
                endpoint=endpoint,
                request_data=sanitized_request_data,
                severity=severity,
                component=component,
                session_id=session_id,
                student_id=student_id,
                additional_context=additional_context
            )
            
            with self.lock:
                # Add to memory store
                self.errors.append(error_event)
                
                # Update counters
                error_key = f"{component}:{type(error).__name__}"
                self.error_counts[error_key] += 1
                
                # Track patterns (keep only last 100 per component)
                if len(self.error_patterns[component]) >= 100:
                    self.error_patterns[component] = self.error_patterns[component][-50:]
                
                self.error_patterns[component].append({
                    'timestamp': error_event.timestamp,
                    'error_type': error_event.error_type,
                    'severity': severity
                })
                
                # Check for alert conditions
                self._check_alert_conditions(component, error_key)
            
            # Log to standard logger with structured logging
            logger.error(f"Error in {component}: {str(error)}", extra={
                'error_type': type(error).__name__,
                'component': component,
                'user_id': user_id,
                'endpoint': endpoint,
                'severity': severity,
                'student_id': student_id,
                'session_id': session_id
            })
            
            return error_event.timestamp
            
        except Exception as e:
            # Fallback logging if main logging fails
            print(f"CRITICAL: Failed to log error: {e}")
            logger.critical(f"Failed to log error: {e}")
            return datetime.utcnow().isoformat()

    def _sanitize_request_data(self, request_data: Dict) -> Dict:
        """Sanitize request data to remove sensitive information"""
        sensitive_keys = ['password', 'token', 'secret', 'key', 'auth']
        sanitized = {}
        
        for key, value in request_data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str) and len(value) > 200:
                sanitized[key] = value[:200] + '...'
            else:
                sanitized[key] = value
                
        return sanitized

    def _check_alert_conditions(self, component: str, error_key: str):
        """Check if error conditions warrant alerts"""
        try:
            if component in self.component_thresholds:
                thresholds = self.component_thresholds[component]
                current_count = self.error_counts[error_key]
                
                # Check if we've exceeded thresholds
                if current_count >= thresholds.get('critical', float('inf')):
                    self._trigger_alert('critical', component, error_key, current_count)
                elif current_count >= thresholds.get('high', float('inf')):
                    self._trigger_alert('high', component, error_key, current_count)
                elif current_count >= thresholds.get('medium', float('inf')):
                    self._trigger_alert('medium', component, error_key, current_count)
                    
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")

    def _trigger_alert(self, severity: str, component: str, error_key: str, count: int):
        """Trigger an alert for error conditions"""
        try:
            alert_message = f"ALERT [{severity.upper()}]: {error_key} has occurred {count} times in {component}"
            logger.warning(alert_message)
            
            # Here you could integrate with external alerting systems
            # For now, we'll just log it
            print(f"🚨 {alert_message}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with self.lock:
                # Filter errors by time
                recent_errors = [
                    error for error in self.errors
                    if datetime.fromisoformat(error.timestamp) >= cutoff_time
                ]
                
                # Calculate statistics
                total_errors = len(recent_errors)
                errors_by_component = defaultdict(int)
                errors_by_severity = defaultdict(int)
                errors_by_type = defaultdict(int)
                
                for error in recent_errors:
                    errors_by_component[error.component] += 1
                    errors_by_severity[error.severity] += 1
                    errors_by_type[error.error_type] += 1
                
                # Get top errors
                top_errors = sorted(
                    [(key, count) for key, count in self.error_counts.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                
                return {
                    'summary': {
                        'total_errors': total_errors,
                        'time_period': f'{hours} hours',
                        'errors_by_component': dict(errors_by_component),
                        'errors_by_severity': dict(errors_by_severity),
                        'errors_by_type': dict(errors_by_type)
                    },
                    'top_errors': top_errors,
                    'recent_errors': [
                        {
                            'timestamp': error.timestamp,
                            'component': error.component,
                            'error_type': error.error_type,
                            'severity': error.severity,
                            'message': error.error_message[:100] + '...' if len(error.error_message) > 100 else error.error_message
                        }
                        for error in recent_errors[-20:]  # Last 20 errors
                    ],
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {
                'error': 'Failed to generate error summary',
                'message': str(e)
            }

    def get_component_health(self) -> Dict[str, Any]:
        """Get health status for each component"""
        try:
            with self.lock:
                component_health = {}
                
                for component in self.component_thresholds.keys():
                    # Get recent errors for this component
                    recent_errors = [
                        error for error in self.errors
                        if error.component == component and
                        datetime.fromisoformat(error.timestamp) >= datetime.utcnow() - timedelta(hours=1)
                    ]
                    
                    error_count = len(recent_errors)
                    thresholds = self.component_thresholds[component]
                    
                    # Determine health status
                    if error_count >= thresholds.get('critical', float('inf')):
                        status = 'critical'
                    elif error_count >= thresholds.get('high', float('inf')):
                        status = 'unhealthy'
                    elif error_count >= thresholds.get('medium', float('inf')):
                        status = 'warning'
                    else:
                        status = 'healthy'
                    
                    component_health[component] = {
                        'status': status,
                        'error_count_1h': error_count,
                        'thresholds': thresholds,
                        'last_error': recent_errors[-1].timestamp if recent_errors else None
                    }
                
                return {
                    'component_health': component_health,
                    'overall_health': self._calculate_overall_health(component_health),
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting component health: {e}")
            return {
                'error': 'Failed to get component health',
                'message': str(e)
            }

    def _calculate_overall_health(self, component_health: Dict) -> str:
        """Calculate overall system health"""
        statuses = [health['status'] for health in component_health.values()]
        
        if 'critical' in statuses:
            return 'critical'
        elif 'unhealthy' in statuses:
            return 'unhealthy'
        elif 'warning' in statuses:
            return 'warning'
        else:
            return 'healthy'

    def get_error_details(self, error_timestamp: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific error"""
        try:
            with self.lock:
                for error in self.errors:
                    if error.timestamp == error_timestamp:
                        return asdict(error)
            return None
            
        except Exception as e:
            logger.error(f"Error getting error details: {e}")
            return None

    def clear_old_errors(self, hours: int = 24):
        """Clear errors older than specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with self.lock:
                # Keep only recent errors
                recent_errors = [
                    error for error in self.errors
                    if datetime.fromisoformat(error.timestamp) >= cutoff_time
                ]
                
                # Clear and repopulate
                self.errors.clear()
                for error in recent_errors:
                    self.errors.append(error)
                
                logger.info(f"Cleared errors older than {hours} hours. Kept {len(recent_errors)} recent errors.")
                
        except Exception as e:
            logger.error(f"Error clearing old errors: {e}")

    def export_errors(self, hours: int = 24, format: str = 'json') -> str:
        """Export errors to file"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with self.lock:
                recent_errors = [
                    error for error in self.errors
                    if datetime.fromisoformat(error.timestamp) >= cutoff_time
                ]
            
            if format == 'json':
                filename = f"error_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join('logs', filename)
                
                # Ensure logs directory exists
                os.makedirs('logs', exist_ok=True)
                
                with open(filepath, 'w') as f:
                    json.dump([asdict(error) for error in recent_errors], f, indent=2)
                
                return filepath
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting errors: {e}")
            raise

# Global instance
error_tracking_service = ErrorTrackingService()

# Decorator for automatic error tracking
def track_errors(component: str, severity: str = 'medium'):
    """Decorator to automatically track errors in functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_tracking_service.log_error(
                    error=e,
                    component=component,
                    severity=severity,
                    additional_context={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                )
                raise
        return wrapper
    return decorator