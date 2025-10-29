import time
import os
import sys
import numpy as np
import psutil
import matplotlib.pyplot as plt
from fpdf import FPDF
from collections import defaultdict
import traceback
try:
    import redis
    REDIS_ON = True
except ImportError:
    REDIS_ON = False

ITER = 15
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/convertedmodels/retinaface_resnet50.onnx'))
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

print("==========[DEBUG ENV]==========")
try:
    import onnxruntime as ort
    print("ONNXRuntime version:", ort.__version__)
    print("Tersedia providers:", ort.get_available_providers())
    print("ONNX device:", ort.get_device())
except Exception as e:
    print("[ONNXRUNTIME ERROR]", e)
try:
    import os
    print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES"))
    print("PATH:", os.environ.get("PATH"))
    print("CUDA_PATH:", os.environ.get("CUDA_PATH"))
    print("NVIDIA SMI Output:")
    import subprocess
    out = subprocess.check_output(["nvidia-smi"], encoding="utf8", stderr=subprocess.STDOUT)
    print(out)
except Exception as e:
    print("[NVIDIA-SMI/CUDA ERROR]", e)
print("===============================\n")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services import detector_retinaface_onnx as ret_onnx

def run_benchmark(provider, iter=ITER):
    try:
        import onnxruntime as ort
    except ImportError:
        print('ONNXRuntime belum tersedia.'); return None
    if provider not in ['CPUExecutionProvider','CUDAExecutionProvider']:
        raise ValueError('Provider harus CPUExecutionProvider atau CUDAExecutionProvider')
    if not os.path.exists(MODEL_PATH):
        print(f'Model tidak ditemukan di: {MODEL_PATH}'); return None
    try:
        print(f"[DEBUG] Membuat session onnxruntime dengan provider: {provider}")
        sess = ort.InferenceSession(MODEL_PATH, providers=[provider])
        print(f"[DEBUG] get_providers: {sess.get_providers()}")
    except Exception as e:
        print(f'Gagal load dengan {provider}: {e}')
        print('> Full traceback:')
        traceback.print_exc()
        return None
    input_name = sess.get_inputs()[0].name
    dummy_img = np.random.randint(0,255, (640,640,3), dtype=np.uint8)
    all_time = []
    all_cpu = []
    all_mem = []
    for i in range(iter):
        p = psutil.Process(os.getpid())
        cpu1 = p.cpu_percent(interval=None)
        mem1 = p.memory_info().rss / 1024 / 1024
        blob = ret_onnx._preprocess(dummy_img)
        start = time.time()
        try:
            _ = sess.run(None, {input_name: blob})
        except Exception as e:
            print(f'[DEBUG] Gagal run inference {provider}: {e}')
            traceback.print_exc()
            return None
        t = time.time()-start
        cpu2 = p.cpu_percent(interval=None)
        mem2 = p.memory_info().rss / 1024 / 1024
        all_cpu.append((cpu1+cpu2)/2)
        all_mem.append((mem1+mem2)/2)
        all_time.append(t)
    return {
        'provider': provider,
        'inference_times': all_time,
        'cpu_usages': all_cpu,
        'mem_usages': all_mem,
        'fps': [1/x if x>0 else 0 for x in all_time],
        'mean_time': np.mean(all_time),
        'mean_cpu': np.mean(all_cpu),
        'mean_mem': np.mean(all_mem),
        'mean_fps': np.mean([1/x if x>0 else 0 for x in all_time])
    }

