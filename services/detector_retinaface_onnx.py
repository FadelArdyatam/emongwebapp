import os
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import logging
logger = logging.getLogger("retinaface_loader_debug")

_retina_sess = None


def _lazy_session(model_path: str):
    global _retina_sess
    if _retina_sess is not None:
        return _retina_sess
    try:
        import onnxruntime as ort  # type: ignore
    except Exception as e:
        print(f"❌ ONNX Runtime tidak tersedia untuk RetinaFace: {e}")
        return None
    if not os.path.isfile(model_path):
        print(f"❌ RetinaFace model tidak ditemukan: {model_path}")
        return None
    
    providers = ["CPUExecutionProvider"]
    available_providers = getattr(ort, "get_available_providers", lambda: [])()
    gpu_available = "CUDAExecutionProvider" in available_providers
    
    if gpu_available:
        providers.insert(0, "CUDAExecutionProvider")
        print("🚀 RetinaFace ONNX: GPU (CUDA) tersedia dan akan digunakan")
    else:
        print("⚠️  RetinaFace ONNX: GPU tidak tersedia, menggunakan CPU")
    
    print(f"   Available providers: {available_providers}")
    print(f"   Using providers: {providers}")
    
    try:
        _retina_sess = ort.InferenceSession(model_path, providers=providers)
        actual_providers = _retina_sess.get_providers()
        print(f"✅ RetinaFace model loaded successfully")
        print(f"   Model: {os.path.basename(model_path)}")
        print(f"   Active providers: {actual_providers}")
    except Exception as e:
        print(f"❌ Failed to load RetinaFace model: {e}")
        _retina_sess = None
    return _retina_sess


def _preprocess(image_bgr: np.ndarray, size=(640, 640)):
    img = cv2.resize(image_bgr, size)
    img = img.astype(np.float32)
    img -= np.array([104, 117, 123], dtype=np.float32)
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    return img


def get_models_dir():
    # Cari root emongwebapp folder regardless current file location
    import os
    this_file = os.path.abspath(__file__)
    root_eidx = this_file.lower().rfind('emongwebapp')
    if root_eidx != -1:
        root_dir = this_file[:root_eidx+len('emongwebapp')]
        return os.path.join(root_dir, 'models', 'convertedmodels')
    # fallback
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models/convertedmodels'))


def extract_faces_with_retinaface_onnx(image_bgr: np.ndarray) -> Optional[List[Dict[str, Any]]]:
    """Return list of DeepFace-like detections using RetinaFace ONNX if model exists.
    Each item: { 'face': np.ndarray(RGB, 0..1), 'facial_area': {'x','y','w','h'} }
    """
    import os
    logger.warning('extract_faces_with_retinaface_onnx dipanggil!')
    logger.warning('Current working directory: %s', os.getcwd())
    try:
        logger.warning('os.listdir(./models/convertedmodels): %s', os.listdir(os.path.join(os.getcwd(), 'models', 'convertedmodels')))
    except Exception as e:
        logger.warning('Tidak bisa listdir ./models/convertedmodels: %s', e)
    models_dir = get_models_dir()
    mobilenet_path = os.path.join(models_dir, 'retinaface_mobilenet25.onnx')
    res50_path = os.path.join(models_dir, 'retinaface_resnet50.onnx')
    logger.warning("[DEBUG] retinaface mobilenet25 onnx: %s (EXISTS: %s)", mobilenet_path, os.path.isfile(mobilenet_path))
    logger.warning("[DEBUG] retinaface resnet50 onnx: %s (EXISTS: %s)", res50_path, os.path.isfile(res50_path))
    sess = _lazy_session(mobilenet_path)
    if sess is None:
        sess = _lazy_session(res50_path)
    if sess is None:
        logger.warning("[ERROR] RetinaFace ONNX model NOT FOUND at any checked path!")
        return None

    input_name = sess.get_inputs()[0].name
    h0, w0 = image_bgr.shape[:2]
    blob = _preprocess(image_bgr)
    try:
        outputs = sess.run(None, {input_name: blob})
    except Exception:
        return None

    # Output parsing depends on model export; here we try common layout
    # For simplicity, we fallback to None if unexpected
    if len(outputs) < 3:
        return None
    loc, conf, landms = outputs[:3]
    loc = np.squeeze(loc, axis=0)
    conf = np.squeeze(conf, axis=0)

    # Simple thresholding
    scores = conf[:, 1] if conf.ndim == 2 and conf.shape[1] >= 2 else conf.reshape(-1)
    mask = scores > 0.5
    if not np.any(mask):
        return []
    boxes = loc[mask]
    scores = scores[mask]

    detections: List[Dict[str, Any]] = []
    for b in boxes:
        # Assume b = [x1,y1,x2,y2] normalized to input size
        x1, y1, x2, y2 = b
        x1 = max(0, int(x1 / 640.0 * w0))
        y1 = max(0, int(y1 / 640.0 * h0))
        x2 = min(w0 - 1, int(x2 / 640.0 * w0))
        y2 = min(h0 - 1, int(y2 / 640.0 * h0))
        w = max(0, x2 - x1)
        h = max(0, y2 - y1)
        if w <= 0 or h <= 0:
            continue
        face = image_bgr[y1:y2, x1:x2]
        if face.size == 0:
            continue
        face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        detections.append({
            'face': face_rgb,
            'facial_area': {'x': x1, 'y': y1, 'w': w, 'h': h}
        })
    return detections

