"""
Emotion Bias Correction Service untuk mengatasi bias model yang cenderung menunjukkan sad padahal neutral
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import Counter, deque
import logging

logger = logging.getLogger(__name__)

class EmotionBiasCorrection:
    def __init__(self):
        # Confidence thresholds untuk setiap emosi - NORMAL CONFIGURATION
        self.confidence_thresholds = {
            'happy': 0.3,    # Threshold normal untuk happy
            'sad': 0.6,      # Threshold tinggi untuk sad (kurangi false positive)
            'angry': 0.4,    # Threshold normal untuk angry
            'fear': 0.5,     # Threshold normal untuk fear
            'surprise': 0.3, # Threshold normal untuk surprise
            'disgust': 0.4,  # Threshold normal untuk disgust
            'neutral': 0.2   # Threshold rendah untuk neutral (prioritaskan neutral)
        }
        
        # Historical context untuk smoothing
        self.emotion_history = deque(maxlen=10)
        self.confidence_history = deque(maxlen=10)
        
        # Bias correction weights - NORMAL CONFIGURATION
        self.bias_weights = {
            'sad': 0.3,      # Kurangi sad (bias model ke sad)
            'neutral': 1.5,  # Boost neutral (prioritaskan neutral)
            'happy': 1.2,    # Boost happy sedikit
            'angry': 1.0,    # Normal weight untuk angry
            'fear': 1.0,     # Normal weight untuk fear
            'disgust': 1.0,  # Normal weight untuk disgust
            'surprise': 1.1  # Boost surprise sedikit
        }
        
        # Context-based corrections - EXTREME BOOST FEAR, ANGRY & SURPRISED
        self.context_rules = {
            'classroom': {
                'sad': 0.1,      # Lebih agresif reduce sad
                'neutral': 0.2,  # KURANGI boost neutral lebih drastis
                'happy': 0.5,    # Kurangi boost happy lebih drastis
                'angry': 2.5,    # EXTREME BOOST ANGRY di classroom
                'fear': 2.0,     # EXTREME BOOST FEAR di classroom
                'disgust': 1.2,  # Boost disgust detection
                'surprise': 2.5  # EXTREME BOOST SURPRISED di classroom
            },
            'home': {
                'sad': 0.2,      # Lebih agresif reduce sad
                'neutral': 0.3,  # KURANGI boost neutral lebih drastis
                'happy': 0.7,    # Kurangi boost happy
                'angry': 2.2,    # EXTREME BOOST ANGRY di home
                'fear': 1.8,     # EXTREME BOOST FEAR di home
                'disgust': 1.1,  # Boost disgust detection di home
                'surprise': 2.2  # EXTREME BOOST SURPRISED di home
            }
        }

    def correct_emotion_bias(self, emotion_scores: Dict[str, float], 
                           context: str = 'classroom',
                           previous_emotions: List[str] = None) -> Dict[str, any]:
        """
        Correct emotion bias dengan multiple strategies
        
        Args:
            emotion_scores: Dictionary dengan emotion scores dari model
            context: Context environment (classroom, home, etc.)
            previous_emotions: List of previous emotions untuk context
            
        Returns:
            Dictionary dengan corrected emotion dan confidence
        """
        try:
            if not emotion_scores or len(emotion_scores) == 0:
                return {
                    'emotion': 'neutral',
                    'confidence': 0.5,
                    'original_emotion': 'neutral',
                    'correction_applied': False
                }
            
            # 1. Apply bias correction weights
            corrected_scores = self._apply_bias_weights(emotion_scores)
            
            # 2. Apply context-based corrections
            corrected_scores = self._apply_context_corrections(corrected_scores, context)
            
            # 3. Apply historical smoothing
            corrected_scores = self._apply_historical_smoothing(corrected_scores, previous_emotions)
            
            # 4. Apply confidence thresholds
            corrected_scores = self._apply_confidence_thresholds(corrected_scores)
            
            # 5. Get final emotion
            final_emotion = max(corrected_scores.items(), key=lambda x: x[1])[0]
            final_confidence = corrected_scores[final_emotion]
            
            # 6. Additional validation
            final_emotion, final_confidence = self._validate_emotion(final_emotion, final_confidence, corrected_scores)
            
            # Store in history
            self.emotion_history.append(final_emotion)
            self.confidence_history.append(final_confidence)
            
            return {
                'emotion': final_emotion,
                'confidence': final_confidence,
                'original_emotion': max(emotion_scores.items(), key=lambda x: x[1])[0],
                'correction_applied': True,
                'corrected_scores': corrected_scores,
                'bias_correction_factors': self._get_correction_factors(emotion_scores, corrected_scores)
            }
            
        except Exception as e:
            logger.error(f"Error in emotion bias correction: {e}")
            # Fallback to original scores
            original_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            return {
                'emotion': original_emotion,
                'confidence': emotion_scores[original_emotion],
                'original_emotion': original_emotion,
                'correction_applied': False,
                'error': str(e)
            }

    def _apply_bias_weights(self, emotion_scores: Dict[str, float]) -> Dict[str, float]:
        """Apply bias correction weights dengan penalty untuk happy/sad dan boost untuk surprise/disgust/angry"""
        corrected = {}
        for emotion, score in emotion_scores.items():
            weight = self.bias_weights.get(emotion, 1.0)
            
            # Penalty khusus untuk sad dan happy - kurangi score secara drastis
            if emotion == 'sad':
                if score > 0.6:
                    corrected[emotion] = score * 0.2  # Kurangi drastis
                else:
                    corrected[emotion] = score * weight
            elif emotion == 'happy':
                if score > 0.7:  # Jika happy score sangat tinggi
                    corrected[emotion] = score * 0.8  # Kurangi sedikit
                else:
                    corrected[emotion] = score * weight
            # Penalty khusus untuk neutral - kurangi score jika ada emosi lain yang tinggi
            elif emotion == 'neutral':
                other_emotions = {k: v for k, v in emotion_scores.items() if k != 'neutral'}
                max_other_score = max(other_emotions.values()) if other_emotions else 0
                if max_other_score > 0.4:  # Jika ada emosi lain yang cukup tinggi
                    corrected[emotion] = score * 0.5  # Kurangi neutral drastis
                else:
                    corrected[emotion] = score * weight
            # EXTREME BOOST untuk angry - SANGAT AGRESIF
            elif emotion == 'angry':
                if score > 0.05:  # Jika ada sedikit indikasi angry
                    corrected[emotion] = min(1.0, score * weight * 2.5)  # EXTREME boost
                else:
                    corrected[emotion] = score * weight
            # EXTREME BOOST untuk fear - SANGAT AGRESIF
            elif emotion == 'fear':
                if score > 0.05:  # Jika ada sedikit indikasi fear
                    corrected[emotion] = min(1.0, score * weight * 2.2)  # EXTREME boost
                else:
                    corrected[emotion] = score * weight
            # EXTREME BOOST untuk surprise - SANGAT AGRESIF
            elif emotion == 'surprise':
                if score > 0.05:  # Jika ada sedikit indikasi surprise
                    corrected[emotion] = min(1.0, score * weight * 2.5)  # EXTREME boost
                else:
                    corrected[emotion] = score * weight
            # Boost khusus untuk disgust
            elif emotion == 'disgust':
                if score > 0.1:  # Jika ada indikasi disgust
                    corrected[emotion] = min(1.0, score * weight * 1.4)  # Extra boost
                else:
                    corrected[emotion] = score * weight
            else:
                corrected[emotion] = min(1.0, score * weight)
        return corrected

    def _apply_context_corrections(self, emotion_scores: Dict[str, float], context: str) -> Dict[str, float]:
        """Apply context-based corrections"""
        if context not in self.context_rules:
            return emotion_scores
            
        context_weights = self.context_rules[context]
        corrected = {}
        for emotion, score in emotion_scores.items():
            weight = context_weights.get(emotion, 1.0)
            corrected[emotion] = min(1.0, score * weight)
        return corrected

    def _apply_historical_smoothing(self, emotion_scores: Dict[str, float], 
                                  previous_emotions: List[str] = None) -> Dict[str, float]:
        """Apply historical smoothing to reduce sudden changes"""
        if not previous_emotions or len(previous_emotions) < 3:
            return emotion_scores
        
        # Get recent emotion pattern
        recent_emotions = previous_emotions[-3:]
        emotion_counts = Counter(recent_emotions)
        most_common = emotion_counts.most_common(1)[0][0]
        
        # Boost the most common recent emotion slightly
        corrected = emotion_scores.copy()
        if most_common in corrected:
            corrected[most_common] = min(1.0, corrected[most_common] * 1.1)
        
        return corrected

    def _apply_confidence_thresholds(self, emotion_scores: Dict[str, float]) -> Dict[str, float]:
        """Apply confidence thresholds to filter low-confidence predictions"""
        corrected = {}
        for emotion, score in emotion_scores.items():
            threshold = self.confidence_thresholds.get(emotion, 0.5)
            if score >= threshold:
                corrected[emotion] = score
            else:
                # Reduce score below threshold
                corrected[emotion] = score * 0.5
        
        # Ensure we have at least one emotion
        if not corrected or max(corrected.values()) < 0.3:
            corrected['neutral'] = 0.5
            
        return corrected

    def _validate_emotion(self, emotion: str, confidence: float, 
                         corrected_scores: Dict[str, float]) -> Tuple[str, float]:
        """Additional validation untuk memastikan emotion masuk akal"""
        
        # Rule 1: Jika confidence sangat rendah, default ke neutral
        if confidence < 0.3:
            return 'neutral', 0.5
        
        # Rule 2: EXTREME AGRESIF - prioritaskan angry, fear, dan surprised
        if emotion in ['sad', 'happy', 'neutral']:
            # Cek angry dulu - PRIORITAS TERTINGGI
            if 'angry' in corrected_scores:
                angry_score = corrected_scores['angry']
                if angry_score > 0.05:  # Threshold EXTREME rendah untuk angry
                    return 'angry', angry_score
            
            # Cek fear - PRIORITAS KEDUA
            if 'fear' in corrected_scores:
                fear_score = corrected_scores['fear']
                if fear_score > 0.05:  # Threshold EXTREME rendah untuk fear
                    return 'fear', fear_score
            
            # Cek surprised - PRIORITAS KETIGA
            if 'surprise' in corrected_scores:
                surprise_score = corrected_scores['surprise']
                if surprise_score > 0.05:  # Threshold EXTREME rendah untuk surprised
                    return 'surprise', surprise_score
            
            # Cek disgust
            if 'disgust' in corrected_scores:
                disgust_score = corrected_scores['disgust']
                if disgust_score > 0.1:  # Threshold rendah untuk disgust
                    return 'disgust', disgust_score
            
            # Cek emosi lain jika priority emotions tidak ada
            other_emotions = {k: v for k, v in corrected_scores.items() if k not in ['sad', 'happy', 'neutral']}
            if other_emotions:
                best_other = max(other_emotions.items(), key=lambda x: x[1])
                # Pilih emosi lain jika score > 0.1
                if best_other[1] > 0.1:
                    return best_other[0], best_other[1]
            
            # Jika tetap harus pilih sad/happy/neutral, pastikan confidence SANGAT tinggi
            if confidence < 0.98:
                return 'angry', 0.8  # Default ke angry jika confidence rendah
        
        # Rule 3: Jika neutral dengan confidence rendah tapi ada emosi lain yang cukup tinggi,
        # pilih emosi lain tersebut
        if emotion == 'neutral' and confidence < 0.5:
            other_emotions = {k: v for k, v in corrected_scores.items() if k != 'neutral'}
            if other_emotions:
                best_other = max(other_emotions.items(), key=lambda x: x[1])
                if best_other[1] > 0.6:
                    return best_other[0], best_other[1]
        
        # Rule 4: Jika ada multiple emotions dengan score yang hampir sama,
        # pilih yang lebih positif
        if confidence > 0.4 and confidence < 0.7:
            positive_emotions = ['happy', 'surprise', 'neutral']
            for pos_emotion in positive_emotions:
                if pos_emotion in corrected_scores and corrected_scores[pos_emotion] > confidence * 0.9:
                    return pos_emotion, corrected_scores[pos_emotion]
        
        return emotion, confidence

    def _get_correction_factors(self, original_scores: Dict[str, float], 
                              corrected_scores: Dict[str, float]) -> Dict[str, float]:
        """Get correction factors untuk debugging"""
        factors = {}
        for emotion in original_scores:
            if emotion in corrected_scores:
                original = original_scores[emotion]
                corrected = corrected_scores[emotion]
                if original > 0:
                    factors[emotion] = corrected / original
                else:
                    factors[emotion] = 1.0
        return factors

    def get_emotion_confidence_analysis(self, emotion_scores: Dict[str, float]) -> Dict[str, any]:
        """Analyze emotion confidence untuk debugging"""
        if not emotion_scores:
            return {'error': 'No emotion scores provided'}
        
        analysis = {
            'original_scores': emotion_scores,
            'confidence_levels': {},
            'recommendations': []
        }
        
        for emotion, score in emotion_scores.items():
            threshold = self.confidence_thresholds.get(emotion, 0.5)
            analysis['confidence_levels'][emotion] = {
                'score': score,
                'threshold': threshold,
                'above_threshold': score >= threshold,
                'confidence_ratio': score / threshold if threshold > 0 else 0
            }
        
        # Generate recommendations
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        if max_emotion[1] < 0.5:
            analysis['recommendations'].append("Confidence rendah, pertimbangkan untuk menggunakan neutral")
        
        if 'sad' in emotion_scores and emotion_scores['sad'] > 0.6:
            analysis['recommendations'].append("Sad confidence tinggi, periksa apakah benar-benar sad atau neutral")
        
        if 'neutral' in emotion_scores and emotion_scores['neutral'] > 0.4:
            analysis['recommendations'].append("Neutral confidence cukup, pertimbangkan untuk memilih neutral")
        
        return analysis

    def reset_history(self):
        """Reset historical data"""
        self.emotion_history.clear()
        self.confidence_history.clear()

# Global instance
emotion_bias_correction = EmotionBiasCorrection()