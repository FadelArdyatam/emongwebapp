"""
Advanced Temporal Analysis Service - Alternatif LSTM
Menggunakan metode statistik dan rule-based untuk analisis temporal emosi
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, Counter
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class AdvancedTemporalService:
    def __init__(self):
        self.emotion_weights = {
            'happy': 1.0, 'surprise': 0.8, 'neutral': 0.5,
            'sad': -0.8, 'angry': -1.0, 'fear': -0.9, 'disgust': -0.9  # Tingkatkan sensitivitas disgust
        }
        
        # Temporal analysis parameters
        self.short_window = 5      # frames untuk analisis jangka pendek
        self.medium_window = 15   # frames untuk analisis jangka menengah  
        self.long_window = 30     # frames untuk analisis jangka panjang
        
    def analyze_emotion_sequences(self, emotion_sequence: List[str]) -> Dict[str, Any]:
        """Analisis urutan emosi menggunakan metode statistik"""
        if len(emotion_sequence) < 3:
            return {'status': 'insufficient_data'}
            
        # 1. Transition Analysis
        transitions = self._analyze_transitions(emotion_sequence)
        
        # 2. Volatility Analysis  
        volatility = self._calculate_volatility(emotion_sequence)
        
        # 3. Pattern Recognition
        patterns = self._detect_patterns(emotion_sequence)
        
        # 4. Trend Analysis
        trend = self._calculate_trend(emotion_sequence)
        
        # 5. Stability Analysis
        stability = self._calculate_stability(emotion_sequence)
        
        return {
            'transitions': transitions,
            'volatility': volatility,
            'patterns': patterns,
            'trend': trend,
            'stability': stability,
            'sequence_length': len(emotion_sequence)
        }
    
    def _analyze_transitions(self, sequence: List[str]) -> Dict[str, Any]:
        """Analisis transisi emosi"""
        transitions = []
        for i in range(len(sequence) - 1):
            transitions.append(f"{sequence[i]} -> {sequence[i+1]}")
        
        transition_counts = Counter(transitions)
        most_common_transition = transition_counts.most_common(1)[0] if transition_counts else None
        
        return {
            'total_transitions': len(transitions),
            'unique_transitions': len(transition_counts),
            'most_common': most_common_transition,
            'transition_entropy': self._calculate_entropy(transitions)
        }
    
    def _calculate_volatility(self, sequence: List[str]) -> Dict[str, Any]:
        """Hitung volatilitas emosi"""
        scores = [self.emotion_weights.get(emotion, 0) for emotion in sequence]
        
        return {
            'variance': np.var(scores),
            'std_dev': np.std(scores),
            'range': max(scores) - min(scores),
            'coefficient_variation': np.std(scores) / np.mean(scores) if np.mean(scores) != 0 else 0
        }
    
    def _detect_patterns(self, sequence: List[str]) -> Dict[str, Any]:
        """Deteksi pola dalam urutan emosi"""
        patterns = {
            'repetitive': self._detect_repetitive_patterns(sequence),
            'cyclical': self._detect_cyclical_patterns(sequence),
            'escalating': self._detect_escalating_patterns(sequence),
            'deescalating': self._detect_deescalating_patterns(sequence)
        }
        
        return patterns
    
    def _detect_repetitive_patterns(self, sequence: List[str]) -> Dict[str, Any]:
        """Deteksi pola repetitif"""
        emotion_counts = Counter(sequence)
        dominant_emotion = emotion_counts.most_common(1)[0]
        dominance_ratio = dominant_emotion[1] / len(sequence)
        
        return {
            'is_repetitive': dominance_ratio > 0.6,
            'dominant_emotion': dominant_emotion[0],
            'dominance_ratio': dominance_ratio
        }
    
    def _detect_cyclical_patterns(self, sequence: List[str]) -> Dict[str, Any]:
        """Deteksi pola siklis"""
        if len(sequence) < 6:
            return {'is_cyclical': False, 'cycle_length': 0}
            
        # Cek untuk cycle length 2-5
        for cycle_len in range(2, min(6, len(sequence) // 2)):
            if self._is_cyclical(sequence, cycle_len):
                return {'is_cyclical': True, 'cycle_length': cycle_len}
        
        return {'is_cyclical': False, 'cycle_length': 0}
    
    def _is_cyclical(self, sequence: List[str], cycle_len: int) -> bool:
        """Cek apakah sequence memiliki pola siklis dengan panjang tertentu"""
        if len(sequence) < cycle_len * 2:
            return False
            
        pattern = sequence[:cycle_len]
        for i in range(cycle_len, len(sequence), cycle_len):
            if sequence[i:i+cycle_len] != pattern:
                return False
        return True
    
    def _detect_escalating_patterns(self, sequence: List[str]) -> Dict[str, Any]:
        """Deteksi pola eskalasi emosi"""
        scores = [self.emotion_weights.get(emotion, 0) for emotion in sequence]
        
        # Linear regression untuk deteksi trend
        x = np.arange(len(scores))
        slope, _ = np.polyfit(x, scores, 1)
        
        return {
            'is_escalating': slope > 0.1,
            'slope': slope,
            'trend_strength': abs(slope)
        }
    
    def _detect_deescalating_patterns(self, sequence: List[str]) -> Dict[str, Any]:
        """Deteksi pola de-eskalasi emosi"""
        scores = [self.emotion_weights.get(emotion, 0) for emotion in sequence]
        
        # Linear regression untuk deteksi trend
        x = np.arange(len(scores))
        slope, _ = np.polyfit(x, scores, 1)
        
        return {
            'is_deescalating': slope < -0.1,
            'slope': slope,
            'trend_strength': abs(slope)
        }
    
    def _calculate_trend(self, sequence: List[str]) -> Dict[str, Any]:
        """Hitung tren emosi menggunakan multiple methods"""
        scores = [self.emotion_weights.get(emotion, 0) for emotion in sequence]
        
        # Method 1: Linear Regression
        x = np.arange(len(scores))
        slope, intercept = np.polyfit(x, scores, 1)
        r_squared = self._calculate_r_squared(scores, slope * x + intercept)
        
        # Method 2: Moving Average Trend
        ma_trend = self._moving_average_trend(scores)
        
        # Method 3: Momentum
        momentum = self._calculate_momentum(scores)
        
        return {
            'linear_slope': slope,
            'linear_r_squared': r_squared,
            'moving_average_trend': ma_trend,
            'momentum': momentum,
            'overall_direction': self._classify_trend(slope, r_squared)
        }
    
    def _calculate_stability(self, sequence: List[str]) -> Dict[str, Any]:
        """Hitung stabilitas emosi"""
        scores = [self.emotion_weights.get(emotion, 0) for emotion in sequence]
        
        # Stability metrics
        variance = np.var(scores)
        std_dev = np.std(scores)
        mean_abs_dev = np.mean(np.abs(scores - np.mean(scores)))
        
        # Stability classification
        if std_dev < 0.2:
            stability_level = 'very_stable'
        elif std_dev < 0.4:
            stability_level = 'stable'
        elif std_dev < 0.6:
            stability_level = 'moderate'
        elif std_dev < 0.8:
            stability_level = 'unstable'
        else:
            stability_level = 'very_unstable'
        
        return {
            'variance': variance,
            'std_deviation': std_dev,
            'mean_abs_deviation': mean_abs_dev,
            'stability_level': stability_level,
            'is_stable': std_dev < 0.4
        }
    
    def _calculate_entropy(self, data: List[str]) -> float:
        """Hitung entropy dari data"""
        counts = Counter(data)
        total = len(data)
        entropy = 0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        return entropy
    
    def _calculate_r_squared(self, y_true: List[float], y_pred: List[float]) -> float:
        """Hitung R-squared"""
        ss_res = np.sum((np.array(y_true) - np.array(y_pred)) ** 2)
        ss_tot = np.sum((np.array(y_true) - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    def _moving_average_trend(self, scores: List[float]) -> Dict[str, Any]:
        """Hitung tren menggunakan moving average"""
        if len(scores) < 3:
            return {'trend': 'insufficient_data'}
            
        # Short MA vs Long MA
        short_window = max(2, len(scores) // 3)
        long_window = max(3, len(scores) // 2)
        
        short_ma = np.mean(scores[-short_window:])
        long_ma = np.mean(scores[-long_window:])
        
        if short_ma > long_ma * 1.1:
            trend = 'increasing'
        elif short_ma < long_ma * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
            
        return {
            'trend': trend,
            'short_ma': short_ma,
            'long_ma': long_ma,
            'difference': short_ma - long_ma
        }
    
    def _calculate_momentum(self, scores: List[float]) -> Dict[str, Any]:
        """Hitung momentum emosi"""
        if len(scores) < 2:
            return {'momentum': 0, 'direction': 'neutral'}
            
        # Rate of change
        roc = (scores[-1] - scores[0]) / len(scores)
        
        # Acceleration (second derivative)
        if len(scores) >= 3:
            first_diff = np.diff(scores)
            second_diff = np.diff(first_diff)
            acceleration = np.mean(second_diff) if len(second_diff) > 0 else 0
        else:
            acceleration = 0
            
        return {
            'rate_of_change': roc,
            'acceleration': acceleration,
            'momentum': roc + acceleration,
            'direction': 'positive' if roc > 0.1 else 'negative' if roc < -0.1 else 'neutral'
        }
    
    def _classify_trend(self, slope: float, r_squared: float) -> str:
        """Klasifikasi tren berdasarkan slope dan R-squared"""
        if r_squared < 0.3:
            return 'no_clear_trend'
        elif slope > 0.1:
            return 'strong_positive'
        elif slope > 0.05:
            return 'weak_positive'
        elif slope < -0.1:
            return 'strong_negative'
        elif slope < -0.05:
            return 'weak_negative'
        else:
            return 'stable'
    
    def predict_next_emotion(self, sequence: List[str], method: str = 'markov') -> Dict[str, Any]:
        """Prediksi emosi berikutnya menggunakan berbagai metode"""
        if len(sequence) < 2:
            return {'prediction': 'insufficient_data'}
            
        if method == 'markov':
            return self._markov_prediction(sequence)
        elif method == 'weighted_average':
            return self._weighted_average_prediction(sequence)
        elif method == 'pattern_based':
            return self._pattern_based_prediction(sequence)
        else:
            return {'prediction': 'invalid_method'}
    
    def _markov_prediction(self, sequence: List[str]) -> Dict[str, Any]:
        """Prediksi menggunakan Markov Chain"""
        # Build transition matrix
        transitions = {}
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_emotion = sequence[i + 1]
            
            if current not in transitions:
                transitions[current] = {}
            if next_emotion not in transitions[current]:
                transitions[current][next_emotion] = 0
            transitions[current][next_emotion] += 1
        
        # Normalize probabilities
        last_emotion = sequence[-1]
        if last_emotion in transitions:
            total = sum(transitions[last_emotion].values())
            probabilities = {
                emotion: count / total 
                for emotion, count in transitions[last_emotion].items()
            }
            predicted_emotion = max(probabilities, key=probabilities.get)
            confidence = probabilities[predicted_emotion]
        else:
            predicted_emotion = sequence[-1]  # Stay same
            confidence = 0.5
            
        return {
            'prediction': predicted_emotion,
            'confidence': confidence,
            'probabilities': probabilities if 'probabilities' in locals() else {}
        }
    
    def _weighted_average_prediction(self, sequence: List[str]) -> Dict[str, Any]:
        """Prediksi menggunakan weighted average"""
        # Recent emotions have higher weight
        weights = np.exp(np.linspace(-1, 0, len(sequence)))
        emotion_scores = {}
        
        for i, emotion in enumerate(sequence):
            if emotion not in emotion_scores:
                emotion_scores[emotion] = 0
            emotion_scores[emotion] += weights[i]
        
        # Normalize
        total_weight = sum(emotion_scores.values())
        probabilities = {
            emotion: score / total_weight 
            for emotion, score in emotion_scores.items()
        }
        
        predicted_emotion = max(probabilities, key=probabilities.get)
        confidence = probabilities[predicted_emotion]
        
        return {
            'prediction': predicted_emotion,
            'confidence': confidence,
            'probabilities': probabilities
        }
    
    def _pattern_based_prediction(self, sequence: List[str]) -> Dict[str, Any]:
        """Prediksi berdasarkan pola yang terdeteksi"""
        patterns = self._detect_patterns(sequence)
        
        # Jika ada pola siklis
        if patterns['cyclical']['is_cyclical']:
            cycle_len = patterns['cyclical']['cycle_length']
            next_index = len(sequence) % cycle_len
            predicted_emotion = sequence[next_index]
            confidence = 0.8
        # Jika ada pola repetitif
        elif patterns['repetitive']['is_repetitive']:
            predicted_emotion = patterns['repetitive']['dominant_emotion']
            confidence = patterns['repetitive']['dominance_ratio']
        # Default: gunakan weighted average
        else:
            return self._weighted_average_prediction(sequence)
        
        return {
            'prediction': predicted_emotion,
            'confidence': confidence,
            'method': 'pattern_based'
        }

# Global instance
advanced_temporal_service = AdvancedTemporalService()