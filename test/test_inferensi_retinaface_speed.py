import os
import sys
import time
import numpy as np
import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services import detector_retinaface_onnx as retina_onnx

def run_inference(model_path, provider, repeat=10):
    try:
        import onnxruntime as ort
    except ImportError:
        print("ONNX Runtime belum terinstal, silakan install dulu.")
        return
    sess = ort.InferenceSession(model_path, providers=[provider])
    input_name = sess.get_inputs()[0].name
    # Gambar dummy 640x640
    img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    blob = retina_onnx._preprocess(img)
    # Warmup 1x
    try:
        sess.run(None, {input_name: blob})
    except Exception as e:
        print(f"⚠️  Gagal inferensi pada provider {provider}: {e}")
        return None
    # Benchmark
    elapsed = []
    for _ in range(repeat):
        start = time.time()
        sess.run(None, {input_name: blob})
        end = time.time()
        elapsed.append(end-start)
    return sum(elapsed)/len(elapsed)

def main():
    # Pilih model mana saja yang ada
    models_dir = retina_onnx.get_models_dir()
    candidates = ['retinaface_mobilenet25.onnx', 'retinaface_resnet50.onnx']
    available = [os.path.join(models_dir, f) for f in candidates if os.path.isfile(os.path.join(models_dir, f))]
    if not available:
        print(f"Model RetinaFace ONNX tidak ditemukan di {models_dir}")
        return
    model_path = available[0]
    print(f"Benchmark dengan model: {os.path.basename(model_path)}\n")

    try:
        import onnxruntime as ort
        all_providers = ort.get_available_providers()
    except ImportError:
        print("ONNX Runtime belum terinstal.")
        return
    providers = [p for p in ['CPUExecutionProvider', 'CUDAExecutionProvider'] if p in all_providers]

    results = {}
    for provider in providers:
        print(f"\n🔬 Benchmark inferensi dengan provider: {provider}")
        avg = run_inference(model_path, provider)
        if avg:
            print(f"⏱️  Rata-rata waktu inferensi ({provider}): {avg:.4f} detik")
            results[provider] = avg
        else:
            print(f"❌ Inferensi gagal dengan {provider}")

    if 'CPUExecutionProvider' in results and 'CUDAExecutionProvider' in results:
        print("\n=== PERBANDINGAN WAKTU (lebih kecil lebih cepat) ===")
        print(f"CPU : {results['CPUExecutionProvider']:.4f} detik")
        print(f"GPU : {results['CUDAExecutionProvider']:.4f} detik")
        selisih = results['CPUExecutionProvider'] - results['CUDAExecutionProvider']
        print(f"➡️  Selisih (CPU - GPU): {selisih:.4f} detik")

if __name__ == "__main__":
    main()
