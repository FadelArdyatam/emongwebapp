"""
Mental Health Service untuk detailed recommendations dan intervention suggestions
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class MentalHealthService:
    def __init__(self):
        self.emotion_weights = {
            'happy': 1.0,
            'surprise': 0.8,
            'neutral': 0.5,
            'sad': -0.8,
            'angry': -1.0,
            'fear': -0.9,
            'disgust': -0.7
        }
        
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        self.intervention_templates = {
            'low': [
                "Siswa menunjukkan kondisi emosional yang stabil. Teruskan monitoring rutin.",
                "Pertahankan lingkungan belajar yang positif dan mendukung.",
                "Berikan pujian dan reinforcement positif untuk mempertahankan mood yang baik."
            ],
            'medium': [
                "Siswa menunjukkan beberapa tanda stress atau ketidakstabilan emosional.",
                "Perhatikan pola emosi dan identifikasi pemicu stress.",
                "Berikan dukungan emosional dan kesempatan untuk beristirahat.",
                "Komunikasikan dengan orang tua untuk monitoring di rumah."
            ],
            'high': [
                "Siswa menunjukkan tanda-tanda distress emosional yang signifikan.",
                "Segera berikan perhatian khusus dan dukungan emosional.",
                "Pertimbangkan untuk melibatkan konselor sekolah atau psikolog.",
                "Komunikasikan segera dengan orang tua dan tim kesehatan mental.",
                "Dokumentasikan semua observasi untuk referensi profesional."
            ]
        }
        
        self.recommendation_templates = {
            'emotional_support': [
                "Berikan waktu untuk siswa mengekspresikan perasaannya",
                "Gunakan teknik active listening saat berkomunikasi",
                "Ciptakan lingkungan yang aman dan tidak menghakimi"
            ],
            'academic_adjustment': [
                "Pertimbangkan penyesuaian beban tugas sementara",
                "Berikan deadline yang lebih fleksibel jika memungkinkan",
                "Fokus pada pencapaian kecil untuk membangun kepercayaan diri"
            ],
            'social_intervention': [
                "Fasilitasi interaksi positif dengan teman sebaya",
                "Pertimbangkan kegiatan kelompok yang mendukung",
                "Monitor interaksi sosial untuk tanda-tanda isolasi"
            ],
            'professional_referral': [
                "Konsultasi dengan konselor sekolah",
                "Rujuk ke psikolog atau psikiater jika diperlukan",
                "Koordinasi dengan tim kesehatan mental sekolah"
            ]
        }

    def analyze_mental_health_trends(self, student_id: int, days: int = 7) -> Dict[str, Any]:
        """Analyze mental health trends for a student"""
        try:
            from app import app
            from models import db, EmotionLog
            
            with app.app_context():
                # Get emotion logs for the specified period
                start_date = datetime.utcnow() - timedelta(days=days)
                logs = EmotionLog.query.filter(
                    EmotionLog.student_id == student_id,
                    EmotionLog.detected_at >= start_date
                ).order_by(EmotionLog.detected_at.desc()).all()
                
                if not logs:
                    return {
                        'status': 'no_data',
                        'message': 'Tidak ada data emosi untuk periode ini',
                        'recommendations': ['Mulai monitoring emosi siswa secara rutin']
                    }
                
                # Analyze emotion patterns
                emotions = [log.emotion for log in logs]
                emotion_counts = Counter(emotions)
                total_detections = len(emotions)
                
                # Calculate weighted emotional score
                weighted_score = sum(
                    self.emotion_weights.get(emotion, 0) * count 
                    for emotion, count in emotion_counts.items()
                ) / total_detections if total_detections > 0 else 0
                
                # Normalize score to 0-1 range
                normalized_score = (weighted_score + 1) / 2
                
                # Determine risk level
                risk_level = self._determine_risk_level(normalized_score)
                
                # Analyze trends
                trends = self._analyze_emotion_trends(logs)
                
                # Generate recommendations
                recommendations = self._generate_recommendations(
                    risk_level, emotion_counts, trends, total_detections
                )
                
                # Generate intervention suggestions
                interventions = self._generate_interventions(risk_level, trends)
                
                return {
                    'status': 'success',
                    'student_id': student_id,
                    'analysis_period': f'{days} hari terakhir',
                    'total_detections': total_detections,
                    'emotion_distribution': dict(emotion_counts),
                    'weighted_emotional_score': round(normalized_score, 3),
                    'risk_level': risk_level,
                    'trends': trends,
                    'recommendations': recommendations,
                    'interventions': interventions,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Mental health analysis error: {e}")
            return {
                'status': 'error',
                'message': f'Error dalam analisis: {str(e)}',
                'recommendations': ['Hubungi administrator sistem']
            }

    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level based on emotional score"""
        if score >= self.risk_thresholds['high']:
            return 'high'
        elif score >= self.risk_thresholds['medium']:
            return 'medium'
        else:
            return 'low'

    def _analyze_emotion_trends(self, logs: List) -> Dict[str, Any]:
        """Analyze emotion trends over time"""
        if len(logs) < 2:
            return {'trend': 'insufficient_data', 'direction': 'stable'}
        
        # Group by day
        daily_emotions = defaultdict(list)
        for log in logs:
            day = log.detected_at.date()
            daily_emotions[day].append(log.emotion)
        
        # Calculate daily scores
        daily_scores = []
        for day, emotions in daily_emotions.items():
            if emotions:
                daily_score = sum(
                    self.emotion_weights.get(emotion, 0) for emotion in emotions
                ) / len(emotions)
                daily_scores.append((day, daily_score))
        
        if len(daily_scores) < 2:
            return {'trend': 'insufficient_data', 'direction': 'stable'}
        
        # Calculate trend direction
        scores = [score for _, score in daily_scores]
        if len(scores) >= 3:
            # Use linear regression for trend
            x = np.arange(len(scores))
            y = np.array(scores)
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1:
                direction = 'improving'
            elif slope < -0.1:
                direction = 'declining'
            else:
                direction = 'stable'
        else:
            direction = 'stable'
        
        return {
            'trend': 'analyzed',
            'direction': direction,
            'daily_scores': [(day.isoformat(), round(score, 3)) for day, score in daily_scores],
            'volatility': np.std(scores) if len(scores) > 1 else 0
        }

    def _generate_recommendations(self, risk_level: str, emotion_counts: Counter, 
                                trends: Dict, total_detections: int) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Base recommendations by risk level
        recommendations.extend(self.intervention_templates[risk_level])
        
        # Specific recommendations based on emotion patterns
        if emotion_counts.get('sad', 0) > total_detections * 0.3:
            recommendations.extend(self.recommendation_templates['emotional_support'])
        
        if emotion_counts.get('angry', 0) > total_detections * 0.2:
            recommendations.extend([
                "Identifikasi pemicu kemarahan dan hindari situasi yang memicu",
                "Ajarkan teknik manajemen kemarahan yang sesuai usia"
            ])
        
        if emotion_counts.get('fear', 0) > total_detections * 0.2:
            recommendations.extend([
                "Ciptakan lingkungan yang aman dan dapat diprediksi",
                "Berikan reassurance dan dukungan emosional"
            ])
        
        if trends.get('direction') == 'declining':
            recommendations.extend(self.recommendation_templates['academic_adjustment'])
        
        if risk_level == 'high':
            recommendations.extend(self.recommendation_templates['professional_referral'])
        
        return list(set(recommendations))  # Remove duplicates

    def _generate_interventions(self, risk_level: str, trends: Dict) -> List[Dict[str, Any]]:
        """Generate specific intervention suggestions"""
        interventions = []
        
        if risk_level == 'low':
            interventions.append({
                'type': 'preventive',
                'priority': 'low',
                'title': 'Maintenance Monitoring',
                'description': 'Lanjutkan monitoring rutin dan pertahankan lingkungan positif',
                'timeline': 'ongoing',
                'resources': ['Form monitoring emosi', 'Checklist lingkungan positif']
            })
        
        elif risk_level == 'medium':
            interventions.extend([
                {
                    'type': 'supportive',
                    'priority': 'medium',
                    'title': 'Emotional Support Session',
                    'description': 'Jadwalkan sesi dukungan emosional dengan siswa',
                    'timeline': '1-2 minggu',
                    'resources': ['Template sesi dukungan', 'Form observasi emosi']
                },
                {
                    'type': 'academic',
                    'priority': 'medium',
                    'title': 'Academic Accommodation',
                    'description': 'Pertimbangkan penyesuaian akademik sementara',
                    'timeline': '1-4 minggu',
                    'resources': ['Form penyesuaian akademik', 'Template komunikasi orang tua']
                }
            ])
        
        else:  # high risk
            interventions.extend([
                {
                    'type': 'crisis',
                    'priority': 'high',
                    'title': 'Immediate Support',
                    'description': 'Berikan dukungan segera dan monitoring intensif',
                    'timeline': 'immediate',
                    'resources': ['Protokol krisis', 'Kontak darurat']
                },
                {
                    'type': 'professional',
                    'priority': 'high',
                    'title': 'Professional Referral',
                    'description': 'Rujuk ke profesional kesehatan mental',
                    'timeline': '1-3 hari',
                    'resources': ['Daftar profesional', 'Form rujukan']
                },
                {
                    'type': 'family',
                    'priority': 'high',
                    'title': 'Family Communication',
                    'description': 'Komunikasi segera dengan keluarga',
                    'timeline': 'immediate',
                    'resources': ['Template komunikasi keluarga', 'Protokol koordinasi']
                }
            ])
        
        return interventions

    def get_progress_tracking(self, student_id: int, intervention_id: str = None) -> Dict[str, Any]:
        """Track progress of mental health interventions"""
        try:
            from app import app
            from models import db, EmotionLog
            
            with app.app_context():
                # Get recent emotion data
                recent_logs = EmotionLog.query.filter(
                    EmotionLog.student_id == student_id
                ).order_by(EmotionLog.detected_at.desc()).limit(100).all()
                
                if not recent_logs:
                    return {'status': 'no_data'}
                
                # Calculate progress metrics
                emotions = [log.emotion for log in recent_logs]
                recent_emotions = emotions[:20]  # Last 20 detections
                older_emotions = emotions[20:40] if len(emotions) > 20 else []
                
                recent_score = self._calculate_emotional_score(recent_emotions)
                older_score = self._calculate_emotional_score(older_emotions) if older_emotions else recent_score
                
                progress = recent_score - older_score
                progress_percentage = (progress / older_score * 100) if older_score != 0 else 0
                
                return {
                    'status': 'success',
                    'student_id': student_id,
                    'current_score': round(recent_score, 3),
                    'previous_score': round(older_score, 3),
                    'progress': round(progress, 3),
                    'progress_percentage': round(progress_percentage, 1),
                    'trend': 'improving' if progress > 0 else 'declining' if progress < 0 else 'stable',
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Progress tracking error: {e}")
            return {'status': 'error', 'message': str(e)}

    def _calculate_emotional_score(self, emotions: List[str]) -> float:
        """Calculate emotional score for a list of emotions"""
        if not emotions:
            return 0.5  # Neutral
        
        weighted_sum = sum(self.emotion_weights.get(emotion, 0) for emotion in emotions)
        return (weighted_sum / len(emotions) + 1) / 2  # Normalize to 0-1

# Global instance
mental_health_service = MentalHealthService()