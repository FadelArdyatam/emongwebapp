"""
Script untuk visualisasi metrics dan hasil dari EmongDeepFaceWeb
Menggunakan matplotlib untuk menampilkan data real-time dan analytics
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import seaborn as sns
from collections import Counter
import json
import os

# Set style untuk visualisasi yang lebih menarik
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class EmongMetricsVisualizer:
    def __init__(self):
        self.fig_size = (12, 8)
        self.dpi = 100
        
    def create_emotion_distribution_chart(self, emotion_data):
        """Chart distribusi emosi harian"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Pie chart untuk distribusi emosi
        emotions = list(emotion_data.keys())
        values = list(emotion_data.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        
        wedges, texts, autotexts = ax1.pie(values, labels=emotions, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        ax1.set_title('Distribusi Emosi Siswa\n(Data Real-time)', fontsize=14, fontweight='bold')
        
        # Bar chart untuk perbandingan
        bars = ax2.bar(emotions, values, color=colors, alpha=0.8)
        ax2.set_title('Jumlah Deteksi per Emosi', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Jumlah Deteksi')
        ax2.tick_params(axis='x', rotation=45)
        
        # Tambahkan nilai di atas bar
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def create_performance_metrics(self, performance_data):
        """Chart metrics performa sistem"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # CPU Usage
        time_points = performance_data['time_points']
        cpu_usage = performance_data['cpu_usage']
        memory_usage = performance_data['memory_usage']
        
        ax1.plot(time_points, cpu_usage, 'b-', linewidth=2, marker='o', markersize=4)
        ax1.fill_between(time_points, cpu_usage, alpha=0.3, color='blue')
        ax1.set_title('CPU Usage (%)', fontweight='bold')
        ax1.set_ylabel('CPU Usage (%)')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        
        # Memory Usage
        ax2.plot(time_points, memory_usage, 'r-', linewidth=2, marker='s', markersize=4)
        ax2.fill_between(time_points, memory_usage, alpha=0.3, color='red')
        ax2.set_title('Memory Usage (GB)', fontweight='bold')
        ax2.set_ylabel('Memory (GB)')
        ax2.grid(True, alpha=0.3)
        
        # Response Time
        response_times = performance_data['response_times']
        ax3.hist(response_times, bins=20, color='green', alpha=0.7, edgecolor='black')
        ax3.axvline(np.mean(response_times), color='red', linestyle='--', 
                   label=f'Average: {np.mean(response_times):.2f}ms')
        ax3.set_title('Response Time Distribution', fontweight='bold')
        ax3.set_xlabel('Response Time (ms)')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Concurrent Users
        concurrent_users = performance_data['concurrent_users']
        ax4.bar(range(len(concurrent_users)), concurrent_users, color='orange', alpha=0.8)
        ax4.set_title('Concurrent Users Over Time', fontweight='bold')
        ax4.set_xlabel('Time Period')
        ax4.set_ylabel('Number of Users')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_emotion_timeline(self, timeline_data):
        """Timeline emosi siswa sepanjang hari"""
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Data timeline
        time_points = timeline_data['time_points']
        emotions = timeline_data['emotions']
        confidence_scores = timeline_data['confidence_scores']
        
        # Color mapping untuk emosi
        emotion_colors = {
            'happy': '#FF6B6B',
            'sad': '#4ECDC4', 
            'angry': '#FF4757',
            'neutral': '#747D8C',
            'surprised': '#FFA502',
            'fearful': '#5F27CD',
            'disgusted': '#00D2D3'
        }
        
        # Plot timeline
        for i, (time, emotion, confidence) in enumerate(zip(time_points, emotions, confidence_scores)):
            color = emotion_colors.get(emotion, '#000000')
            size = confidence * 100  # Ukuran berdasarkan confidence
            ax.scatter(time, i, c=color, s=size, alpha=0.7, edgecolors='black', linewidth=0.5)
        
        ax.set_title('Timeline Emosi Siswa - Real-time Detection', fontsize=16, fontweight='bold')
        ax.set_xlabel('Waktu')
        ax.set_ylabel('Deteksi ke-')
        ax.grid(True, alpha=0.3)
        
        # Legend
        legend_elements = [plt.scatter([], [], c=color, s=50, label=emotion) 
                          for emotion, color in emotion_colors.items()]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        # Format waktu
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return fig
    
    def create_accuracy_metrics(self, accuracy_data):
        """Chart akurasi model dan confidence scores"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Model Accuracy per Emotion
        emotions = list(accuracy_data['emotion_accuracy'].keys())
        accuracies = list(accuracy_data['emotion_accuracy'].values())
        
        bars = ax1.bar(emotions, accuracies, color='skyblue', alpha=0.8, edgecolor='navy')
        ax1.set_title('Akurasi Model per Emosi', fontweight='bold')
        ax1.set_ylabel('Akurasi (%)')
        ax1.set_ylim(0, 100)
        ax1.tick_params(axis='x', rotation=45)
        
        # Tambahkan nilai di atas bar
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{acc:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # Confidence Score Distribution
        confidence_scores = accuracy_data['confidence_distribution']
        ax2.hist(confidence_scores, bins=30, color='lightgreen', alpha=0.7, edgecolor='black')
        ax2.axvline(np.mean(confidence_scores), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(confidence_scores):.3f}')
        ax2.set_title('Distribusi Confidence Score', fontweight='bold')
        ax2.set_xlabel('Confidence Score')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Processing Time per Frame
        processing_times = accuracy_data['processing_times']
        ax3.plot(processing_times, 'b-', linewidth=2, marker='o', markersize=3)
        ax3.axhline(np.mean(processing_times), color='red', linestyle='--', 
                   label=f'Average: {np.mean(processing_times):.3f}s')
        ax3.set_title('Processing Time per Frame', fontweight='bold')
        ax3.set_xlabel('Frame Number')
        ax3.set_ylabel('Processing Time (seconds)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # False Positive vs True Positive
        fp_rate = accuracy_data['false_positive_rate']
        tp_rate = accuracy_data['true_positive_rate']
        
        categories = ['False Positive', 'True Positive']
        rates = [fp_rate, tp_rate]
        colors = ['red', 'green']
        
        bars = ax4.bar(categories, rates, color=colors, alpha=0.7)
        ax4.set_title('False Positive vs True Positive Rate', fontweight='bold')
        ax4.set_ylabel('Rate (%)')
        ax4.set_ylim(0, 100)
        
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def create_user_activity_dashboard(self, user_data):
        """Dashboard aktivitas user"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Login Activity per Hour
        hours = list(range(24))
        login_counts = user_data['login_activity']
        
        ax1.bar(hours, login_counts, color='steelblue', alpha=0.8)
        ax1.set_title('Aktivitas Login per Jam', fontweight='bold')
        ax1.set_xlabel('Jam')
        ax1.set_ylabel('Jumlah Login')
        ax1.set_xticks(range(0, 24, 2))
        ax1.grid(True, alpha=0.3)
        
        # Feature Usage
        features = list(user_data['feature_usage'].keys())
        usage_counts = list(user_data['feature_usage'].values())
        
        bars = ax2.barh(features, usage_counts, color='lightcoral', alpha=0.8)
        ax2.set_title('Penggunaan Fitur', fontweight='bold')
        ax2.set_xlabel('Jumlah Penggunaan')
        
        # Tambahkan nilai di ujung bar
        for i, (bar, count) in enumerate(zip(bars, usage_counts)):
            width = bar.get_width()
            ax2.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                    f'{count}', ha='left', va='center', fontweight='bold')
        
        # User Role Distribution
        roles = list(user_data['role_distribution'].keys())
        role_counts = list(user_data['role_distribution'].values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        wedges, texts, autotexts = ax3.pie(role_counts, labels=roles, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        ax3.set_title('Distribusi Role User', fontweight='bold')
        
        # Session Duration
        session_durations = user_data['session_durations']
        ax4.hist(session_durations, bins=20, color='gold', alpha=0.7, edgecolor='black')
        ax4.axvline(np.mean(session_durations), color='red', linestyle='--', 
                   label=f'Average: {np.mean(session_durations):.1f} min')
        ax4.set_title('Durasi Session User', fontweight='bold')
        ax4.set_xlabel('Durasi (menit)')
        ax4.set_ylabel('Frequency')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_rtsp_performance_chart(self, rtsp_data):
        """Chart performa RTSP connection"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Connection Status
        time_points = rtsp_data['time_points']
        connection_status = rtsp_data['connection_status']
        
        # Convert status to numeric for plotting
        status_numeric = [1 if status == 'connected' else 0 for status in connection_status]
        
        ax1.fill_between(time_points, status_numeric, alpha=0.7, color='green', 
                        label='Connected', step='post')
        ax1.set_title('RTSP Connection Status', fontweight='bold')
        ax1.set_ylabel('Status (1=Connected, 0=Disconnected)')
        ax1.set_ylim(-0.1, 1.1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Frame Rate
        frame_rates = rtsp_data['frame_rates']
        ax2.plot(time_points, frame_rates, 'b-', linewidth=2, marker='o', markersize=3)
        ax2.set_title('Frame Rate (FPS)', fontweight='bold')
        ax2.set_ylabel('FPS')
        ax2.grid(True, alpha=0.3)
        
        # Latency
        latencies = rtsp_data['latencies']
        ax3.plot(time_points, latencies, 'r-', linewidth=2, marker='s', markersize=3)
        ax3.set_title('Network Latency', fontweight='bold')
        ax3.set_ylabel('Latency (ms)')
        ax3.grid(True, alpha=0.3)
        
        # Bandwidth Usage
        bandwidth = rtsp_data['bandwidth_usage']
        ax4.plot(time_points, bandwidth, 'purple', linewidth=2, marker='^', markersize=3)
        ax4.set_title('Bandwidth Usage', fontweight='bold')
        ax4.set_ylabel('Bandwidth (Mbps)')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_comparison_chart(self, comparison_data):
        """Chart perbandingan sebelum dan sesudah implementasi"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Before vs After Metrics
        metrics = ['Accuracy', 'Speed', 'User Satisfaction', 'Cost Efficiency']
        before_values = comparison_data['before']
        after_values = comparison_data['after']
        
        x = np.arange(len(metrics))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, before_values, width, label='Sebelum', 
                       color='lightcoral', alpha=0.8)
        bars2 = ax1.bar(x + width/2, after_values, width, label='Sesudah', 
                       color='lightgreen', alpha=0.8)
        
        ax1.set_title('Perbandingan Performa Sistem', fontweight='bold')
        ax1.set_ylabel('Score (0-100)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(metrics)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Tambahkan nilai di atas bar
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # ROI Analysis
        months = list(range(1, 13))
        roi_values = comparison_data['roi_values']
        
        ax2.plot(months, roi_values, 'b-', linewidth=3, marker='o', markersize=6)
        ax2.fill_between(months, roi_values, alpha=0.3, color='blue')
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax2.set_title('ROI Analysis (12 Bulan)', fontweight='bold')
        ax2.set_xlabel('Bulan')
        ax2.set_ylabel('ROI (%)')
        ax2.grid(True, alpha=0.3)
        
        # Tambahkan break-even point
        break_even = next((i for i, val in enumerate(roi_values) if val >= 0), None)
        if break_even is not None:
            ax2.axvline(x=break_even+1, color='red', linestyle=':', alpha=0.7,
                       label=f'Break-even: Bulan {break_even+1}')
            ax2.legend()
        
        plt.tight_layout()
        return fig

def generate_sample_data():
    """Generate sample data untuk demo"""
    
    # Emotion distribution data
    emotion_data = {
        'happy': 45.2,
        'neutral': 28.7,
        'sad': 12.3,
        'surprised': 8.1,
        'angry': 3.8,
        'fearful': 1.5,
        'disgusted': 0.4
    }
    
    # Performance metrics
    time_points = pd.date_range(start='2024-01-01 08:00', periods=24, freq='H')
    performance_data = {
        'time_points': time_points,
        'cpu_usage': np.random.normal(45, 10, 24).clip(0, 100),
        'memory_usage': np.random.normal(2.1, 0.5, 24).clip(0, 8),
        'response_times': np.random.normal(120, 30, 100).clip(50, 300),
        'concurrent_users': np.random.poisson(25, 24)
    }
    
    # Emotion timeline
    timeline_data = {
        'time_points': pd.date_range(start='2024-01-01 08:00', periods=50, freq='15min'),
        'emotions': np.random.choice(['happy', 'sad', 'neutral', 'surprised', 'angry'], 50),
        'confidence_scores': np.random.uniform(0.6, 0.95, 50)
    }
    
    # Accuracy metrics
    accuracy_data = {
        'emotion_accuracy': {
            'happy': 94.2,
            'sad': 89.1,
            'neutral': 91.5,
            'surprised': 87.3,
            'angry': 92.8,
            'fearful': 85.6,
            'disgusted': 88.9
        },
        'confidence_distribution': np.random.beta(8, 2, 1000),
        'processing_times': np.random.normal(0.15, 0.03, 100),
        'false_positive_rate': 3.2,
        'true_positive_rate': 94.8
    }
    
    # User activity data
    user_data = {
        'login_activity': np.random.poisson(5, 24),
        'feature_usage': {
            'Emotion Detection': 89,
            'RTSP Testing': 67,
            'Reports': 34,
            'Student Management': 78,
            'Dashboard': 156
        },
        'role_distribution': {
            'Admin': 5,
            'Guru': 25,
            'Orang Tua': 15
        },
        'session_durations': np.random.normal(45, 15, 100).clip(5, 120)
    }
    
    # RTSP performance data
    rtsp_data = {
        'time_points': pd.date_range(start='2024-01-01 08:00', periods=20, freq='30min'),
        'connection_status': ['connected'] * 15 + ['disconnected'] * 2 + ['connected'] * 3,
        'frame_rates': np.random.normal(25, 3, 20).clip(15, 30),
        'latencies': np.random.normal(50, 10, 20).clip(20, 100),
        'bandwidth_usage': np.random.normal(2.5, 0.5, 20).clip(1, 5)
    }
    
    # Comparison data
    comparison_data = {
        'before': [65, 70, 60, 55],
        'after': [94, 95, 88, 85],
        'roi_values': [-20, -15, -8, -2, 5, 12, 18, 25, 32, 38, 45, 52]
    }
    
    return {
        'emotion_data': emotion_data,
        'performance_data': performance_data,
        'timeline_data': timeline_data,
        'accuracy_data': accuracy_data,
        'user_data': user_data,
        'rtsp_data': rtsp_data,
        'comparison_data': comparison_data
    }

def main():
    """Main function untuk generate semua charts"""
    print("🚀 Generating EmongDeepFaceWeb Metrics Visualization...")
    
    # Initialize visualizer
    visualizer = EmongMetricsVisualizer()
    
    # Generate sample data
    data = generate_sample_data()
    
    # Create output directory
    os.makedirs('metrics_charts', exist_ok=True)
    
    # Generate all charts
    charts = [
        ('emotion_distribution', visualizer.create_emotion_distribution_chart(data['emotion_data'])),
        ('performance_metrics', visualizer.create_performance_metrics(data['performance_data'])),
        ('emotion_timeline', visualizer.create_emotion_timeline(data['timeline_data'])),
        ('accuracy_metrics', visualizer.create_accuracy_metrics(data['accuracy_data'])),
        ('user_activity', visualizer.create_user_activity_dashboard(data['user_data'])),
        ('rtsp_performance', visualizer.create_rtsp_performance_chart(data['rtsp_data'])),
        ('comparison_chart', visualizer.create_comparison_chart(data['comparison_data']))
    ]
    
    # Save charts
    for name, fig in charts:
        filename = f'metrics_charts/{name}.png'
        fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✅ Saved: {filename}")
        plt.close(fig)
    
    # Generate summary report
    generate_summary_report(data)
    
    print("🎉 All metrics charts generated successfully!")
    print("📁 Check 'metrics_charts' folder for all visualizations")

def generate_summary_report(data):
    """Generate summary report dalam format JSON"""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "system_overview": {
            "total_emotion_detections": 1250,
            "average_accuracy": 91.2,
            "average_processing_time": "0.15s",
            "concurrent_users": 25,
            "system_uptime": "99.8%"
        },
        "emotion_analysis": data['emotion_data'],
        "performance_summary": {
            "average_cpu_usage": f"{np.mean(data['performance_data']['cpu_usage']):.1f}%",
            "average_memory_usage": f"{np.mean(data['performance_data']['memory_usage']):.2f}GB",
            "average_response_time": f"{np.mean(data['performance_data']['response_times']):.0f}ms"
        },
        "user_engagement": {
            "total_users": 45,
            "active_sessions": 23,
            "most_used_feature": "Dashboard",
            "average_session_duration": f"{np.mean(data['user_data']['session_durations']):.1f} minutes"
        }
    }
    
    with open('metrics_charts/summary_report.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("📊 Summary report generated: metrics_charts/summary_report.json")

if __name__ == "__main__":
    main()
