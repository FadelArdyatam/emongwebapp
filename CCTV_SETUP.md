# CCTV (RTSP) Setup Guide — Emong DeepFace Web

Dokumen ini menjelaskan cara mengaktifkan dan menguji input CCTV (RTSP) pada proyek EmongDeepFaceWeb, baik melalui konfigurasi environment, endpoint runtime, maupun melalui UI dashboard guru. Disertai langkah verifikasi dan troubleshooting.

---

## 1) Prasyarat

- CCTV/IP Camera yang mendukung RTSP, dan Anda memiliki URL RTSP (berisi user, password, IP/Host, port, dan path).
  - Contoh format umum RTSP:
    - Hikvision: `rtsp://user:pass@IP:554/Streaming/Channels/101`
    - Dahua: `rtsp://user:pass@IP:554/cam/realmonitor?channel=1&subtype=0`
    - Generic ONVIF: `rtsp://user:pass@IP:554/trackID=1` atau `rtsp://user:pass@IP:554/stream1`
- Server memiliki konektivitas jaringan ke kamera (cek ping, port 554 atau port RTSP kamera).
- Dependency multimedia untuk OpenCV/FFmpeg di Ubuntu (opsional tapi direkomendasikan):
  - `sudo apt-get update && sudo apt-get install -y ffmpeg gstreamer1.0-tools libsm6 libxext6`

---

## 2) Cara Mengaktifkan RTSP (3 Opsi)

Anda bisa memilih salah satu cara berikut untuk mengaktifkan input RTSP.

### Opsi A — Environment Variable (pada saat start)

Set variabel environment sebelum menjalankan aplikasi:

```bash
# Contoh (Ubuntu)
export CAM_SOURCE=rtsp
export RTSP_URL="rtsp://user:pass@IP:554/Streaming/Channels/101"

# Jalankan server Flask (sesuaikan per cara Anda menjalankan app)
python app.py
```

Aplikasi akan membaca:
- `CAM_SOURCE` → `webcam` | `rtsp`
- `RTSP_URL` → string RTSP Anda

Lokasi terkait di kode: `app.py`
- `CURRENT_CAM_SOURCE`, `CURRENT_RTSP_URL`
- `_open_rtsp_stream()` → pembuka RTSP
- `_open_video_source()` → memilih sumber video berdasarkan konfigurasi runtime

### Opsi B — Runtime API (tanpa restart)

Gunakan endpoint untuk mengubah sumber kamera saat aplikasi berjalan:

```bash
# Set ke RTSP
curl -X POST http://HOST:PORT/camera/source \
  -H "Content-Type: application/json" \
  -d '{"source":"rtsp", "rtspUrl":"rtsp://user:pass@IP:554/Streaming/Channels/101"}'

# Set kembali ke webcam
curl -X POST http://HOST:PORT/camera/source \
  -H "Content-Type: application/json" \
  -d '{"source":"webcam"}'
```

Jika sukses, response: `{ "message": "Camera source updated", "cameraSource": "rtsp" }`.

### Opsi C — Melalui UI Dashboard Guru

Pada halaman `Dashboard Guru` → tab `Deteksi Emosi`:
- Pilih dropdown Kamera: `RTSP (CCTV)`
- Isi `RTSP URL`: `rtsp://user:pass@IP:554/...`
- Klik tombol `Terapkan`
- Anda juga bisa mengubah detector di dropdown (OpenCV/RetinaFace/MTCNN). Di codebase saat ini default runtime: `MTCNN`.

Komponen terkait di UI (file `templates/dashboard_guru.html`):
- `#dgCamSource` (webcam/rtsp)
- `#dgRtspUrl` (input RTSP)
- `applyDGCAMERA()` (menerapkan perubahan)

---

## 3) Verifikasi Koneksi Kamera

### A. Dari Aplikasi

Gunakan endpoint health:
```bash
curl http://HOST:PORT/camera/health | jq
```
Respons OK akan mengandung informasi kamera (contoh: `{ "camera": "ok", ... }`).

### B. Uji RTSP Secara Independen

- VLC: Media → Open Network Stream → masukkan URL RTSP.
- FFplay (FFmpeg):
```bash
ffplay -rtsp_transport tcp "rtsp://user:pass@IP:554/Streaming/Channels/101"
```
Jika gagal di VLC/FFplay, periksa kredensial, IP, port, dan firewall.

---

## 4) Pengaturan Detector Backend (opsional)

