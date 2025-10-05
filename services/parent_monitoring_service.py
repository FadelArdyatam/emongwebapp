"""
Parent Monitoring Service untuk comprehensive child monitoring
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from models import db, Student, EmotionLog, EmotionSession, StudentParent, User
from sqlalchemy import func, and_, or_
import json

logger = logging.getLogger(__name__)

class ParentMonitoringService:
    def __init__(self):
        pass
    
    def get_child_comprehensive_data(self, parent_id: int, child_id: int, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive data for a specific child"""
        try:
            # Verify parent-child relationship
            relationship = StudentParent.query.filter(
                StudentParent.parent_id == parent_id,
                StudentParent.student_id == child_id
            ).first()
            
            if not relationship:
                return {'status': 'error', 'message': 'Access denied to this child'}
            
            # Get child info
            child = Student.query.get(child_id)
            if not child:
                return {'status': 'error', 'message': 'Child not found'}
            
            # Get emotion data for the period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            emotion_logs = EmotionLog.query.filter(
                EmotionLog.student_id == child_id,
                EmotionLog.detected_at >= start_date,
                EmotionLog.detected_at <= end_date
            ).order_by(EmotionLog.detected_at.desc()).all()
            
            # Calculate emotion statistics
            emotion_stats = self._calculate_emotion_statistics(emotion_logs)
            
            # Get session data
            sessions = EmotionSession.query.filter(
                EmotionSession.student_id == child_id,
                EmotionSession.start_time >= start_date
            ).order_by(EmotionSession.start_time.desc()).all()
            
            # Get recent activity
            recent_activity = self._get_recent_activity(child_id, days)
            
            # Get trends
            trends = self._calculate_trends(emotion_logs, days)
            
            # Get alerts and recommendations
            alerts = self._get_child_alerts(child_id, emotion_stats)
            recommendations = self._get_recommendations(emotion_stats, trends)
            
            return {
                'status': 'success',
                'child_info': {
                    'id': child.id,
                    'student_code': child.student_code,
                    'full_name': child.full_name,
                    'class_name': child.class_name,
                    'date_of_birth': child.date_of_birth.isoformat() if child.date_of_birth else None,
                    'is_active': child.is_active
                },
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'emotion_statistics': emotion_stats,
                'sessions': [
                    {
                        'id': session.id,
                        'session_name': session.session_name,
                        'start_time': session.start_time.isoformat(),
                        'end_time': session.end_time.isoformat() if session.end_time else None,
                        'duration_minutes': session.duration_minutes,
                        'emotion_count': session.emotion_count
                    }
                    for session in sessions
                ],
                'recent_activity': recent_activity,
                'trends': trends,
                'alerts': alerts,
                'recommendations': recommendations,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting child comprehensive data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _calculate_emotion_statistics(self, emotion_logs: List[EmotionLog]) -> Dict[str, Any]:
        """Calculate comprehensive emotion statistics"""
        if not emotion_logs:
            return {
                'total_detections': 0,
                'emotion_distribution': {},
                'average_confidence': 0,
                'dominant_emotion': 'neutral',
                'emotion_frequency': {},
                'confidence_trend': 'stable'
            }
        
        # Basic counts
        total_detections = len(emotion_logs)
        emotion_counts = {}
        confidence_scores = []
        
        for log in emotion_logs:
            emotion = log.emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            if log.confidence_score:
                confidence_scores.append(log.confidence_score)
        
        # Calculate percentages
        emotion_distribution = {
            emotion: round((count / total_detections) * 100, 1)
            for emotion, count in emotion_counts.items()
        }
        
        # Find dominant emotion
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'neutral'
        
        # Calculate average confidence
        average_confidence = round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else 0
        
        # Calculate emotion frequency (detections per day)
        emotion_frequency = {}
        for emotion, count in emotion_counts.items():
            emotion_frequency[emotion] = round(count / (total_detections / 7), 1)  # Per day average
        
        return {
            'total_detections': total_detections,
            'emotion_distribution': emotion_distribution,
            'emotion_counts': emotion_counts,
            'average_confidence': average_confidence,
            'dominant_emotion': dominant_emotion,
            'emotion_frequency': emotion_frequency,
            'confidence_trend': 'stable'  # Could be enhanced with trend calculation
        }
    
    def _get_recent_activity(self, child_id: int, days: int) -> List[Dict[str, Any]]:
        """Get recent activity for the child"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get recent emotion logs with session info
            recent_logs = db.session.query(
                EmotionLog, EmotionSession
            ).join(EmotionSession).filter(
                EmotionLog.student_id == child_id,
                EmotionLog.detected_at >= start_date
            ).order_by(EmotionLog.detected_at.desc()).limit(20).all()
            
            activities = []
            for log, session in recent_logs:
                activities.append({
                    'type': 'emotion_detected',
                    'timestamp': log.detected_at.isoformat(),
                    'emotion': log.emotion,
                    'confidence': log.confidence_score,
                    'session_name': session.session_name,
                    'description': f"Emotion '{log.emotion}' detected with {log.confidence_score:.1%} confidence"
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _calculate_trends(self, emotion_logs: List[EmotionLog], days: int) -> Dict[str, Any]:
        """Calculate emotion trends over time"""
        if len(emotion_logs) < 2:
            return {'trend': 'insufficient_data', 'direction': 'stable'}
        
        # Group by day
        daily_emotions = {}
        for log in emotion_logs:
            day = log.detected_at.date()
            if day not in daily_emotions:
                daily_emotions[day] = []
            daily_emotions[day].append(log.emotion)
        
        # Calculate daily emotion scores
        emotion_scores = {'happy': 1, 'surprise': 0.8, 'neutral': 0.5, 'sad': -0.8, 'angry': -1, 'fear': -0.9, 'disgust': -0.7}
        
        daily_scores = []
        for day, emotions in daily_emotions.items():
            if emotions:
                avg_score = sum(emotion_scores.get(emotion, 0) for emotion in emotions) / len(emotions)
                daily_scores.append(avg_score)
        
        if len(daily_scores) < 2:
            return {'trend': 'insufficient_data', 'direction': 'stable'}
        
        # Calculate trend direction
        first_half = daily_scores[:len(daily_scores)//2]
        second_half = daily_scores[len(daily_scores)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        diff = second_avg - first_avg
        
        if diff > 0.1:
            direction = 'improving'
        elif diff < -0.1:
            direction = 'declining'
        else:
            direction = 'stable'
        
        return {
            'trend': 'calculated',
            'direction': direction,
            'change_percentage': round(diff * 100, 1),
            'daily_scores': daily_scores
        }
    
    def _get_child_alerts(self, child_id: int, emotion_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get alerts for the child based on emotion patterns"""
        alerts = []
        
        # Check for concerning patterns
        if emotion_stats['total_detections'] == 0:
            alerts.append({
                'type': 'no_data',
                'severity': 'info',
                'message': 'No emotion data available for this period',
                'recommendation': 'Ensure child participates in emotion detection sessions'
            })
            return alerts
        
        # Check for high negative emotion ratio
        negative_emotions = ['sad', 'angry', 'fear', 'disgust']
        negative_ratio = sum(emotion_stats['emotion_distribution'].get(emotion, 0) for emotion in negative_emotions)
        
        if negative_ratio > 60:
            alerts.append({
                'type': 'high_negative_emotions',
                'severity': 'warning',
                'message': f'High ratio of negative emotions detected ({negative_ratio:.1f}%)',
                'recommendation': 'Consider discussing with child about their feelings and well-being'
            })
        
        # Check for low confidence scores
        if emotion_stats['average_confidence'] < 0.3:
            alerts.append({
                'type': 'low_confidence',
                'severity': 'info',
                'message': 'Low average confidence in emotion detection',
                'recommendation': 'Ensure good lighting and clear facial expressions during sessions'
            })
        
        # Check for single dominant emotion
        dominant_percentage = max(emotion_stats['emotion_distribution'].values()) if emotion_stats['emotion_distribution'] else 0
        if dominant_percentage > 80:
            alerts.append({
                'type': 'limited_emotion_range',
                'severity': 'info',
                'message': f'Limited emotion range detected (dominant: {emotion_stats["dominant_emotion"]})',
                'recommendation': 'Encourage child to express different emotions naturally'
            })
        
        return alerts
    
    def _get_recommendations(self, emotion_stats: Dict[str, Any], trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations based on emotion data"""
        recommendations = []
        
        if emotion_stats['total_detections'] == 0:
            return recommendations
        
        # Positive recommendations
        if trends['direction'] == 'improving':
            recommendations.append({
                'type': 'positive_trend',
                'title': 'Positive Emotional Trend',
                'description': 'Your child shows improving emotional patterns',
                'action': 'Continue current supportive activities'
            })
        
        # Recommendations based on dominant emotion
        dominant_emotion = emotion_stats['dominant_emotion']
        if dominant_emotion == 'sad':
            recommendations.append({
                'type': 'emotional_support',
                'title': 'Emotional Support Needed',
                'description': 'Child shows frequent sadness',
                'action': 'Spend quality time together and encourage open communication'
            })
        elif dominant_emotion == 'angry':
            recommendations.append({
                'type': 'anger_management',
                'title': 'Anger Management Support',
                'description': 'Child shows frequent anger',
                'action': 'Teach coping strategies and provide calm environment'
            })
        elif dominant_emotion == 'happy':
            recommendations.append({
                'type': 'maintain_positive',
                'title': 'Maintain Positive Environment',
                'description': 'Child shows good emotional well-being',
                'action': 'Continue current positive practices'
            })
        
        # General recommendations
        if emotion_stats['average_confidence'] < 0.5:
            recommendations.append({
                'type': 'technical_improvement',
                'title': 'Improve Detection Quality',
                'description': 'Low confidence in emotion detection',
                'action': 'Ensure good lighting and clear facial expressions'
            })
        
        return recommendations
    
    def get_real_time_updates(self, parent_id: int, child_id: int) -> Dict[str, Any]:
        """Get real-time updates for a child (for WebSocket)"""
        try:
            # Verify access
            relationship = StudentParent.query.filter(
                StudentParent.parent_id == parent_id,
                StudentParent.student_id == child_id
            ).first()
            
            if not relationship:
                return {'status': 'error', 'message': 'Access denied'}
            
            # Get latest emotion data (last 5 minutes)
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            
            recent_logs = EmotionLog.query.filter(
                EmotionLog.student_id == child_id,
                EmotionLog.detected_at >= five_minutes_ago
            ).order_by(EmotionLog.detected_at.desc()).all()
            
            # Get active sessions
            active_sessions = EmotionSession.query.filter(
                EmotionSession.student_id == child_id,
                EmotionSession.end_time.is_(None)  # Still active
            ).all()
            
            return {
                'status': 'success',
                'child_id': child_id,
                'recent_emotions': [
                    {
                        'emotion': log.emotion,
                        'confidence': log.confidence_score,
                        'timestamp': log.detected_at.isoformat()
                    }
                    for log in recent_logs
                ],
                'active_sessions': [
                    {
                        'id': session.id,
                        'session_name': session.session_name,
                        'start_time': session.start_time.isoformat(),
                        'duration_minutes': session.duration_minutes
                    }
                    for session in active_sessions
                ],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time updates: {e}")
            return {'status': 'error', 'message': str(e)}

# Global instance
parent_monitoring_service = ParentMonitoringService()