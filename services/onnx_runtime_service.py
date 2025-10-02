import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

_onnx_runtime = None
_arcface_sess = None
_emotion_sess = None


def _lazy_import_onnxruntime():
    global _onnx_runtime
    if _onnx_runtime is None:
        try:
            import onnxruntime as ort  # type: ignore
        except Exception as e:
            raise RuntimeError(f"onnxruntime not available: {e}")
        _onnx_runtime = ort
    return _onnx_runtime


def init_onnx_models(models_dir: str, arcface_path: Optional[str] = None, emotion_path: Optional[str] = None) -> None:
    """Initialize ONNX runtime sessions if model files exist.

    models_dir: directory containing arcface.onnx and emotion.onnx
    """
    global _arcface_sess, _emotion_sess
    ort = _lazy_import_onnxruntime()

    arcface_path = arcface_path or os.path.join(models_dir, "arcface.onnx")
    emotion_path = emotion_path or os.path.join(models_dir, "emotion.onnx")

    providers = ["CPUExecutionProvider"]
    available_providers = []
    if hasattr(ort, "get_available_providers"):
        available_providers = ort.get_available_providers()
        
    # Check for GPU availability and log status
    gpu_available = "CUDAExecutionProvider" in available_providers
    if gpu_available:
        providers.insert(0, "CUDAExecutionProvider")
        print("🚀 ONNX Runtime: GPU (CUDA) tersedia dan akan digunakan")
        print(f"   Available providers: {available_providers}")
    else:
        print("⚠️  ONNX Runtime: GPU tidak tersedia, menggunakan CPU")
        print(f"   Available providers: {available_providers}")
    
    print(f"   Using providers: {providers}")

    # ArcFace
    if os.path.isfile(arcface_path) and _arcface_sess is None:
        try:
            _arcface_sess = ort.InferenceSession(arcface_path, providers=providers)
            actual_providers = _arcface_sess.get_providers()
            print(f"✅ ArcFace model loaded successfully")
            print(f"   Model: {os.path.basename(arcface_path)}")
            print(f"   Active providers: {actual_providers}")
        except Exception as e:
            print(f"❌ Failed to load ArcFace model: {e}")
            _arcface_sess = None

    # Emotion
    if os.path.isfile(emotion_path) and _emotion_sess is None:
        try:
            _emotion_sess = ort.InferenceSession(emotion_path, providers=providers)
            actual_providers = _emotion_sess.get_providers()
            print(f"✅ Emotion model loaded successfully")
            print(f"   Model: {os.path.basename(emotion_path)}")
            print(f"   Active providers: {actual_providers}")
        except Exception as e:
            print(f"❌ Failed to load Emotion model: {e}")
            _emotion_sess = None


def _get_input_shape(session) -> Tuple[int, int, int, int]:
    inp = session.get_inputs()[0]
    shape = [d if isinstance(d, int) else (1 if d in (None, "None", "batch", "N") else 1) for d in inp.shape]
    # Ensure 4D
    if len(shape) != 4:
        raise ValueError(f"Unexpected input rank: {shape}")
    return tuple(int(x) for x in shape)  # type: ignore


def _to_nchw(image_bgr: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    import cv2
    h, w = size
    img = cv2.resize(image_bgr, (w, h))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))  # HWC -> CHW
    return img


def _to_nhwc(image_bgr: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    import cv2
    h, w = size
    img = cv2.resize(image_bgr, (w, h))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    return img


def arcface_embed(face_bgr: np.ndarray) -> Optional[np.ndarray]:
    """Compute ArcFace embedding using ONNX model if available.
    Returns 1D numpy array or None on failure.
    """
    if _arcface_sess is None:
        return None
    try:
        sess = _arcface_sess
        n, c_or_h, h_or_w, maybe_w = _get_input_shape(sess)
        # Heuristic: if channels==3 at dim 1 -> NCHW; if 3 at last dim -> NHWC
        inputs = sess.get_inputs()[0].name
        if c_or_h == 3:
            inp = _to_nchw(face_bgr, (h_or_w, maybe_w))
            inp = (inp * 2.0) - 1.0  # scale to [-1,1] commonly used by ArcFace
            tensor = inp[None, ...]
        else:
            # NHWC
            _, h, w, c = _get_input_shape(sess)
            inp = _to_nhwc(face_bgr, (h, w))
            inp = (inp * 2.0) - 1.0
            tensor = inp[None, ...]
        outputs = sess.run(None, {inputs: tensor})
        vec = outputs[0]
        if vec.ndim == 2:
            vec = vec[0]
        vec = vec.astype(np.float32)
        # Normalize embedding
        norm = np.linalg.norm(vec) + 1e-6
        return vec / norm
    except Exception:
        return None


_DEFAULT_EMO_LABELS = [
    "angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"
]


def predict_emotion(face_bgr: np.ndarray) -> Optional[Dict[str, Any]]:
    """Predict emotion using ONNX model if available.
    Returns { 'emotion': str, 'scores': {label: prob}} or None on failure.
    """
    if _emotion_sess is None:
        return None
    try:
        sess = _emotion_sess
        n, c_or_h, h_or_w, maybe_w = _get_input_shape(sess)
        inputs = sess.get_inputs()[0].name
        if c_or_h == 3:
            inp = _to_nchw(face_bgr, (h_or_w, maybe_w))
        else:
            _, h, w, _ = _get_input_shape(sess)
            inp = _to_nhwc(face_bgr, (h, w))
        tensor = inp[None, ...].astype(np.float32)
        outputs = sess.run(None, {inputs: tensor})
        logits = outputs[0]
        if logits.ndim == 2:
            logits = logits[0]
        # Softmax
        exp = np.exp(logits - np.max(logits))
        probs = exp / (np.sum(exp) + 1e-9)
        labels = _DEFAULT_EMO_LABELS[: len(probs)]
        scores = {lbl: float(probs[i]) for i, lbl in enumerate(labels)}
        top_idx = int(np.argmax(probs))
        top_label = labels[top_idx]
        return {"emotion": top_label, "scores": scores}
    except Exception:
        return None