Aplikasi menyediakan endpoint untuk melihat/mengubah detector backend.

- GET backend aktif:
```bash
curl http://HOST:PORT/detector/backend | jq
```
- POST ganti backend:
```bash
curl -X POST http://HOST:PORT/detector/backend \
  -H "Content-Type: application/json" \
  -d '{"backend":"mtcnn"}'
```
Nilai yang didukung (mengacu pada integrasi DeepFace/OpenCV Anda): `opencv`, `retinaface`, `mtcnn`.

Catatan: Saat ini di `app.py` diset default runtime: `CURRENT_DETECTOR_BACKEND = 'mtcnn'`.

---

## 5) Alur Kerja Internal (Ringkas)

- `generate_frames()` memanggil `_open_video_source()` → jika `CURRENT_CAM_SOURCE == 'rtsp'` akan menggunakan `_open_rtsp_stream(CURRENT_RTSP_URL)`
- Frame dianalisis oleh DeepFace (`actions=['emotion', 'age', 'gender', 'race']` saat ini)
- Event emosi akan di-broadcast via websocket ke UI

---

## 6) Keamanan & Jaringan

- Disarankan menjalankan aplikasi di HTTPS agar fitur kamera (jika dari browser) bekerja baik dan menghindari block oleh browser.
- Untuk RTSP, stream umumnya plaintext, pastikan jaringan internal aman.
- Jika kamera berada di jaringan berbeda, pastikan routing dan firewall (port RTSP, default 554) terbuka.

---

## 7) Troubleshooting

1) RTSP tidak bisa dibuka di app, tetapi bisa di VLC/FFplay
- Pastikan environment atau runtime API sudah benar: `CAM_SOURCE=rtsp`, `RTSP_URL` valid.
- Periksa log server: cari pesan `RTSP error:` dari `_open_rtsp_stream`.
- Coba tambahkan parameter transport TCP: beberapa kamera lebih stabil di TCP (sesuaikan implementasi OpenCV/FFmpeg Anda).

2) Latensi tinggi / frame patah-patah
- Gunakan koneksi kabel untuk kamera dan server.
- Kurangi resolusi/bitrate stream kamera.
- Pastikan server tidak kekurangan CPU (DeepFace + deteksi real-time cukup berat).

3) 401/403 saat memanggil API kamera
- Endpoint `/camera/source` tidak memerlukan JWT, tapi endpoint lain mungkin memerlukan header Authorization. Periksa dokumentasi endpoint terkait.

4) Browser menolak kamera (bukan RTSP) – getUserMedia undefined
- Akses harus HTTPS atau localhost.
- Karena ini mode CCTV (RTSP), kamera diambil dari server (bukan getUserMedia), jadi nonaktifkan pemanggilan webcam di UI atau pastikan Anda set ke RTSP.

---

## 8) Contoh Alur Setup Singkat

```bash
# 1. Pastikan RTSP bisa diputar di VLC/FFplay terlebih dahulu
ffplay -rtsp_transport tcp "rtsp://user:pass@IP:554/Streaming/Channels/101"

# 2. Jalankan app dengan sumber RTSP
export CAM_SOURCE=rtsp
export RTSP_URL="rtsp://user:pass@IP:554/Streaming/Channels/101"
python app.py

# 3. (Opsional) Ubah detector
curl -X POST http://HOST:PORT/detector/backend \
  -H "Content-Type: application/json" \
  -d '{"backend":"mtcnn"}'

# 4. Verifikasi koneksi kamera
curl http://HOST:PORT/camera/health | jq

# 5. Buka Dashboard Guru → Deteksi Emosi
#    Pastikan dropdown Kamera = RTSP dan RTSP URL sesuai, lalu klik Terapkan
```

---

## 9) Catatan Integrasi di Kode

- Variabel runtime:
  - `CURRENT_CAM_SOURCE`, `CURRENT_RTSP_URL` (app.py)
- Endpoint runtime:
  - POST `/camera/source` → ganti sumber kamera (webcam/rtsp)
  - GET `/camera/health` → cek status kamera
  - GET/POST `/detector/backend` → cek/ganti backend deteksi
- UI helper di `templates/dashboard_guru.html`:
  - `#dgCamSource` (webcam/rtsp), `#dgRtspUrl`, tombol `applyDGCAMERA()`

Jika Anda butuh, saya bisa bantu membuat script helper (bash/PowerShell) untuk mengganti sumber kamera dan menguji koneksi secara otomatis.