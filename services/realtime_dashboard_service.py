#!/usr/bin/env python3
"""
Service untuk real-time dashboard updates
"""

import redis
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class RealtimeDashboardService:
    def __init__(self, socketio, redis_client):
        self.socketio = socketio
        self.redis_client = redis_client
        self.enabled = redis_client is not None
        
        if self.enabled:
            self.setup_redis_listeners()
    
    def setup_redis_listeners(self):
        """Setup Redis listeners for real-time updates"""
        try:
            # Subscribe to emotion events
            self.emotion_pubsub = self.redis_client.pubsub()
            self.emotion_pubsub.subscribe('emotion-updates')
            
            # Start listening in background thread
            import threading
            self.listener_thread = threading.Thread(target=self._listen_for_updates, daemon=True)
            self.listener_thread.start()
            
            logger.info("Real-time dashboard service started")
        except Exception as e:
            logger.error(f"Failed to setup real-time service: {e}")
            self.enabled = False
    
    def _listen_for_updates(self):
        """Listen for Redis updates and broadcast to clients"""
        while self.enabled:
            try:
                message = self.emotion_pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    self._process_update_message(message['data'])
            except Exception as e:
                logger.error(f"Error in real-time listener: {e}")
                import time
                time.sleep(1)
    
    def _process_update_message(self, data: str):
        """Process update message from Redis"""
        try:
            update_data = json.loads(data)
            student_id = update_data.get('student_id')
            emotion = update_data.get('emotion')
            confidence = update_data.get('confidence')
            timestamp = update_data.get('timestamp')
            
            # Get parent IDs for this student
            parent_ids = self._get_parent_ids_for_student(student_id)
            
            # Send update to all parents of this student
            for parent_id in parent_ids:
                self.socketio.emit('emotion_update', {
                    'student_id': student_id,
                    'emotion': emotion,
                    'confidence': confidence,
                    'timestamp': timestamp,
                    'type': 'new_detection'
                }, room=f'parent_{parent_id}')
            
            # Send general dashboard update
            self.socketio.emit('dashboard_update', {
                'type': 'emotion_detected',
                'student_id': student_id,
                'emotion': emotion,
                'timestamp': timestamp
            }, namespace='/')
            
        except Exception as e:
            logger.error(f"Error processing update message: {e}")
    
    def _get_parent_ids_for_student(self, student_id: str) -> List[str]:
        """Get parent IDs for a student"""
        try:
            # Query database to get parent IDs
            from models import StudentParent
            from app import db
            
            with db.session() as session:
                parents = session.query(StudentParent).filter_by(student_id=student_id).all()
                return [str(parent.parent_id) for parent in parents]
        except Exception as e:
            logger.error(f"Error getting parent IDs for student {student_id}: {e}")
            return []
    
    def broadcast_emotion_update(self, student_id: str, emotion: str, confidence: float, session_id: int = None):
        """Broadcast emotion update to relevant clients"""
        if not self.enabled:
            return
        
        try:
            update_data = {
                'student_id': student_id,
                'emotion': emotion,
                'confidence': confidence,
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': session_id
            }
            
            # Publish to Redis for other workers to process
            self.redis_client.publish('emotion-updates', json.dumps(update_data))
            
            # Also send directly to connected clients
            parent_ids = self._get_parent_ids_for_student(student_id)
            for parent_id in parent_ids:
                self.socketio.emit('emotion_update', {
                    **update_data,
                    'type': 'new_detection'
                }, room=f'parent_{parent_id}')
            
        except Exception as e:
            logger.error(f"Error broadcasting emotion update: {e}")
    
    def broadcast_dashboard_refresh(self, user_id: str, data_type: str = 'all'):
        """Broadcast dashboard refresh to specific user"""
        if not self.enabled:
            return
        
        try:
            self.socketio.emit('dashboard_refresh', {
                'type': 'refresh',
                'data_type': data_type,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'parent_{user_id}')
        except Exception as e:
            logger.error(f"Error broadcasting dashboard refresh: {e}")
    
    def join_parent_room(self, parent_id: str, session_id: str):
        """Join parent to their room for targeted updates"""
        try:
            from flask_socketio import join_room
            join_room(f'parent_{parent_id}', session=session_id)
            logger.info(f"Parent {parent_id} joined room")
        except Exception as e:
            logger.error(f"Error joining parent room: {e}")
    
    def leave_parent_room(self, parent_id: str, session_id: str):
        """Leave parent from their room"""
        try:
            from flask_socketio import leave_room
            leave_room(f'parent_{parent_id}', session=session_id)
            logger.info(f"Parent {parent_id} left room")
        except Exception as e:
            logger.error(f"Error leaving parent room: {e}")

# Global service instance (will be initialized in app.py)
realtime_service = None

def init_realtime_service(socketio, redis_client):
    """Initialize real-time service"""
    global realtime_service
    realtime_service = RealtimeDashboardService(socketio, redis_client)
    return realtime_service
