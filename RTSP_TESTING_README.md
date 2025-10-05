# RTSP Testing & CCTV Capture - EmongDeepFace

## Deskripsi
Halaman RTSP Testing memungkinkan admin dan guru untuk menguji koneksi RTSP dari CCTV dan melakukan capture image untuk emotion detection. Fitur ini sangat berguna untuk testing sistem dengan feed CCTV langsung.

## Fitur Utama

### 1. Koneksi RTSP
- **Input URL RTSP**: Masukkan URL RTSP dari CCTV
- **Preset URLs**: URL preset untuk berbagai jenis CCTV
- **Validasi URL**: Validasi format URL RTSP
- **Status Koneksi**: Indikator real-time status koneksi

### 2. Capture Image
- **Manual Capture**: Capture image secara manual
- **Auto Capture**: Capture otomatis dengan interval yang dapat dikonfigurasi
- **Batch Capture**: Capture multiple images dengan jumlah yang ditentukan
- **Image Storage**: Penyimpanan image di Redis dengan expiry 24 jam

### 3. Emotion Detection
- **Single Person**: Deteksi emosi untuk satu orang
- **Multi-person**: Deteksi emosi untuk multiple orang
- **Real-time Analysis**: Analisis emosi real-time
- **Confidence Score**: Skor kepercayaan untuk setiap deteksi

### 4. Image Management
- **Image Gallery**: Galeri image yang telah di-capture
- **Download**: Download individual atau batch
- **Delete**: Hapus image individual atau semua
- **Metadata**: Informasi timestamp, emotion, dan ID

## Cara Penggunaan

### 1. Akses Halaman
```
URL: http://localhost:5000/rtsp-testing
```

### 2. Login
- Pastikan sudah login sebagai admin atau guru
- Token authentication diperlukan untuk semua operasi

### 3. Koneksi RTSP
1. Masukkan URL RTSP di field "RTSP URL"
2. Klik "Connect RTSP" untuk memulai koneksi
3. Tunggu hingga status berubah menjadi "Terhubung"
4. Video stream akan muncul di area video

### 4. Capture Image
1. Pastikan RTSP sudah terhubung
2. Pilih opsi emotion detection (single/multi-person)
3. Klik "Capture Sekarang" untuk capture manual
4. Atau aktifkan "Auto Capture" untuk capture otomatis

### 5. Kelola Image
- Lihat image di galeri "Captured Images"
- Download image individual atau semua
- Hapus image yang tidak diperlukan
- Lihat metadata emotion detection

## API Endpoints

### RTSP Connection
```http
POST /api/rtsp/connect
Content-Type: application/json
Authorization: Bearer <token>

{
    "rtsp_url": "rtsp://username:password@ip:port/path"
}
```

### RTSP Disconnect
```http
POST /api/rtsp/disconnect
Authorization: Bearer <token>
```

### RTSP Status
```http
GET /api/rtsp/status
Authorization: Bearer <token>
```

### Capture Image
```http
POST /api/rtsp/capture
Content-Type: application/json
Authorization: Bearer <token>

{
    "enable_emotion_detection": true,
    "enable_multi_person": false
}
```

### Get Captured Images
```http
GET /api/rtsp/captured-images?page=1&per_page=20
Authorization: Bearer <token>
```

### Get Specific Image
```http
GET /api/rtsp/captured-images/<capture_id>
Authorization: Bearer <token>
```

### Delete Image
```http
DELETE /api/rtsp/captured-images/<capture_id>
Authorization: Bearer <token>
```

## Format URL RTSP

### Format Umum
```
rtsp://username:password@ip_address:port/path
```

### Contoh URL
```
rtsp://admin:admin123@192.168.1.100:554/stream1
rtsp://admin:admin123@192.168.1.101:554/live
rtsp://admin:admin123@192.168.1.102:554/ch1
rtsp://admin:admin123@192.168.1.103:554/main
```

## Response Format

### Emotion Detection Response
```json
{
    "type": "single_person",
    "emotion": "happy",
    "confidence": 0.85,
    "all_emotions": {
        "happy": 0.85,
        "sad": 0.05,
        "angry": 0.03,
        "surprised": 0.04,
        "neutral": 0.02,
        "fearful": 0.01,
        "disgusted": 0.00
    }
}
```

### Multi-person Response
```json
{
    "type": "multi_person",
    "faces_detected": 2,
    "emotions": [
        {
            "face_id": 0,
            "bbox": [100, 150, 200, 250],
            "emotion": "happy",
            "confidence": 0.85
        },
        {
            "face_id": 1,
            "bbox": [300, 200, 180, 220],
            "emotion": "neutral",
            "confidence": 0.72
        }
    ]
}
```

## Konfigurasi

### Redis Storage
- **Connection Info**: `rtsp_connection` (expiry: 1 hour)
- **Captured Images**: `captured_image:<id>` (expiry: 24 hours)
- **Image List**: `captured_images_list` (max: 100 images)

### Auto Capture Settings
- **Interval**: 1-60 detik
- **Count**: 1-100 images
- **Emotion Detection**: Enable/disable
- **Multi-person**: Enable/disable

## Troubleshooting

### Koneksi Gagal
1. Periksa format URL RTSP
2. Pastikan CCTV dapat diakses dari server
3. Verifikasi username/password
4. Periksa firewall dan network

### Capture Gagal
1. Pastikan RTSP sudah terhubung
2. Periksa koneksi Redis
3. Verifikasi token authentication
4. Periksa log system

### Emotion Detection Error
1. Pastikan DeepFace model sudah loaded
2. Periksa OpenCV installation
3. Verifikasi image format
4. Periksa memory usage

## Security

### Authentication
- Semua endpoint memerlukan JWT token
- Role-based access (admin, teacher)
- Token expiry handling

### Data Protection
- Image data disimpan di Redis dengan expiry
- Sensitive data tidak disimpan permanen
- Log sanitization untuk security

## Performance

### Optimization
- Redis caching untuk performance
- Image compression (JPEG 85% quality)
- Batch operations untuk multiple images
- Lazy loading untuk image data

### Monitoring
- Real-time connection status
- System logs untuk debugging
- Performance metrics
- Error tracking

## Dependencies

### Backend
- Flask
- Redis
- OpenCV
- DeepFace
- PIL (Pillow)

### Frontend
- Bootstrap 5
- Font Awesome
- Chart.js
- JavaScript ES6+

## Future Enhancements

### Planned Features
- Real-time video streaming
- WebRTC integration
- Advanced image filters
- Batch emotion analysis
- Export to various formats
- Integration with main dashboard
- Real-time notifications
- Advanced analytics

### Technical Improvements
- WebSocket for real-time updates
- Image compression optimization
- Caching strategies
- Error recovery mechanisms
- Performance monitoring
- Security enhancements

## Support

Untuk bantuan atau pertanyaan:
1. Periksa log system
2. Gunakan browser developer tools
3. Periksa network connectivity
4. Verifikasi authentication
5. Contact system administrator

---

**Note**: Fitur ini dalam tahap development dan mungkin memerlukan konfigurasi tambahan untuk production environment.