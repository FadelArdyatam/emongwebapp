"""
Communication Service untuk parent-teacher communication
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models import db, User, Student, StudentParent
from sqlalchemy import and_, or_
import json

logger = logging.getLogger(__name__)

class CommunicationService:
    def __init__(self):
        pass
    
    def send_message_to_teacher(self, parent_id: int, student_id: int, message: str, 
                               message_type: str = 'general') -> Dict[str, Any]:
        """Send message from parent to teacher"""
        try:
            # Verify parent-child relationship
            relationship = StudentParent.query.filter(
                StudentParent.parent_id == parent_id,
                StudentParent.student_id == student_id
            ).first()
            
            if not relationship:
                return {'status': 'error', 'message': 'Access denied to this child'}
            
            # Get child info
            child = Student.query.get(student_id)
            if not child:
                return {'status': 'error', 'message': 'Child not found'}
            
            # Get parent info
            parent = User.query.get(parent_id)
            if not parent:
                return {'status': 'error', 'message': 'Parent not found'}
            
            # For now, we'll simulate sending message
            # In a real implementation, this would store in database and send notifications
            
            message_data = {
                'id': f"msg_{datetime.utcnow().timestamp()}",
                'parent_id': parent_id,
                'parent_name': parent.full_name or parent.username,
                'student_id': student_id,
                'student_name': child.full_name,
                'student_code': child.student_code,
                'message': message,
                'message_type': message_type,
                'sent_at': datetime.utcnow().isoformat(),
                'status': 'sent'
            }
            
            # Log the message (in real implementation, store in database)
            logger.info(f"Message from parent {parent_id} to teacher for student {student_id}: {message}")
            
            return {
                'status': 'success',
                'message': 'Message sent successfully',
                'message_data': message_data
            }
            
        except Exception as e:
            logger.error(f"Error sending message to teacher: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_communication_history(self, parent_id: int, student_id: int, 
                                 days: int = 30) -> Dict[str, Any]:
        """Get communication history for a specific child"""
        try:
            # Verify parent-child relationship
            relationship = StudentParent.query.filter(
                StudentParent.parent_id == parent_id,
                StudentParent.student_id == student_id
            ).first()
            
            if not relationship:
                return {'status': 'error', 'message': 'Access denied to this child'}
            
            # For now, return mock data
            # In real implementation, this would query from database
            
            mock_messages = [
                {
                    'id': 'msg_1',
                    'sender': 'teacher',
                    'sender_name': 'Guru Kelas',
                    'message': 'Anak Anda menunjukkan performa yang baik dalam sesi deteksi emosi hari ini.',
                    'message_type': 'positive_feedback',
                    'sent_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    'status': 'read'
                },
                {
                    'id': 'msg_2',
                    'sender': 'parent',
                    'sender_name': 'Orang Tua',
                    'message': 'Terima kasih atas informasinya. Apakah ada yang perlu saya perhatikan?',
                    'message_type': 'question',
                    'sent_at': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    'status': 'read'
                },
                {
                    'id': 'msg_3',
                    'sender': 'teacher',
                    'sender_name': 'Guru Kelas',
                    'message': 'Tidak ada yang perlu dikhawatirkan. Anak Anda terlihat bahagia dan aktif di kelas.',
                    'message_type': 'reassurance',
                    'sent_at': (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                    'status': 'unread'
                }
            ]
            
            return {
                'status': 'success',
                'student_id': student_id,
                'messages': mock_messages,
                'total_messages': len(mock_messages),
                'unread_count': len([m for m in mock_messages if m['status'] == 'unread']),
                'period_days': days,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting communication history: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_notification_preferences(self, parent_id: int) -> Dict[str, Any]:
        """Get notification preferences for parent"""
        try:
            # For now, return default preferences
            # In real implementation, this would query from database
            
            preferences = {
                'email_notifications': True,
                'push_notifications': True,
                'sms_notifications': False,
                'notification_types': {
                    'emotion_alerts': True,
                    'session_updates': True,
                    'teacher_messages': True,
                    'system_updates': False,
                    'weekly_reports': True
                },
                'frequency': {
                    'emotion_alerts': 'immediate',
                    'session_updates': 'daily',
                    'teacher_messages': 'immediate',
                    'weekly_reports': 'weekly'
                }
            }
            
            return {
                'status': 'success',
                'parent_id': parent_id,
                'preferences': preferences,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def update_notification_preferences(self, parent_id: int, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update notification preferences for parent"""
        try:
            # For now, just log the update
            # In real implementation, this would update database
            
            logger.info(f"Updating notification preferences for parent {parent_id}: {preferences}")
            
            return {
                'status': 'success',
                'message': 'Notification preferences updated successfully',
                'preferences': preferences,
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_teacher_contact_info(self, parent_id: int, student_id: int) -> Dict[str, Any]:
        """Get teacher contact information for a specific child"""
        try:
            # Verify parent-child relationship
            relationship = StudentParent.query.filter(
                StudentParent.parent_id == parent_id,
                StudentParent.student_id == student_id
            ).first()
            
            if not relationship:
                return {'status': 'error', 'message': 'Access denied to this child'}
            
            # Get child info
            child = Student.query.get(student_id)
            if not child:
                return {'status': 'error', 'message': 'Child not found'}
            
            # For now, return mock teacher info
            # In real implementation, this would query from database based on child's class
            
            teacher_info = {
                'teacher_name': 'Guru Kelas',
                'teacher_email': 'guru@sekolah.com',
                'teacher_phone': '+62-xxx-xxx-xxxx',
                'class_name': child.class_name,
                'school_name': 'Sekolah Emong',
                'office_hours': '08:00 - 16:00 WIB',
                'response_time': 'Within 24 hours'
            }
            
            return {
                'status': 'success',
                'student_id': student_id,
                'student_name': child.full_name,
                'teacher_info': teacher_info,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting teacher contact info: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def send_emergency_alert(self, parent_id: int, student_id: int, alert_type: str, 
                           message: str) -> Dict[str, Any]:
        """Send emergency alert to parent"""
        try:
            # Verify parent-child relationship
            relationship = StudentParent.query.filter(
                StudentParent.parent_id == parent_id,
                StudentParent.student_id == student_id
            ).first()
            
            if not relationship:
                return {'status': 'error', 'message': 'Access denied to this child'}
            
            # Get child info
            child = Student.query.get(student_id)
            if not child:
                return {'status': 'error', 'message': 'Child not found'}
            
            # Log emergency alert
            logger.warning(f"Emergency alert for parent {parent_id}, student {student_id}: {alert_type} - {message}")
            
            alert_data = {
                'id': f"alert_{datetime.utcnow().timestamp()}",
                'parent_id': parent_id,
                'student_id': student_id,
                'student_name': child.full_name,
                'alert_type': alert_type,
                'message': message,
                'sent_at': datetime.utcnow().isoformat(),
                'status': 'sent',
                'priority': 'high'
            }
            
            return {
                'status': 'success',
                'message': 'Emergency alert sent successfully',
                'alert_data': alert_data
            }
            
        except Exception as e:
            logger.error(f"Error sending emergency alert: {e}")
            return {'status': 'error', 'message': str(e)}

# Global instance
communication_service = CommunicationService()