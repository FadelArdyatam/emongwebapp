# 🔧 Panduan Penggunaan Worker EMONG

## 📋 Daftar Worker yang Tersedia

### 1. **Emotion Stream Worker** (`emotion_stream_worker.py`)
- **Tujuan**: Memproses data emosi real-time dari Redis Stream
- **Fungsi**: 
  - Mengagregasi data emosi per hari per siswa
  - Menghitung risk score harian
  - Menyimpan data ke Redis untuk akses cepat

### 2. **Notification Worker** (`notification_worker.py`)
- **Tujuan**: Mengirim notifikasi email dan push notification
- **Fungsi**:
  - Kirim email ke parent/guru
  - Kirim push notification real-time
  - Support HTML email templates

### 3. **Report Worker** (`report_worker.py`)
- **Tujuan**: Generate laporan PDF/Excel
- **Fungsi**:
  - Generate laporan emosi siswa
  - Generate laporan ringkasan harian
  - Export data ke berbagai format

### 4. **Scheduler Worker** (`scheduler_worker.py`)
- **Tujuan**: Menangani tugas terjadwal
- **Fungsi**:
  - Cleanup data lama
  - Generate laporan otomatis
  - Backup database
  - Kirim ringkasan mingguan

## 🚀 Cara Menjalankan Worker

### **Opsi 1: Jalankan Semua Worker**
```bash
# Windows
run_worker.bat

# Linux/Mac
python run_all_workers.py
```

### **Opsi 2: Jalankan Worker Individual**
```bash
# Emotion Stream Worker
python workers/emotion_stream_worker.py

# Notification Worker
python workers/notification_worker.py

# Report Worker
python workers/report_worker.py

# Scheduler Worker
python workers/scheduler_worker.py
```

## 📡 API Endpoints untuk Worker

### **1. Kirim Notifikasi**
```http
POST /api/worker/send-notification
Content-Type: application/json
Authorization: Bearer <token>

{
    "type": "email",           // "email", "push", "both"
    "recipient": "parent@example.com",
    "subject": "Laporan Emosi Anak",
    "message": "Anak Anda menunjukkan emosi yang baik hari ini!",
    "data": {
        "student_id": "1",
        "emotion_summary": {...}
    }
}
```

### **2. Request Generate Laporan**
```http
POST /api/worker/request-report
Content-Type: application/json
Authorization: Bearer <token>

{
    "type": "emotion",         // "emotion", "daily_summary"
    "student_id": "1",
    "start_date": "2025-10-01",
    "end_date": "2025-10-14",
    "format": "pdf"            // "pdf", "excel"
}
```

### **3. Schedule Task**
```http
POST /api/worker/schedule-task
Content-Type: application/json
Authorization: Bearer <token>

{
    "task_type": "cleanup_old_data",
    "task_data": {
        "days_to_keep": 30
    },
    "delay_seconds": 0
}
```

### **4. Cek Status Job**
```http
GET /api/worker/job-status/<stream_name>/<message_id>
Authorization: Bearer <token>
```

## 💻 Contoh Penggunaan dalam Kode

### **Kirim Email ke Parent**
```python
from services.worker_service import send_email_to_parent

# Kirim email laporan emosi
message_id = send_email_to_parent(
    parent_email='parent@example.com',
    student_name='Andi Pratama',
    emotion_summary={
        'happy': 15,
        'sad': 3,
        'neutral': 8,
        'angry': 1
    }
)
print(f"Email queued: {message_id}")
```

### **Kirim Push Notification**
```python
from services.worker_service import send_push_notification_to_parent

# Kirim push notification
message_id = send_push_notification_to_parent(
    parent_id='parent123',
    title='Deteksi Emosi Baru',
    message='Anak Anda terdeteksi emosi happy!',
    data={'student_id': '1', 'emotion': 'happy'}
)
print(f"Push notification queued: {message_id}")
```

### **Generate Laporan**
```python
from services.worker_service import generate_student_emotion_report

# Generate laporan emosi siswa
report_id = generate_student_emotion_report(
    student_id='1',
    start_date='2025-10-01',
    end_date='2025-10-14',
    user_id='parent123'
)
print(f"Report queued: {report_id}")
```

### **Schedule Task**
```python
from services.worker_service import schedule_daily_cleanup

# Schedule cleanup harian
task_id = schedule_daily_cleanup()
print(f"Task scheduled: {task_id}")
```

## 🔧 Konfigurasi Worker

### **Environment Variables**
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration (untuk Notification Worker)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Worker Configuration
EMOTION_STREAM=emotion-events
NOTIFICATION_STREAM=notification-events
REPORT_STREAM=report-events
SCHEDULER_STREAM=scheduler-events
```

### **Redis Stream Names**
- `emotion-events`: Data emosi real-time
- `notification-events`: Job notifikasi
- `report-events`: Job generate laporan
- `scheduler-events`: Job terjadwal

## 📊 Monitoring Worker

### **Cek Status Worker**
```bash
# Cek apakah worker berjalan
python -c "
import redis
r = redis.Redis.from_url('redis://localhost:6379/0')
print('Redis Streams:')
for stream in ['emotion-events', 'notification-events', 'report-events', 'scheduler-events']:
    try:
        info = r.xinfo_stream(stream)
        print(f'{stream}: {info[\"length\"]} messages')
    except:
        print(f'{stream}: No messages')
"
```

### **Cek Pending Jobs**
```bash
# Cek pending jobs di setiap stream
python -c "
import redis
r = redis.Redis.from_url('redis://localhost:6379/0')
for stream in ['emotion-events', 'notification-events', 'report-events', 'scheduler-events']:
    try:
        pending = r.xpending_range(stream, 'emotion-workers', '-', '+', 10)
        print(f'{stream}: {len(pending)} pending jobs')
    except:
        print(f'{stream}: No pending jobs')
"
```

## 🚨 Troubleshooting

### **Worker Tidak Berjalan**
1. Pastikan Redis berjalan: `redis-cli ping`
2. Cek environment variables
3. Cek log error di console

### **Job Tidak Diproses**
1. Cek apakah worker berjalan
2. Cek Redis connection
3. Cek pending jobs di Redis

### **Email Tidak Terkirim**
1. Cek SMTP credentials
2. Cek network connection
3. Cek spam folder

### **Report Tidak Generate**
1. Cek file permissions
2. Cek disk space
3. Cek log error

## 📈 Performance Tips

1. **Jalankan worker di background** untuk production
2. **Monitor memory usage** worker
3. **Set appropriate timeouts** untuk Redis operations
4. **Use connection pooling** untuk database
5. **Implement retry logic** untuk failed jobs

## 🔒 Security Considerations

1. **Jangan hardcode credentials** di worker
2. **Gunakan environment variables** untuk sensitive data
3. **Implement rate limiting** untuk API endpoints
4. **Validate input data** sebelum processing
5. **Log semua activities** untuk audit

---

**📝 Catatan**: Worker system ini menggunakan Redis Streams untuk reliable message processing. Pastikan Redis berjalan dan terkonfigurasi dengan benar sebelum menjalankan worker.