def bar_single(val, label, ylabel, filename, provider):
    plt.figure(figsize=(3,4))
    plt.bar([provider], [val], color=['#1f8ef1' if provider=='CPU' else '#00c48c'])
    plt.title(f'{label} ({provider})')
    plt.ylabel(ylabel)
    plt.text(0, val+(0.01*val), f'{val:.3f}', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def line_iter_single(values, label, ylabel, filename, provider):
    plt.figure(figsize=(6,4))
    plt.plot(values, '-o', label=provider, color='#1f8ef1' if provider=='CPU' else '#00c48c')
    plt.title(f'{label} per Iterasi ({provider})')
    plt.xlabel('Iterasi')
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def bar_compare(val_cpu, val_gpu, label, ylabel, filename):
    plt.figure(figsize=(6,4))
    x = ['CPU', 'GPU']
    vals = [val_cpu, val_gpu]
    color = ['#1f8ef1','#00c48c']
    plt.bar(x, vals, color=color)
    plt.title(f'Perbandingan {label}')
    plt.ylabel(ylabel)
    for i,v in enumerate(vals):
        plt.text(i, v+(0.01*max(vals)), f'{v:.3f}', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def line_iter(cpu, gpu, label, ylabel, filename):
    plt.figure(figsize=(6,4))
    plt.plot(cpu, '-ob', label='CPU')
    plt.plot(gpu, '-og', label='GPU')
    plt.title(f'Trend {label} per Iterasi')
    plt.xlabel('Iterasi')
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# BENCHMARK RUN
print('Benchmarking CPU...')
data_cpu = run_benchmark('CPUExecutionProvider')
data_gpu = None
try:
    import onnxruntime as ort
    if 'CUDAExecutionProvider' in ort.get_available_providers():
        print('Benchmarking GPU...')
        data_gpu = run_benchmark('CUDAExecutionProvider')
    else:
        print('CUDAExecutionProvider tidak tersedia.')
except:
    print('ONNX Runtime dengan CUDA tidak ditemukan')

grafik_path = []
pdf_note = ''
if data_cpu and data_gpu:
    bar_compare(data_cpu['mean_time'], data_gpu['mean_time'], 'Waktu Inferensi Rata-Rata', 'Detik', 'c_vs_g_inference_time.png')
    bar_compare(data_cpu['mean_cpu'], data_gpu['mean_cpu'], 'CPU Usage Rata-Rata', '% CPU', 'c_vs_g_cpu_usage.png')
    bar_compare(data_cpu['mean_mem'], data_gpu['mean_mem'], 'RAM Usage Rata-Rata', 'MB', 'c_vs_g_mem_usage.png')
    bar_compare(data_cpu['mean_fps'], data_gpu['mean_fps'], 'Throughput FPS', 'Frame/detik', 'c_vs_g_fps.png')
    line_iter(data_cpu['inference_times'], data_gpu['inference_times'], 'Waktu Inferensi', 'Detik', 'inftime_line.png')
    line_iter(data_cpu['cpu_usages'], data_gpu['cpu_usages'], 'CPU Usage', '% CPU', 'cpuusage_line.png')
    line_iter(data_cpu['mem_usages'], data_gpu['mem_usages'], 'RAM Usage', 'MB', 'memusage_line.png')
    grafik_path = [
        ('Waktu Inferensi: CPU vs GPU','c_vs_g_inference_time.png'),
        ('CPU Usage: CPU vs GPU','c_vs_g_cpu_usage.png'),
        ('RAM Usage: CPU vs GPU','c_vs_g_mem_usage.png'),
        ('Throughput FPS: CPU vs GPU','c_vs_g_fps.png'),
        ('Per Iterasi Waktu Inferensi', 'inftime_line.png'),
        ('Per Iterasi CPU Usage', 'cpuusage_line.png'),
        ('Per Iterasi RAM Usage', 'memusage_line.png'),
    ]
    pdf_note = 'CPU dan GPU keduanya tersedia (side-by-side benchmark)'
elif data_cpu and not data_gpu:
    # Hanya CPU
    bar_single(data_cpu['mean_time'], 'Waktu Inferensi Rata-rata', 'Detik', 'cpu_infer_time.png','CPU')
    bar_single(data_cpu['mean_cpu'], 'CPU Usage Rata-rata', '%CPU', 'cpu_cpu_usage.png','CPU')
    bar_single(data_cpu['mean_mem'], 'RAM Usage Rata-rata', 'MB', 'cpu_mem_usage.png','CPU')
    bar_single(data_cpu['mean_fps'], 'Throughput FPS', 'Frame/detik', 'cpu_fps.png','CPU')
    line_iter_single(data_cpu['inference_times'],'Waktu Inferensi','Detik','cpu_infer_time_line.png','CPU')
    line_iter_single(data_cpu['cpu_usages'],'CPU Usage','%CPU','cpu_usage_line.png','CPU')
    line_iter_single(data_cpu['mem_usages'],'RAM Usage','MB','cpu_mem_line.png','CPU')
    grafik_path = [
        ('Waktu Inferensi (CPU)','cpu_infer_time.png'),
        ('CPU Usage (CPU)','cpu_cpu_usage.png'),
        ('RAM Usage (CPU)','cpu_mem_usage.png'),
        ('Throughput FPS (CPU)','cpu_fps.png'),
        ('Per Iterasi Waktu Inferensi','cpu_infer_time_line.png'),
        ('Per Iterasi CPU Usage','cpu_usage_line.png'),
        ('Per Iterasi RAM Usage','cpu_mem_line.png'),
    ]
    pdf_note = 'Hanya CPU yang tersedia (benchmark single-provider)'
elif (not data_cpu) and data_gpu:
    # Hanya GPU
    bar_single(data_gpu['mean_time'], 'Waktu Inferensi Rata-rata', 'Detik', 'gpu_infer_time.png','GPU')
    bar_single(data_gpu['mean_cpu'], 'CPU Usage Rata-rata', '%CPU', 'gpu_cpu_usage.png','GPU')
    bar_single(data_gpu['mean_mem'], 'RAM Usage Rata-rata', 'MB', 'gpu_mem_usage.png','GPU')
    bar_single(data_gpu['mean_fps'], 'Throughput FPS', 'Frame/detik', 'gpu_fps.png','GPU')
    line_iter_single(data_gpu['inference_times'],'Waktu Inferensi','Detik','gpu_infer_time_line.png','GPU')
    line_iter_single(data_gpu['cpu_usages'],'CPU Usage','%CPU','gpu_usage_line.png','GPU')
    line_iter_single(data_gpu['mem_usages'],'RAM Usage','MB','gpu_mem_line.png','GPU')
    grafik_path = [
        ('Waktu Inferensi (GPU)','gpu_infer_time.png'),
        ('CPU Usage (GPU)','gpu_cpu_usage.png'),
        ('RAM Usage (GPU)','gpu_mem_usage.png'),
        ('Throughput FPS (GPU)','gpu_fps.png'),
        ('Per Iterasi Waktu Inferensi','gpu_infer_time_line.png'),
        ('Per Iterasi CPU Usage','gpu_usage_line.png'),
        ('Per Iterasi RAM Usage','gpu_mem_line.png'),
    ]
    pdf_note = 'Hanya GPU yang tersedia (benchmark single-provider)'
else:
    pdf_note = 'Tidak ada provider valid yang tersedia/model load gagal.'

# --- PDF ---
pdf = FPDF()
pdf.add_page()
pdf.set_font('Arial', 'B', 14)
pdf.cell(0,12, 'Benchmark CPU vs GPU EmongDeepFace', ln=1, align='C')
pdf.ln(4)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0,8, f"Hasil benchmark aktual EmongDeepFaceWeb.\n---\nCatatan: {pdf_note}\n" )
pdf.ln(2)
# Ringkasan metrik
def val(x):
    return f"{x:.4f}" if isinstance(x,(float,np.floating)) else str(x)

if data_cpu:
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0,9,'METRIK CPU:',ln=1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0,7, f"Rata-rata waktu inferensi (CPU): {val(data_cpu['mean_time'])} detik\nThroughput FPS: {val(data_cpu['mean_fps'])}\nCPU Usage avg: {val(data_cpu['mean_cpu'])}\nRAM Usage avg: {val(data_cpu['mean_mem'])}")
    pdf.ln(2)
if data_gpu:
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0,9,'METRIK GPU:',ln=1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0,7, f"Rata-rata waktu inferensi (GPU): {val(data_gpu['mean_time'])} detik\nThroughput FPS: {val(data_gpu['mean_fps'])}\nCPU Usage avg: {val(data_gpu['mean_cpu'])}\nRAM Usage avg: {val(data_gpu['mean_mem'])}")
    pdf.ln(2)
if grafik_path:
    for judul, path in grafik_path:
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0,9, judul, ln=1)
        try:
            pdf.image(path, w=175)
        except:
            pdf.cell(0,7,"(Gagal load gambar)",ln=1)
        pdf.ln(2)
pdf.output('laporan_perbandingan_cpu_vs_gpu.pdf')
print('✅ PDF: laporan_perbandingan_cpu_vs_gpu.pdf')
