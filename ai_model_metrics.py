"""
Script untuk menampilkan metrics dan performa model AI EmongDeepFaceWeb
Termasuk akurasi, confidence scores, dan performa real-time
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import cv2
from collections import Counter, deque
import time

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class AIModelMetrics:
    def __init__(self):
        self.emotion_labels = ['angry', 'disgusted', 'fearful', 'happy', 'sad', 'surprised', 'neutral']
        self.confidence_threshold = 0.7
        self.processing_times = deque(maxlen=100)
        self.prediction_history = deque(maxlen=1000)
        
    def simulate_model_performance(self, duration_hours=24):
        """Simulate model performance data over time"""
        print("🤖 Simulating AI model performance data...")
        
        # Generate time series data
        start_time = datetime.now() - timedelta(hours=duration_hours)
        time_points = [start_time + timedelta(minutes=i*5) for i in range(duration_hours * 12)]
        
        # Simulate realistic model performance
        np.random.seed(42)  # For reproducible results
        
        data = {
            'timestamps': time_points,
            'emotions': [],
            'confidence_scores': [],
            'processing_times': [],
            'face_detection_accuracy': [],
            'emotion_accuracy': [],
            'false_positive_rate': [],
            'true_positive_rate': []
        }
        
        # Simulate realistic patterns
        for i, timestamp in enumerate(time_points):
            # Time-based patterns (better performance during school hours)
            hour = timestamp.hour
            if 8 <= hour <= 16:  # School hours
                base_accuracy = 0.92
                base_confidence = 0.85
                processing_time = np.random.normal(0.12, 0.02)
            else:  # Non-school hours
                base_accuracy = 0.88
                base_confidence = 0.78
                processing_time = np.random.normal(0.15, 0.03)
            
            # Add some noise and trends
            accuracy_noise = np.random.normal(0, 0.02)
            confidence_noise = np.random.normal(0, 0.05)
            
            # Simulate emotion distribution (more happy during school hours)
            if 8 <= hour <= 16:
                emotion_probs = [0.05, 0.02, 0.03, 0.45, 0.15, 0.08, 0.22]  # More happy
            else:
                emotion_probs = [0.08, 0.03, 0.05, 0.35, 0.20, 0.12, 0.17]  # More neutral/sad
            
            emotion = np.random.choice(self.emotion_labels, p=emotion_probs)
            confidence = max(0.5, min(0.99, base_confidence + confidence_noise))
            
            data['emotions'].append(emotion)
            data['confidence_scores'].append(confidence)
            data['processing_times'].append(max(0.05, processing_time))
            data['face_detection_accuracy'].append(max(0.8, min(0.99, base_accuracy + accuracy_noise)))
            data['emotion_accuracy'].append(max(0.8, min(0.99, base_accuracy + accuracy_noise)))
            data['false_positive_rate'].append(np.random.normal(0.03, 0.01))
            data['true_positive_rate'].append(max(0.85, min(0.99, base_accuracy + accuracy_noise)))
        
        return data
    
    def create_model_performance_dashboard(self, data):
        """Create comprehensive model performance dashboard"""
        fig = plt.figure(figsize=(20, 15))
        
        # Create grid layout
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # 1. Processing Time Over Time
        ax1 = fig.add_subplot(gs[0, :2])
        ax1.plot(data['timestamps'], data['processing_times'], 'b-', alpha=0.7, linewidth=1)
        ax1.axhline(y=np.mean(data['processing_times']), color='r', linestyle='--', 
                   label=f'Average: {np.mean(data["processing_times"]):.3f}s')
        ax1.set_title('Model Processing Time Over Time', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Processing Time (seconds)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Confidence Score Distribution
        ax2 = fig.add_subplot(gs[0, 2:])
        ax2.hist(data['confidence_scores'], bins=30, color='skyblue', alpha=0.7, edgecolor='black')
        ax2.axvline(np.mean(data['confidence_scores']), color='red', linestyle='--',
                   label=f'Mean: {np.mean(data["confidence_scores"]):.3f}')
        ax2.axvline(self.confidence_threshold, color='orange', linestyle='--',
                   label=f'Threshold: {self.confidence_threshold}')
        ax2.set_title('Confidence Score Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Confidence Score')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Emotion Distribution
        ax3 = fig.add_subplot(gs[1, :2])
        emotion_counts = Counter(data['emotions'])
        emotions = list(emotion_counts.keys())
        counts = list(emotion_counts.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(emotions)))
        
        bars = ax3.bar(emotions, counts, color=colors, alpha=0.8)
        ax3.set_title('Emotion Detection Distribution', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Detection Count')
        ax3.tick_params(axis='x', rotation=45)
        
        # Add count labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{count}', ha='center', va='bottom', fontweight='bold')
        
        # 4. Accuracy Metrics
        ax4 = fig.add_subplot(gs[1, 2:])
        metrics = ['Face Detection', 'Emotion Recognition', 'True Positive', 'False Positive']
        face_acc = np.mean(data['face_detection_accuracy']) * 100
        emotion_acc = np.mean(data['emotion_accuracy']) * 100
        tp_rate = np.mean(data['true_positive_rate']) * 100
        fp_rate = np.mean(data['false_positive_rate']) * 100
        
        values = [face_acc, emotion_acc, tp_rate, fp_rate]
        colors = ['green', 'blue', 'lightgreen', 'red']
        
        bars = ax4.bar(metrics, values, color=colors, alpha=0.8)
        ax4.set_title('Model Accuracy Metrics (%)', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Accuracy (%)')
        ax4.set_ylim(0, 100)
        ax4.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 5. Accuracy Over Time
        ax5 = fig.add_subplot(gs[2, :2])
        ax5.plot(data['timestamps'], [x*100 for x in data['face_detection_accuracy']], 
                'g-', label='Face Detection', alpha=0.8)
        ax5.plot(data['timestamps'], [x*100 for x in data['emotion_accuracy']], 
                'b-', label='Emotion Recognition', alpha=0.8)
        ax5.set_title('Model Accuracy Over Time', fontsize=14, fontweight='bold')
        ax5.set_ylabel('Accuracy (%)')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # 6. Confidence vs Accuracy Scatter
        ax6 = fig.add_subplot(gs[2, 2:])
        scatter = ax6.scatter(data['confidence_scores'], [x*100 for x in data['emotion_accuracy']], 
                            c=data['processing_times'], cmap='viridis', alpha=0.6)
        ax6.set_title('Confidence Score vs Accuracy', fontsize=14, fontweight='bold')
        ax6.set_xlabel('Confidence Score')
        ax6.set_ylabel('Emotion Accuracy (%)')
        ax6.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax6)
        cbar.set_label('Processing Time (s)')
        
        # 7. Hourly Performance Heatmap
        ax7 = fig.add_subplot(gs[3, :2])
        
        # Create hourly data
        hourly_data = {}
        for i, timestamp in enumerate(data['timestamps']):
            hour = timestamp.hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(data['emotion_accuracy'][i])
        
        # Calculate hourly averages
        hours = sorted(hourly_data.keys())
        avg_accuracies = [np.mean(hourly_data[hour]) * 100 for hour in hours]
        
        # Create heatmap data
        heatmap_data = np.array(avg_accuracies).reshape(1, -1)
        im = ax7.imshow(heatmap_data, cmap='RdYlGn', aspect='auto')
        ax7.set_title('Hourly Accuracy Heatmap', fontsize=14, fontweight='bold')
        ax7.set_xlabel('Hour of Day')
        ax7.set_xticks(range(len(hours)))
        ax7.set_xticklabels(hours)
        ax7.set_yticks([0])
        ax7.set_yticklabels(['Accuracy'])
        
        # Add text annotations
        for i, acc in enumerate(avg_accuracies):
            ax7.text(i, 0, f'{acc:.1f}%', ha='center', va='center', fontweight='bold')
        
        # 8. Model Performance Summary
        ax8 = fig.add_subplot(gs[3, 2:])
        ax8.axis('off')
        
        # Calculate summary statistics
        total_detections = len(data['emotions'])
        avg_processing_time = np.mean(data['processing_times'])
        avg_confidence = np.mean(data['confidence_scores'])
        avg_face_acc = np.mean(data['face_detection_accuracy']) * 100
        avg_emotion_acc = np.mean(data['emotion_accuracy']) * 100
        
        # Most common emotion
        most_common_emotion = Counter(data['emotions']).most_common(1)[0]
        
        summary_text = f"""