import os
import threading
from typing import List, Dict, Optional

import cv2
import numpy as np


_MODEL_LOCK = threading.Lock()
_NET = None


def _get_default_model_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    # Expect model at RealtimeEmotionDetection/models/retinaface.onnx
    return os.path.join(base_dir, 'models', 'retinaface.onnx')


def _lazy_load_model(model_path: Optional[str] = None) -> Optional[cv2.dnn_Net]:
    global _NET
    if _NET is not None:
        return _NET
    with _MODEL_LOCK:
        if _NET is not None:
            return _NET
        path = model_path or _get_default_model_path()
        if not os.path.isfile(path):
            return None
        try:
            net = cv2.dnn.readNetFromONNX(path)
            _NET = net
            return _NET
        except Exception:
            return None


def extract_faces_with_retinaface_onnx(
    frame_bgr: np.ndarray,
    conf_threshold: float = 0.5,
    input_size: int = 640,
    model_path: Optional[str] = None
) -> Optional[List[Dict]]:
    """Attempt to detect faces using RetinaFace ONNX via OpenCV DNN.

    Returns list of DeepFace-like dicts: [{ 'face': rgb_float01, 'facial_area': {x,y,w,h}, 'confidence': float }, ...]
    If model not available or failure occurs, returns None to signal caller to fallback to DeepFace.
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return []

    net = _lazy_load_model(model_path)
    if net is None:
        # Model not available -> let caller fallback
        return None

    try:
        h, w = frame_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame_bgr,
            scalefactor=1.0,
            size=(input_size, input_size),
            mean=(104, 117, 123),  # typical for RetinaFace preprocessing (BGR mean)
            swapRB=False,
            crop=False
        )
        net.setInput(blob)

        # NOTE: Different RetinaFace ONNX exports may have differing output names/shapes.
        # Here we try a generic forward and very conservative parsing. If parsing fails,
        # we return None so upstream can fallback to DeepFace's detector.
        try:
            outputs = net.forward(net.getUnconnectedOutLayersNames())
        except Exception:
            outputs = [net.forward()]

        # Minimal, defensive parsing: try to interpret any Nx[?, 5] boxes with [x1,y1,x2,y2,score]
        detections: List[Dict] = []
        for out in outputs:
            out_np = np.array(out)
            out_2d = out_np.reshape(-1, out_np.shape[-1]) if out_np.ndim > 2 else out_np
            if out_2d.shape[-1] < 5:
                continue
            for row in out_2d:
                x1, y1, x2, y2, score = row[:5]
                if score < conf_threshold:
                    continue
                # Rescale from model input space to original frame size if values are relative to input size
                # This is a heuristic; if the model outputs are already in absolute pixels, clamp will handle.
                if max(x1, y1, x2, y2) <= 1.5:  # likely normalized 0..1
                    x1 *= w
                    x2 *= w
                    y1 *= h
                    y2 *= h
                x1 = int(max(0, min(w - 1, x1)))
                y1 = int(max(0, min(h - 1, y1)))
                x2 = int(max(0, min(w - 1, x2)))
                y2 = int(max(0, min(h - 1, y2)))
                if x2 <= x1 or y2 <= y1:
                    continue
                roi = frame_bgr[y1:y2, x1:x2]
                if roi.size == 0:
                    continue
                # Convert to DeepFace-like face image: RGB float [0..1]
                face_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB).astype('float32') / 255.0
                detections.append({
                    'face': face_rgb,
                    'facial_area': {
                        'x': int(x1), 'y': int(y1), 'w': int(x2 - x1), 'h': int(y2 - y1)
                    },
                    'confidence': float(score)
                })

        return detections if detections else []
    except Exception:
        # Any error -> allow fallback
        return None

