import os
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from .onnx_runtime_service import arcface_embed


class EmbeddingCache:
    """Caches ArcFace embeddings for gallery images under known_faces.

    Directory layout: known_faces/<student_code>/*.jpg|*.png
    """

    def __init__(self, known_faces_dir: str):
        self.known_faces_dir = known_faces_dir
        self.student_to_embeddings: Dict[str, List[np.ndarray]] = {}

    def build_cache(self) -> int:
        total = 0
        self.student_to_embeddings.clear()
        if not os.path.isdir(self.known_faces_dir):
            return 0
        for student_code in os.listdir(self.known_faces_dir):
            student_dir = os.path.join(self.known_faces_dir, student_code)
            if not os.path.isdir(student_dir):
                continue
            embs: List[np.ndarray] = []
            for fn in os.listdir(student_dir):
                if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                path = os.path.join(student_dir, fn)
                try:
                    img = cv2.imread(path)
                    if img is None:
                        continue
                    emb = arcface_embed(img)
                    if emb is not None:
                        embs.append(emb)
                        total += 1
                except Exception:
                    continue
            if embs:
                self.student_to_embeddings[student_code] = embs
        return total

    def best_match(self, query_emb: np.ndarray) -> Tuple[Optional[str], Optional[float]]:
        """Return (best_student_code, best_similarity[0..1]) or (None, None)."""
        best_id = None
        best_sim = -1.0
        for student_code, embs in self.student_to_embeddings.items():
            for emb in embs:
                sim = float(np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-6))
                if sim > best_sim:
                    best_sim = sim
                    best_id = student_code
        if best_id is None:
            return None, None
        return best_id, best_sim

