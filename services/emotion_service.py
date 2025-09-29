"""
Emotion Processing Service untuk optimasi real-time processing
"""
import cv2
import numpy as np
from collections import deque, Counter
from deepface import DeepFace
import threading
import queue
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmotionProcessor:
    def __init__(self, max_queue_size=10, processing_interval=0.1):
        self.max_queue_size = max_queue_size
        self.processing_interval = processing_interval
        self.frame_queue = queue.Queue(maxsize=max_queue_size)
        self.emotion_history = deque(maxlen=10)
        self.processing = False
        self.thread = None
        self.callbacks = []
        
        # Real-time optimization settings
        self.frame_skip_count = 0
        self.frame_skip_threshold = 2  # Process every 3rd frame for performance
        self.last_processing_time = 0
        self.min_processing_interval = 0.05  # Minimum 50ms between processing
        
        # Face clustering integration
        self.face_clustering = FaceClustering()
        
    def add_callback(self, callback):
        """Add callback untuk emotion detection"""
        self.callbacks.append(callback)
    
    def start_processing(self):
        """Start background processing thread"""
        if self.processing:
            return
            
        self.processing = True
        self.thread = threading.Thread(target=self._process_frames, daemon=True)
        self.thread.start()
        logger.info("Emotion processor started")
    
    def stop_processing(self):
        """Stop background processing"""
        self.processing = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("Emotion processor stopped")
    
    def add_frame(self, frame, metadata=None):
        """Add frame to processing queue"""
        if self.frame_queue.full():
            # Remove oldest frame if queue is full
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
                
        frame_data = {
            'frame': frame.copy(),
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        try:
            self.frame_queue.put_nowait(frame_data)
        except queue.Full:
            logger.warning("Frame queue full, dropping frame")
    
    def _process_frames(self):
        """Background frame processing"""
        while self.processing:
            try:
                # Get frame with timeout
                frame_data = self.frame_queue.get(timeout=self.processing_interval)
                self._process_single_frame(frame_data)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Frame processing error: {e}")
    
    def _process_single_frame(self, frame_data):
        """Process single frame untuk emotion detection dengan optimasi real-time"""
        try:
            frame = frame_data['frame']
            timestamp = frame_data['timestamp']
            
            # Real-time optimization: Skip processing if too frequent
            current_time = time.time()
            if current_time - self.last_processing_time < self.min_processing_interval:
                return
                
            # Frame skipping for performance
            self.frame_skip_count += 1
            if self.frame_skip_count < self.frame_skip_threshold:
                return
            self.frame_skip_count = 0
            
            # Skip processing if queue has newer frames
            if not self.frame_queue.empty():
                return
                
            # Intelligent frame skipping based on motion
            if self._should_skip_frame(frame):
                return
                
            # Process emotion with demographic analysis
            emotion_data = self._detect_emotion(frame)
            if emotion_data:
                self.emotion_history.append(emotion_data)
                self.last_processing_time = current_time
                
                # Extract face embedding for clustering
                face_embedding = self._extract_face_embedding(frame)
                cluster_info = None
                
                if face_embedding is not None:
                    # Generate unique face ID
                    import hashlib
                    face_id = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
                    
                    # Add to clustering system
                    cluster_id = self.face_clustering.add_face_embedding(face_id, face_embedding)
                    cluster_info = self.face_clustering.get_cluster_info(cluster_id)
                
                # Smooth emotion using history
                smoothed_emotion = self._smooth_emotion()
                
                # Notify callbacks with enhanced data including clustering info
                for callback in self.callbacks:
                    try:
                        callback({
                            'emotion': smoothed_emotion.get('emotion', 'neutral'),
                            'emotion_confidence': smoothed_emotion.get('emotion_confidence', 0),
                            'age': smoothed_emotion.get('age', 0),
                            'gender': smoothed_emotion.get('gender', 'unknown'),
                            'gender_confidence': smoothed_emotion.get('gender_confidence', 0),
                            'race': smoothed_emotion.get('race', 'unknown'),
                            'race_confidence': smoothed_emotion.get('race_confidence', 0),
                            'face_confidence': smoothed_emotion.get('face_confidence', 0),
                            'face_embedding': face_embedding,
                            'cluster_info': cluster_info,
                            'timestamp': timestamp,
                            'metadata': frame_data['metadata']
                        })
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                        
        except Exception as e:
            logger.error(f"Single frame processing error: {e}")
    
    def _should_skip_frame(self, frame):
        """Determine if frame should be skipped based on motion"""
        # Simple motion detection
        if len(self.emotion_history) < 3:
            return False
            
        # Skip if emotion hasn't changed much
        recent_emotions = list(self.emotion_history)[-3:]
        if len(set(recent_emotions)) == 1:  # All same emotion
            return True
            
        return False
    
    def _detect_emotion(self, frame):
        """Detect emotion from frame dengan optimasi real-time"""
        try:
            # Resize frame untuk performa (optimasi untuk real-time)
            height, width = frame.shape[:2]
            if width > 480:  # Kurangi resolusi untuk performa lebih baik
                scale = 480 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Process dengan DeepFace menggunakan detector backend yang dinamis
            # Tambahkan analisis demografi untuk insight lebih dalam
            result = DeepFace.analyze(
                frame,
                actions=['emotion', 'age', 'gender', 'race'],
                detector_backend='mtcnn',  # Default ke MTCNN, bisa diubah via API
                enforce_detection=False,
                silent=True
            )
            
            if result and len(result) > 0:
                analysis = result[0]
                return {
                    'emotion': analysis.get('dominant_emotion', 'neutral'),
                    'emotion_confidence': max(analysis.get('emotion', {}).values()) if analysis.get('emotion') else 0,
                    'age': analysis.get('age', 0),
                    'gender': analysis.get('dominant_gender', 'unknown'),
                    'gender_confidence': max(analysis.get('gender', {}).values()) if analysis.get('gender') else 0,
                    'race': analysis.get('dominant_race', 'unknown'),
                    'race_confidence': max(analysis.get('race', {}).values()) if analysis.get('race') else 0,
                    'face_confidence': analysis.get('face_confidence', 0)
                }
                
        except Exception as e:
            logger.warning(f"Emotion detection error: {e}")
            
        return None
    
    def _extract_face_embedding(self, frame):
        """Extract face embedding for clustering"""
        try:
            # Extract face embedding using DeepFace
            embedding = DeepFace.represent(
                frame,
                model_name='ArcFace',
                detector_backend='mtcnn',
                enforce_detection=False,
                silent=True
            )
            
            if embedding and len(embedding) > 0:
                return embedding[0]  # Return the embedding vector
                
        except Exception as e:
            logger.warning(f"Face embedding extraction error: {e}")
            
        return None
    
    def _smooth_emotion(self):
        """Smooth emotion using history"""
        if not self.emotion_history:
            return {
                'emotion': 'neutral',
                'emotion_confidence': 0,
                'age': 0,
                'gender': 'unknown',
                'gender_confidence': 0,
                'race': 'unknown',
                'race_confidence': 0,
                'face_confidence': 0
            }
            
        # Use most common emotion from recent history
        emotions = [entry.get('emotion', 'neutral') if isinstance(entry, dict) else entry for entry in self.emotion_history]
        emotion_counts = Counter(emotions)
        dominant_emotion = emotion_counts.most_common(1)[0][0]
        
        # Get latest demographic data
        latest_data = self.emotion_history[-1] if self.emotion_history else {}
        if isinstance(latest_data, dict):
            return {
                'emotion': dominant_emotion,
                'emotion_confidence': latest_data.get('emotion_confidence', 0),
                'age': latest_data.get('age', 0),
                'gender': latest_data.get('gender', 'unknown'),
                'gender_confidence': latest_data.get('gender_confidence', 0),
                'race': latest_data.get('race', 'unknown'),
                'race_confidence': latest_data.get('race_confidence', 0),
                'face_confidence': latest_data.get('face_confidence', 0)
            }
        else:
            return {
                'emotion': dominant_emotion,
                'emotion_confidence': 0,
                'age': 0,
                'gender': 'unknown',
                'gender_confidence': 0,
                'race': 'unknown',
                'race_confidence': 0,
                'face_confidence': 0
            }

class FaceClustering:
    def __init__(self, similarity_threshold=0.4):
        self.similarity_threshold = similarity_threshold
        self.face_embeddings = {}  # {face_id: embedding}
        self.face_clusters = {}    # {cluster_id: [face_ids]}
        self.cluster_centers = {}  # {cluster_id: center_embedding}
        self.next_cluster_id = 1
        
    def add_face_embedding(self, face_id, embedding):
        """Add face embedding to clustering system"""
        self.face_embeddings[face_id] = embedding
        
        # Find best matching cluster
        best_cluster = self._find_best_cluster(embedding)
        
        if best_cluster is not None:
            # Add to existing cluster
            self.face_clusters[best_cluster].append(face_id)
            self._update_cluster_center(best_cluster)
        else:
            # Create new cluster
            cluster_id = self.next_cluster_id
            self.next_cluster_id += 1
            self.face_clusters[cluster_id] = [face_id]
            self.cluster_centers[cluster_id] = embedding.copy()
            
        return best_cluster if best_cluster is not None else cluster_id
    
    def _find_best_cluster(self, embedding):
        """Find the best matching cluster for an embedding"""
        best_cluster = None
        best_similarity = 0
        
        for cluster_id, center in self.cluster_centers.items():
            similarity = self._cosine_similarity(embedding, center)
            if similarity > self.similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_cluster = cluster_id
                
        return best_cluster
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
            
        return dot_product / (norm1 * norm2)
    
    def _update_cluster_center(self, cluster_id):
        """Update cluster center based on all faces in cluster"""
        if cluster_id not in self.face_clusters:
            return
            
        face_ids = self.face_clusters[cluster_id]
        embeddings = [self.face_embeddings[face_id] for face_id in face_ids if face_id in self.face_embeddings]
        
        if embeddings:
            import numpy as np
            self.cluster_centers[cluster_id] = np.mean(embeddings, axis=0)
    
    def get_cluster_info(self, cluster_id):
        """Get information about a specific cluster"""
        if cluster_id not in self.face_clusters:
            return None
            
        return {
            'cluster_id': cluster_id,
            'face_count': len(self.face_clusters[cluster_id]),
            'face_ids': self.face_clusters[cluster_id],
            'center_embedding': self.cluster_centers.get(cluster_id, None)
        }
    
    def get_all_clusters(self):
        """Get information about all clusters"""
        return {
            cluster_id: self.get_cluster_info(cluster_id)
            for cluster_id in self.face_clusters.keys()
        }

class EmotionAggregator:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.emotion_windows = {}
        self.face_clustering = FaceClustering()  # Add face clustering
        
    def add_emotion(self, student_id, emotion, timestamp):
        """Add emotion to student's window"""
        if student_id not in self.emotion_windows:
            self.emotion_windows[student_id] = deque(maxlen=self.window_size)
            
        self.emotion_windows[student_id].append({
            'emotion': emotion,
            'timestamp': timestamp
        })
    
    def get_dominant_emotion(self, student_id):
        """Get dominant emotion for student"""
        if student_id not in self.emotion_windows:
            return None
            
        window = self.emotion_windows[student_id]
        if not window:
            return None
            
        emotions = [entry['emotion'] for entry in window]
        emotion_counts = Counter(emotions)
        return emotion_counts.most_common(1)[0][0]
    
    def get_emotion_trend(self, student_id):
        """Get emotion trend for student"""
        if student_id not in self.emotion_windows:
            return []
            
        window = self.emotion_windows[student_id]
        return [entry['emotion'] for entry in window]

# Global instances
emotion_processor = EmotionProcessor()
emotion_aggregator = EmotionAggregator()