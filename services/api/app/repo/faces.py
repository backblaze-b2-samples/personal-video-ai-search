"""Local face detect + embed adapter ($0 API cost).

Faces are detected and embedded entirely on the local machine with
``insightface`` (ONNX models, CPU via ``onnxruntime``). The first ingest with
face indexing downloads the model weights once; nothing leaves the host and no
provider key is required. The greedy cosine clustering below is a small, pure
helper that the service layer composes — it lives here next to the detector so
the embedding dimension and distance metric stay in one place.

Detection returns L2-normalized 512-d embeddings, so cosine distance is just
``1 - dot``.
"""

import logging

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

_MODEL = "buffalo_l"  # insightface model pack (detection + ArcFace embedding)
_app = None


def is_available() -> bool:
    """True when the local face stack can be imported. Unlike the AI provider
    adapters this needs no key — only the optional ML dependencies."""
    try:
        import insightface  # noqa: F401
        import onnxruntime  # noqa: F401
    except Exception:
        return False
    return True


def model_name() -> str:
    return _MODEL


def _detector():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis

        app = FaceAnalysis(name=_MODEL, providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))
        _app = app
    return _app


def embed_faces(jpeg_bytes: bytes) -> list[list[float]]:
    """Detect every face in a keyframe and return their (normalized) vectors.

    Returns an empty list when no face is found. Raises only on a genuine
    model failure — a frame with no faces is normal, not an error.
    """
    if not is_available():
        return []
    import cv2  # bundled transitively with insightface

    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return []
    faces = _detector().get(img)
    out: list[list[float]] = []
    for f in faces:
        vec = np.asarray(f.normed_embedding, dtype="float32")
        out.append(vec.tolist())
    return out


# --- pure clustering helpers (no SDK) ---------------------------------------


def cosine_distance(a: list[float], b: list[float]) -> float:
    va = np.asarray(a, dtype="float32")
    vb = np.asarray(b, dtype="float32")
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0.0:
        return 1.0
    return 1.0 - float(np.dot(va, vb) / denom)


def nearest_centroid(
    vector: list[float], centroids: list[list[float]]
) -> tuple[int, float]:
    """Return ``(index, distance)`` of the closest centroid, or ``(-1, inf)``
    when there are no centroids yet."""
    best_i, best_d = -1, float("inf")
    for i, c in enumerate(centroids):
        d = cosine_distance(vector, c)
        if d < best_d:
            best_i, best_d = i, d
    return best_i, best_d


def matches(vector: list[float], centroid: list[float]) -> bool:
    """Whether a face belongs to a cluster, per the configured threshold."""
    return cosine_distance(vector, centroid) <= settings.face_cluster_threshold


def update_centroid(
    centroid: list[float], member_count: int, vector: list[float]
) -> list[float]:
    """Running mean of an L2-normalized cluster centroid after adding a face."""
    c = np.asarray(centroid, dtype="float32") * member_count
    c = (c + np.asarray(vector, dtype="float32")) / (member_count + 1)
    norm = float(np.linalg.norm(c))
    if norm > 0:
        c = c / norm
    return c.tolist()
