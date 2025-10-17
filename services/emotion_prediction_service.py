"""
Emotion Trend Prediction Service dengan AI features
"""
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter, deque
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class EmotionPredictionService:
    def __init__(self):
        self.emotion_weights = {
            'happy': 1.0,
            'surprise': 0.8,
            'neutral': 0.5,
            'sad': -0.8,
            'angry': -1.0,
            'fear': -0.9,
            'disgust': -0.9  # Tingkatkan sensitivitas disgust dari -0.7 ke -0.9
        }
        
        self.prediction_window = 7  # days
        self.min_data_points = 5   # minimum data points for prediction
        
        # Behavioral pattern recognition parameters
        self.pattern_window = 14   # days to analyze for patterns
        self.anomaly_threshold = 2.0  # standard deviations for anomaly detection

    def predict_emotion_trends(self, student_id: int, days_ahead: int = 3) -> Dict[str, Any]:
        """Predict emotion trends for a student"""
        try:
            from app import app
            from models import db, EmotionLog
            
            with app.app_context():
                # Get historical emotion data
                start_date = datetime.utcnow() - timedelta(days=self.prediction_window * 2)
                logs = EmotionLog.query.filter(
                    EmotionLog.student_id == student_id,
                    EmotionLog.detected_at >= start_date
                ).order_by(EmotionLog.detected_at.asc()).all()
                
                if len(logs) < self.min_data_points:
                    return {
                        'status': 'insufficient_data',
                        'message': f'Minimal {self.min_data_points} data points diperlukan untuk prediksi',
                        'required_points': self.min_data_points,
                        'available_points': len(logs)
                    }
                
                # Prepare data for prediction
                daily_scores = self._prepare_daily_scores(logs)
                
                if len(daily_scores) < self.min_data_points:
                    return {
                        'status': 'insufficient_data',
                        'message': 'Data harian tidak mencukupi untuk prediksi'
                    }
                
                # Generate predictions
                predictions = self._generate_predictions(daily_scores, days_ahead)
                
                # Analyze behavioral patterns
                patterns = self._analyze_behavioral_patterns(logs)
                
                # Detect anomalies
                anomalies = self._detect_anomalies(daily_scores)
                
                return {
                    'status': 'success',
                    'student_id': student_id,
                    'prediction_period': f'{days_ahead} hari ke depan',
                    'predictions': predictions,
                    'behavioral_patterns': patterns,
                    'anomalies': anomalies,
                    'confidence': self._calculate_prediction_confidence(daily_scores),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Emotion prediction error: {e}")
            return {
                'status': 'error',
                'message': f'Error dalam prediksi: {str(e)}'
            }

    def _prepare_daily_scores(self, logs: List) -> List[Tuple[datetime, float]]:
        """Prepare daily emotional scores from logs"""
        daily_emotions = {}
        
        for log in logs:
            day = log.detected_at.date()
            if day not in daily_emotions:
                daily_emotions[day] = []
            daily_emotions[day].append(log.emotion)
        
        # Calculate daily scores
        daily_scores = []
        for day, emotions in daily_emotions.items():
            if emotions:
                # Calculate weighted average
                score = sum(self.emotion_weights.get(emotion, 0) for emotion in emotions) / len(emotions)
                # Normalize to 0-1 range
                normalized_score = (score + 1) / 2
                daily_scores.append((datetime.combine(day, datetime.min.time()), normalized_score))
        
        return sorted(daily_scores, key=lambda x: x[0])

    def _generate_predictions(self, daily_scores: List[Tuple[datetime, float]], 
                            days_ahead: int) -> List[Dict[str, Any]]:
        """Generate emotion trend predictions"""
        if len(daily_scores) < 3:
            return []
        
        # Extract features and targets
        X = np.array(range(len(daily_scores))).reshape(-1, 1)
        y = np.array([score for _, score in daily_scores])
        
        # Add time-based features
        X_features = np.column_stack([
            X.flatten(),
            np.sin(2 * np.pi * X.flatten() / 7),  # Weekly pattern
            np.cos(2 * np.pi * X.flatten() / 7),
            np.sin(2 * np.pi * X.flatten() / 30), # Monthly pattern
            np.cos(2 * np.pi * X.flatten() / 30)
        ])
        
        # Train model
        model = LinearRegression()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_features)
        model.fit(X_scaled, y)
        
        # Generate predictions
        predictions = []
        last_date = daily_scores[-1][0]
        
        for i in range(1, days_ahead + 1):
            future_idx = len(daily_scores) + i - 1
            future_features = np.array([[
                future_idx,
                np.sin(2 * np.pi * future_idx / 7),
                np.cos(2 * np.pi * future_idx / 7),
                np.sin(2 * np.pi * future_idx / 30),
                np.cos(2 * np.pi * future_idx / 30)
            ]])
            
            future_scaled = scaler.transform(future_features)
            predicted_score = model.predict(future_scaled)[0]
            
            # Clamp prediction to valid range
            predicted_score = max(0, min(1, predicted_score))
            
            # Convert score back to emotion
            predicted_emotion = self._score_to_emotion(predicted_score)
            
            predictions.append({
                'date': (last_date + timedelta(days=i)).isoformat(),
                'predicted_score': round(predicted_score, 3),
                'predicted_emotion': predicted_emotion,
                'confidence': self._calculate_single_prediction_confidence(model, X_scaled, y)
            })
        
        return predictions

    def _analyze_behavioral_patterns(self, logs: List) -> Dict[str, Any]:
        """Analyze behavioral patterns in emotion data"""
        if len(logs) < 10:
            return {'status': 'insufficient_data'}
        
        # Analyze time-based patterns
        hourly_patterns = {}
        daily_patterns = {}
        weekly_patterns = {}
        
        for log in logs:
            hour = log.detected_at.hour
            weekday = log.detected_at.weekday()
            
            if hour not in hourly_patterns:
                hourly_patterns[hour] = []
            if weekday not in daily_patterns:
                daily_patterns[weekday] = []
            
            hourly_patterns[hour].append(log.emotion)
            daily_patterns[weekday].append(log.emotion)
        
        # Calculate dominant emotions by time
        hourly_dominants = {}
        for hour, emotions in hourly_patterns.items():
            if len(emotions) >= 3:  # Minimum samples
                dominant = Counter(emotions).most_common(1)[0][0]
                hourly_dominants[hour] = {
                    'dominant_emotion': dominant,
                    'frequency': len(emotions),
                    'confidence': Counter(emotions)[dominant] / len(emotions)
                }
        
        daily_dominants = {}
        for day, emotions in daily_patterns.items():
            if len(emotions) >= 3:
                dominant = Counter(emotions).most_common(1)[0][0]
                daily_dominants[day] = {
                    'dominant_emotion': dominant,
                    'frequency': len(emotions),
                    'confidence': Counter(emotions)[dominant] / len(emotions)
                }
        
        # Analyze emotion transitions
        transitions = self._analyze_emotion_transitions(logs)
        
        return {
            'status': 'analyzed',
            'hourly_patterns': hourly_dominants,
            'daily_patterns': daily_dominants,
            'emotion_transitions': transitions,
            'pattern_strength': self._calculate_pattern_strength(hourly_dominants, daily_dominants)
        }

    def _analyze_emotion_transitions(self, logs: List) -> Dict[str, Any]:
        """Analyze emotion transition patterns"""
        if len(logs) < 5:
            return {}
        
        # Sort logs by time
        sorted_logs = sorted(logs, key=lambda x: x.detected_at)
        
        transitions = {}
        for i in range(len(sorted_logs) - 1):
            current_emotion = sorted_logs[i].emotion
            next_emotion = sorted_logs[i + 1].emotion
            
            transition_key = f"{current_emotion} -> {next_emotion}"
            if transition_key not in transitions:
                transitions[transition_key] = 0
            transitions[transition_key] += 1
        
        # Calculate transition probabilities
        transition_probs = {}
        for transition, count in transitions.items():
            from_emotion = transition.split(' -> ')[0]
            total_from = sum(c for t, c in transitions.items() if t.startswith(from_emotion + ' ->'))
            transition_probs[transition] = count / total_from if total_from > 0 else 0
        
        return {
            'transitions': transitions,
            'probabilities': transition_probs,
            'most_common_transition': max(transitions.items(), key=lambda x: x[1]) if transitions else None
        }

    def _detect_anomalies(self, daily_scores: List[Tuple[datetime, float]]) -> List[Dict[str, Any]]:
        """Detect anomalies in emotion patterns"""
        if len(daily_scores) < 5:
            return []
        
        scores = np.array([score for _, score in daily_scores])
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        anomalies = []
        for i, (date, score) in enumerate(daily_scores):
            z_score = abs(score - mean_score) / std_score if std_score > 0 else 0
            
            if z_score > self.anomaly_threshold:
                anomalies.append({
                    'date': date.isoformat(),
                    'score': round(score, 3),
                    'z_score': round(z_score, 2),
                    'severity': 'high' if z_score > 3 else 'medium',
                    'description': self._describe_anomaly(score, mean_score)
                })
        
        return anomalies

    def _describe_anomaly(self, score: float, mean_score: float) -> str:
        """Describe an anomaly"""
        if score > mean_score + 0.3:
            return "Emosi sangat positif (di atas normal)"
        elif score < mean_score - 0.3:
            return "Emosi sangat negatif (di bawah normal)"
        else:
            return "Pola emosi tidak biasa"

    def _score_to_emotion(self, score: float) -> str:
        """Convert normalized score back to emotion"""
        if score >= 0.8:
            return 'happy'
        elif score >= 0.6:
            return 'surprise'
        elif score >= 0.4:
            return 'neutral'
        elif score >= 0.2:
            return 'sad'
        else:
            return 'angry'

    def _calculate_prediction_confidence(self, daily_scores: List[Tuple[datetime, float]]) -> float:
        """Calculate overall prediction confidence"""
        if len(daily_scores) < 3:
            return 0.0
        
        scores = [score for _, score in daily_scores]
        
        # Calculate data consistency (lower variance = higher confidence)
        variance = np.var(scores)
        consistency = max(0, 1 - variance)
        
        # Calculate data sufficiency (more data = higher confidence)
        sufficiency = min(1.0, len(daily_scores) / 14)  # 14 days = 100% sufficiency
        
        # Combine factors
        confidence = (consistency * 0.6) + (sufficiency * 0.4)
        return round(confidence, 3)

    def _calculate_single_prediction_confidence(self, model, X_scaled, y) -> float:
        """Calculate confidence for a single prediction"""
        try:
            # Use R-squared as confidence measure
            score = model.score(X_scaled, y)
            return round(max(0, min(1, score)), 3)
        except:
            return 0.5

    def _calculate_pattern_strength(self, hourly_patterns: Dict, daily_patterns: Dict) -> float:
        """Calculate strength of behavioral patterns"""
        total_patterns = len(hourly_patterns) + len(daily_patterns)
        if total_patterns == 0:
            return 0.0
        
        strong_patterns = 0
        for patterns in [hourly_patterns, daily_patterns]:
            for pattern in patterns.values():
                if pattern.get('confidence', 0) > 0.7:  # Strong pattern threshold
                    strong_patterns += 1
        
        return round(strong_patterns / total_patterns, 3)

    def get_behavioral_insights(self, student_id: int) -> Dict[str, Any]:
        """Get comprehensive behavioral insights"""
        try:
            from app import app
            from models import db, EmotionLog
            
            with app.app_context():
                # Get extended historical data
                start_date = datetime.utcnow() - timedelta(days=30)
                logs = EmotionLog.query.filter(
                    EmotionLog.student_id == student_id,
                    EmotionLog.detected_at >= start_date
                ).order_by(EmotionLog.detected_at.asc()).all()
                
                if len(logs) < 10:
                    return {
                        'status': 'insufficient_data',
                        'message': 'Data tidak mencukupi untuk analisis perilaku'
                    }
                
                # Analyze patterns
                patterns = self._analyze_behavioral_patterns(logs)
                
                # Detect anomalies
                daily_scores = self._prepare_daily_scores(logs)
                anomalies = self._detect_anomalies(daily_scores)
                
                # Generate insights
                insights = self._generate_behavioral_insights(patterns, anomalies, daily_scores)
                
                return {
                    'status': 'success',
                    'student_id': student_id,
                    'analysis_period': '30 hari terakhir',
                    'patterns': patterns,
                    'anomalies': anomalies,
                    'insights': insights,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Behavioral insights error: {e}")
            return {
                'status': 'error',
                'message': f'Error dalam analisis perilaku: {str(e)}'
            }

    def _generate_behavioral_insights(self, patterns: Dict, anomalies: List, 
                                    daily_scores: List[Tuple[datetime, float]]) -> List[str]:
        """Generate behavioral insights from analysis"""
        insights = []
        
        # Pattern-based insights
        if patterns.get('status') == 'analyzed':
            hourly_patterns = patterns.get('hourly_patterns', {})
            daily_patterns = patterns.get('daily_patterns', {})
            
            # Time-based insights
            if hourly_patterns:
                morning_emotions = [p for h, p in hourly_patterns.items() if 6 <= h <= 11]
                afternoon_emotions = [p for h, p in hourly_patterns.items() if 12 <= h <= 17]
                evening_emotions = [p for h, p in hourly_patterns.items() if 18 <= h <= 22]
                
                if morning_emotions:
                    dominant_morning = max(morning_emotions, key=lambda x: x['confidence'])
                    insights.append(f"Pola emosi pagi: {dominant_morning['dominant_emotion']} (confidence: {dominant_morning['confidence']:.2f})")
                
                if afternoon_emotions:
                    dominant_afternoon = max(afternoon_emotions, key=lambda x: x['confidence'])
                    insights.append(f"Pola emosi siang: {dominant_afternoon['dominant_emotion']} (confidence: {dominant_afternoon['confidence']:.2f})")
            
            # Day-of-week insights
            if daily_patterns:
                weekday_emotions = [p for d, p in daily_patterns.items() if d < 5]
                weekend_emotions = [p for d, p in daily_patterns.items() if d >= 5]
                
                if weekday_emotions and weekend_emotions:
                    avg_weekday = np.mean([self.emotion_weights.get(p['dominant_emotion'], 0) for p in weekday_emotions])
                    avg_weekend = np.mean([self.emotion_weights.get(p['dominant_emotion'], 0) for p in weekend_emotions])
                    
                    if avg_weekend > avg_weekday + 0.2:
                        insights.append("Siswa cenderung lebih bahagia di akhir pekan")
                    elif avg_weekday > avg_weekend + 0.2:
                        insights.append("Siswa cenderung lebih bahagia di hari sekolah")
        
        # Anomaly-based insights
        if anomalies:
            high_severity = [a for a in anomalies if a['severity'] == 'high']
            if high_severity:
                insights.append(f"Ditemukan {len(high_severity)} anomali emosi dengan tingkat tinggi")
            
            recent_anomalies = [a for a in anomalies if datetime.fromisoformat(a['date']).date() >= (datetime.utcnow() - timedelta(days=7)).date()]
            if recent_anomalies:
                insights.append(f"Terdapat {len(recent_anomalies)} anomali emosi dalam 7 hari terakhir")
        
        # Trend insights
        if len(daily_scores) >= 7:
            recent_scores = [score for _, score in daily_scores[-7:]]
            older_scores = [score for _, score in daily_scores[-14:-7]] if len(daily_scores) >= 14 else recent_scores
            
            recent_avg = np.mean(recent_scores)
            older_avg = np.mean(older_scores)
            
            if recent_avg > older_avg + 0.1:
                insights.append("Tren emosi menunjukkan peningkatan positif dalam seminggu terakhir")
            elif recent_avg < older_avg - 0.1:
                insights.append("Tren emosi menunjukkan penurunan dalam seminggu terakhir")
        
        return insights

# Global instance
emotion_prediction_service = EmotionPredictionService()