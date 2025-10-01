import argparse
import os
import sys
from typing import Optional


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def export_arcface(output_dir: str, opset: int = 13) -> None:
    """Export ArcFace obtained via DeepFace.build_model('ArcFace').
    Supports PyTorch or Keras backends depending on DeepFace version.
    """
    from deepface import DeepFace

    print("[INFO] Loading ArcFace via DeepFace.build_model('ArcFace')...")
    model = DeepFace.build_model("ArcFace")

    # Try PyTorch first
    try:
        import torch
        import torch.nn as nn
        if isinstance(model, nn.Module):
            model.eval()
            dummy = torch.randn(1, 3, 112, 112)
            ensure_dir(output_dir)
            out_path = os.path.join(output_dir, 'arcface.onnx')
            print(f"[INFO] Exporting ArcFace (PyTorch) to ONNX -> {out_path}")
            torch.onnx.export(
                model,
                dummy,
                out_path,
                input_names=["input"],
                output_names=["emb"],
                opset_version=opset,
                dynamic_axes={"input": {0: "batch"}, "emb": {0: "batch"}},
            )
            print("[OK] ArcFace ONNX exported (PyTorch).")
            return
    except Exception:
        pass

    # Fallback: try Keras / TensorFlow
    try:
        import tensorflow as tf
        if isinstance(model, tf.keras.Model):
            ensure_dir(output_dir)
            out_path = os.path.join(output_dir, 'arcface.onnx')
            print(f"[INFO] Exporting ArcFace (Keras) to ONNX -> {out_path}")
            export_keras_model(model, out_path, opset)
            print("[OK] ArcFace ONNX exported (Keras).")
            return
    except Exception:
        pass

    # DeepFace v0.0.83 may load ArcFace via InsightFace ONNX (already ONNX).
    # Try to locate an ONNX file from common caches and copy it into output_dir.
    onnx_path = _find_existing_arcface_onnx()
    if onnx_path:
        ensure_dir(output_dir)
        dst = os.path.join(output_dir, 'arcface.onnx')
        import shutil
        shutil.copy2(onnx_path, dst)
        print(f"[OK] Found existing ArcFace ONNX and copied to {dst}")
        return

    # As a last resort, try to fetch via insightface
    try:
        from insightface.app import FaceAnalysis
        print("[INFO] Downloading ArcFace (InsightFace) ONNX via FaceAnalysis...")
        app = FaceAnalysis(name='buffalo_l')  # widely used pack
        app.prepare(ctx_id=-1)
        # Attempt to discover recognition model file
        candidate = _find_existing_arcface_onnx()
        if candidate:
            ensure_dir(output_dir)
            import shutil
            dst = os.path.join(output_dir, 'arcface.onnx')
            shutil.copy2(candidate, dst)
            print(f"[OK] Downloaded and copied ArcFace ONNX to {dst}")
            return
    except Exception as e:
        print("[WARN] insightface fetch failed or unavailable:", e)

    raise RuntimeError("Unsupported ArcFace model type for ONNX export, and no ONNX found in caches. Install insightface or provide an ArcFace ONNX.")


def _find_existing_arcface_onnx() -> Optional[str]:
    """Search common cache dirs for ArcFace/InsightFace ONNX files and return first hit."""
    import glob
    home = os.path.expanduser('~')
    candidates = []
    # Common InsightFace cache paths
    candidates += glob.glob(os.path.join(home, '.insightface', 'models', '**', '*.onnx'), recursive=True)
    # DeepFace weights cache often stores arcs also
    candidates += glob.glob(os.path.join(home, '.deepface', 'weights', '**', '*.onnx'), recursive=True)
    # Heuristic filter for recognition models
    preferred_keywords = ['arcface', 'glint', 'r50', 'r100', 'w600k', 'ms1mv3']
    ranked = []
    for p in candidates:
        name = os.path.basename(p).lower()
        score = sum(1 for k in preferred_keywords if k in name)
        ranked.append((score, p))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return ranked[0][1] if ranked else None


def export_keras_model(keras_model, out_path: str, opset: int = 13) -> None:
    try:
        import tf2onnx
        import tensorflow as tf
    except Exception as e:
        print("[ERROR] tf2onnx / tensorflow not available. Please install: pip install tf2onnx")
        raise

    print(f"[INFO] Converting Keras model to ONNX -> {out_path}")
    spec = (tf.TensorSpec(keras_model.inputs[0].shape, keras_model.inputs[0].dtype, name=keras_model.inputs[0].name),)
    model_proto, _ = tf2onnx.convert.from_keras(keras_model, input_signature=spec, opset=opset, output_path=out_path)
    print("[OK] Keras -> ONNX exported:", out_path)


def export_emotion(output_dir: str, opset: int = 13) -> None:
    try:
        from deepface.basemodels import Emotion
    except Exception as e:
        print("[ERROR] Cannot import DeepFace Emotion model:", e)
        raise

    print("[INFO] Loading Emotion model (Keras/TF)...")
    model = Emotion.loadModel()
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, 'emotion.onnx')
    export_keras_model(model, out_path, opset)


def export_age(output_dir: str, opset: int = 13) -> None:
    try:
        from deepface.basemodels import Age
    except Exception as e:
        print("[ERROR] Cannot import DeepFace Age model:", e)
        raise

    print("[INFO] Loading Age model (Keras/TF)...")
    model = Age.loadModel()
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, 'age.onnx')
    export_keras_model(model, out_path, opset)


def export_gender(output_dir: str, opset: int = 13) -> None:
    try:
        from deepface.basemodels import Gender
    except Exception as e:
        print("[ERROR] Cannot import DeepFace Gender model:", e)
        raise

    print("[INFO] Loading Gender model (Keras/TF)...")
    model = Gender.loadModel()
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, 'gender.onnx')
    export_keras_model(model, out_path, opset)


def export_race(output_dir: str, opset: int = 13) -> None:
    try:
        from deepface.basemodels import Race
    except Exception as e:
        print("[ERROR] Cannot import DeepFace Race model:", e)
        raise

    print("[INFO] Loading Race model (Keras/TF)...")
    model = Race.loadModel()
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, 'race.onnx')
    export_keras_model(model, out_path, opset)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description='Export DeepFace models to ONNX')
    parser.add_argument('--output-dir', default=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models'), help='Directory to save ONNX files')
    parser.add_argument('--opset', type=int, default=13, help='ONNX opset version')
    parser.add_argument('--arcface', action='store_true', help='Export ArcFace (recognition, PyTorch)')
    parser.add_argument('--emotion', action='store_true', help='Export Emotion (Keras/TF)')
    parser.add_argument('--age', action='store_true', help='Export Age (Keras/TF)')
    parser.add_argument('--gender', action='store_true', help='Export Gender (Keras/TF)')
    parser.add_argument('--race', action='store_true', help='Export Race (Keras/TF)')

    args = parser.parse_args(argv)

    # If no specific flags, export commonly used: arcface + emotion
    if not (args.arcface or args.emotion or args.age or args.gender or args.race):
        args.arcface = True
        args.emotion = True

    try:
        if args.arcface:
            export_arcface(args.output_dir, args.opset)
        if args.emotion:
            export_emotion(args.output_dir, args.opset)
        if args.age:
            export_age(args.output_dir, args.opset)
        if args.gender:
            export_gender(args.output_dir, args.opset)
        if args.race:
            export_race(args.output_dir, args.opset)
    except Exception as e:
        print("[FAILED] Export failed:", e)
        return 1

    print("[DONE] Export complete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