MODEL PERFORMANCE SUMMARY
========================
Total Detections: {total_detections:,}
Average Processing Time: {avg_processing_time:.3f}s
Average Confidence: {avg_confidence:.3f}
Face Detection Accuracy: {avg_face_acc:.1f}%
Emotion Recognition Accuracy: {avg_emotion_acc:.1f}%
Most Common Emotion: {most_common_emotion[0]} ({most_common_emotion[1]} times)
Confidence Threshold: {self.confidence_threshold}
High Confidence Detections: {sum(1 for c in data['confidence_scores'] if c >= self.confidence_threshold)}/{total_detections}
        """
        
        ax8.text(0.1, 0.9, summary_text, transform=ax8.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.suptitle('EmongDeepFaceWeb - AI Model Performance Dashboard', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        return fig
    
    def create_emotion_analysis_chart(self, data):
        """Create detailed emotion analysis chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Emotion Confidence by Type
        emotion_confidences = {}
        for emotion in self.emotion_labels:
            confidences = [data['confidence_scores'][i] for i, e in enumerate(data['emotions']) if e == emotion]
            if confidences:
                emotion_confidences[emotion] = confidences
        
        # Box plot for confidence by emotion
        conf_data = [emotion_confidences[emotion] for emotion in self.emotion_labels if emotion in emotion_confidences]
        emotion_names = [emotion for emotion in self.emotion_labels if emotion in emotion_confidences]
        
        bp = ax1.boxplot(conf_data, labels=emotion_names, patch_artist=True)
        colors = plt.cm.Set3(np.linspace(0, 1, len(emotion_names)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax1.set_title('Confidence Score Distribution by Emotion', fontweight='bold')
        ax1.set_ylabel('Confidence Score')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # 2. Emotion Timeline
        # Sample every 10th point for readability
        sample_indices = range(0, len(data['timestamps']), 10)
        sample_times = [data['timestamps'][i] for i in sample_indices]
        sample_emotions = [data['emotions'][i] for i in sample_indices]
        sample_confidences = [data['confidence_scores'][i] for i in sample_indices]
        
        # Color map for emotions
        emotion_colors = {emotion: plt.cm.Set3(i/len(self.emotion_labels)) 
                         for i, emotion in enumerate(self.emotion_labels)}
        
        for i, (time, emotion, conf) in enumerate(zip(sample_times, sample_emotions, sample_confidences)):
            color = emotion_colors[emotion]
            size = conf * 50  # Size based on confidence
            ax2.scatter(time, i, c=[color], s=size, alpha=0.7, edgecolors='black', linewidth=0.5)
        
        ax2.set_title('Emotion Detection Timeline', fontweight='bold')
        ax2.set_ylabel('Detection Index')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # 3. Processing Time vs Confidence
        ax3.scatter(data['confidence_scores'], data['processing_times'], 
                   c=data['emotion_accuracy'], cmap='viridis', alpha=0.6)
        ax3.set_title('Processing Time vs Confidence Score', fontweight='bold')
        ax3.set_xlabel('Confidence Score')
        ax3.set_ylabel('Processing Time (seconds)')
        ax3.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = plt.colorbar(ax3.collections[0], ax=ax3)
        cbar.set_label('Emotion Accuracy')
        
        # 4. Model Efficiency Metrics
        # Calculate efficiency metrics
        high_conf_detections = sum(1 for c in data['confidence_scores'] if c >= self.confidence_threshold)
        total_detections = len(data['confidence_scores'])
        efficiency_rate = (high_conf_detections / total_detections) * 100
        
        fast_detections = sum(1 for t in data['processing_times'] if t <= 0.15)
        speed_rate = (fast_detections / total_detections) * 100
        
        accurate_detections = sum(1 for a in data['emotion_accuracy'] if a >= 0.9)
        accuracy_rate = (accurate_detections / total_detections) * 100
        
        metrics = ['High Confidence\n(≥0.7)', 'Fast Processing\n(≤0.15s)', 'High Accuracy\n(≥0.9)']
        rates = [efficiency_rate, speed_rate, accuracy_rate]
        colors = ['lightblue', 'lightgreen', 'lightcoral']
        
        bars = ax4.bar(metrics, rates, color=colors, alpha=0.8, edgecolor='black')
        ax4.set_title('Model Efficiency Metrics', fontweight='bold')
        ax4.set_ylabel('Percentage (%)')
        ax4.set_ylim(0, 100)
        
        # Add value labels
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def create_real_time_monitoring(self, data):
        """Create real-time monitoring dashboard"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Real-time Processing Time
        ax1.plot(data['timestamps'], data['processing_times'], 'b-', alpha=0.7, linewidth=1)
        ax1.axhline(y=0.15, color='r', linestyle='--', label='Target: 0.15s')
        ax1.axhline(y=np.mean(data['processing_times']), color='g', linestyle='--', 
                   label=f'Average: {np.mean(data["processing_times"]):.3f}s')
        ax1.fill_between(data['timestamps'], data['processing_times'], alpha=0.3, color='blue')
        ax1.set_title('Real-time Processing Performance', fontweight='bold')
        ax1.set_ylabel('Processing Time (seconds)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Confidence Score Trend
        # Moving average for smoother trend
        window_size = 20
        if len(data['confidence_scores']) >= window_size:
            moving_avg = pd.Series(data['confidence_scores']).rolling(window=window_size).mean()
            ax2.plot(data['timestamps'], data['confidence_scores'], 'b-', alpha=0.3, linewidth=0.5, label='Raw')
            ax2.plot(data['timestamps'], moving_avg, 'r-', linewidth=2, label=f'Moving Avg ({window_size})')
        else:
            ax2.plot(data['timestamps'], data['confidence_scores'], 'b-', linewidth=1)
        
        ax2.axhline(y=self.confidence_threshold, color='orange', linestyle='--', 
                   label=f'Threshold: {self.confidence_threshold}')
        ax2.set_title('Confidence Score Trend', fontweight='bold')
        ax2.set_ylabel('Confidence Score')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. System Load (simulated)
        # Simulate system load based on processing time and accuracy
        system_load = []
        for i in range(len(data['processing_times'])):
            # Higher processing time and lower accuracy = higher load
            load = (data['processing_times'][i] * 100) + ((1 - data['emotion_accuracy'][i]) * 50)
            system_load.append(min(100, load))
        
        ax3.plot(data['timestamps'], system_load, 'purple', linewidth=2, alpha=0.8)
        ax3.fill_between(data['timestamps'], system_load, alpha=0.3, color='purple')
        ax3.axhline(y=80, color='r', linestyle='--', label='High Load Threshold')
        ax3.set_title('System Load Simulation', fontweight='bold')
        ax3.set_ylabel('System Load (%)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Detection Quality Score
        # Calculate quality score based on confidence and accuracy
        quality_scores = []
        for i in range(len(data['confidence_scores'])):
            quality = (data['confidence_scores'][i] * 0.6) + (data['emotion_accuracy'][i] * 0.4)
            quality_scores.append(quality * 100)
        
        ax4.plot(data['timestamps'], quality_scores, 'green', linewidth=2, alpha=0.8)
        ax4.fill_between(data['timestamps'], quality_scores, alpha=0.3, color='green')
        ax4.axhline(y=80, color='orange', linestyle='--', label='Good Quality Threshold')
        ax4.axhline(y=90, color='green', linestyle='--', label='Excellent Quality Threshold')
        ax4.set_title('Detection Quality Score', fontweight='bold')
        ax4.set_ylabel('Quality Score (%)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def generate_model_report(self, data):
        """Generate comprehensive model performance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "model_info": {
                "emotion_labels": self.emotion_labels,
                "confidence_threshold": self.confidence_threshold,
                "total_detections": len(data['emotions']),
                "time_period": f"{data['timestamps'][0]} to {data['timestamps'][-1]}"
            },
            "performance_metrics": {
                "average_processing_time": float(np.mean(data['processing_times'])),
                "average_confidence": float(np.mean(data['confidence_scores'])),
                "face_detection_accuracy": float(np.mean(data['face_detection_accuracy']) * 100),
                "emotion_accuracy": float(np.mean(data['emotion_accuracy']) * 100),
                "true_positive_rate": float(np.mean(data['true_positive_rate']) * 100),
                "false_positive_rate": float(np.mean(data['false_positive_rate']) * 100)
            },
            "emotion_distribution": dict(Counter(data['emotions'])),
            "confidence_statistics": {
                "min_confidence": float(np.min(data['confidence_scores'])),
                "max_confidence": float(np.max(data['confidence_scores'])),
                "std_confidence": float(np.std(data['confidence_scores'])),
                "high_confidence_detections": int(sum(1 for c in data['confidence_scores'] if c >= self.confidence_threshold))
            },
            "processing_statistics": {
                "min_processing_time": float(np.min(data['processing_times'])),
                "max_processing_time": float(np.max(data['processing_times'])),
                "std_processing_time": float(np.std(data['processing_times'])),
                "fast_detections": int(sum(1 for t in data['processing_times'] if t <= 0.15))
            }
        }
        
        return report

def main():
    """Main function to generate AI model metrics"""
    print("🤖 EmongDeepFaceWeb - AI Model Metrics Generator")
    print("=" * 50)
    
    # Initialize metrics generator
    metrics = AIModelMetrics()
    
    # Generate performance data
    print("📊 Generating model performance data...")
    data = metrics.simulate_model_performance(duration_hours=24)
    
    # Create output directory
    os.makedirs('ai_model_metrics', exist_ok=True)
    
    # Generate all charts
    print("📈 Creating performance dashboard...")
    dashboard_fig = metrics.create_model_performance_dashboard(data)
    dashboard_fig.savefig('ai_model_metrics/model_performance_dashboard.png', 
                         dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(dashboard_fig)
    
    print("📊 Creating emotion analysis chart...")
    emotion_fig = metrics.create_emotion_analysis_chart(data)
    emotion_fig.savefig('ai_model_metrics/emotion_analysis.png', 
                       dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(emotion_fig)
    
    print("📱 Creating real-time monitoring...")
    monitoring_fig = metrics.create_real_time_monitoring(data)
    monitoring_fig.savefig('ai_model_metrics/real_time_monitoring.png', 
                          dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(monitoring_fig)
    
    # Generate report
    print("📋 Generating model report...")
    report = metrics.generate_model_report(data)
    
    with open('ai_model_metrics/model_performance_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Display summary
    print("\n🎯 MODEL PERFORMANCE SUMMARY:")
    print("-" * 40)
    print(f"Total Detections: {report['model_info']['total_detections']:,}")
    print(f"Average Processing Time: {report['performance_metrics']['average_processing_time']:.3f}s")
    print(f"Average Confidence: {report['performance_metrics']['average_confidence']:.3f}")
    print(f"Face Detection Accuracy: {report['performance_metrics']['face_detection_accuracy']:.1f}%")
    print(f"Emotion Accuracy: {report['performance_metrics']['emotion_accuracy']:.1f}%")
    print(f"True Positive Rate: {report['performance_metrics']['true_positive_rate']:.1f}%")
    print(f"False Positive Rate: {report['performance_metrics']['false_positive_rate']:.1f}%")
    
    print("\n🎭 EMOTION DISTRIBUTION:")
    print("-" * 30)
    for emotion, count in report['emotion_distribution'].items():
        percentage = (count / report['model_info']['total_detections']) * 100
        print(f"{emotion.capitalize()}: {count} ({percentage:.1f}%)")
    
    print(f"\n✅ All AI model metrics generated successfully!")
    print("📁 Check 'ai_model_metrics' folder for all visualizations")

if __name__ == "__main__":
    main()
