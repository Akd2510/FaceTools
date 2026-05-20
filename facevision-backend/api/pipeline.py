"""
FaceVision Processing Pipeline
================================
Stage 1 : BlazeFace (MediaPipe) - face detection + 468 landmarks
Stage 2 : Face alignment           - affine warp to canonical pose
Stage 3 : InsightFace ArcFace      - 512-dim identity embedding
Stage 4 : DBSCAN clustering        - group faces by identity
"""
import io
import json
import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy model loaders
# ---------------------------------------------------------------------------

_mediapipe_detector = None
_arcface_app = None


def _get_mediapipe():
    """Lazily initialise MediaPipe FaceMesh (includes BlazeFace detector)."""
    global _mediapipe_detector
    if _mediapipe_detector is None:
        try:
            import mediapipe as mp
            _mediapipe_detector = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=20,
                refine_landmarks=True,
                min_detection_confidence=0.5,
            )
            logger.info("MediaPipe FaceMesh initialised.")
        except Exception as exc:
            logger.error("Failed to init MediaPipe: %s", exc)
            raise
    return _mediapipe_detector


def _get_arcface():
    """Lazily initialise InsightFace ArcFace embedding model."""
    global _arcface_app
    if _arcface_app is None:
        try:
            from insightface.app import FaceAnalysis
            _arcface_app = FaceAnalysis(
                name='buffalo_sc',
                providers=['CPUExecutionProvider'],
            )
            _arcface_app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace ArcFace initialised.")
        except Exception as exc:
            logger.error("Failed to init InsightFace: %s", exc)
            raise
    return _arcface_app


# ---------------------------------------------------------------------------
# Stage 1 – Face detection (BlazeFace via MediaPipe FaceMesh)
# ---------------------------------------------------------------------------

def detect_faces_mediapipe(bgr: np.ndarray):
    """
    Run BlazeFace + FaceMesh on *bgr* image.
    Returns list of dicts:
      {bbox: (x,y,w,h) pixels, confidence: float, landmarks: [[x,y,z], ...]}
    """
    mesh = _get_mediapipe()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = bgr.shape[:2]
    results = mesh.process(rgb)

    faces = []
    if not results.multi_face_landmarks:
        return faces

    for face_landmarks in results.multi_face_landmarks:
        xs = [lm.x for lm in face_landmarks.landmark]
        ys = [lm.y for lm in face_landmarks.landmark]

        x1 = max(0, int(min(xs) * w) - 10)
        y1 = max(0, int(min(ys) * h) - 10)
        x2 = min(w, int(max(xs) * w) + 10)
        y2 = min(h, int(max(ys) * h) + 10)

        landmarks_list = [
            [lm.x, lm.y, lm.z] for lm in face_landmarks.landmark
        ]

        faces.append({
            'bbox': (x1, y1, x2 - x1, y2 - y1),
            'confidence': 1.0,  # MediaPipe FaceMesh always confident
            'landmarks': landmarks_list,
        })

    return faces


# ---------------------------------------------------------------------------
# Stage 2 – Face alignment
# ---------------------------------------------------------------------------

# Standard 5-point landmarks used by InsightFace for alignment
# (indices into MediaPipe 468-point mesh)
# left-eye, right-eye, nose-tip, mouth-left, mouth-right
_MP_ALIGN_IDX = [33, 263, 1, 61, 291]

_TEMPLATE_5PT = np.float32([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041],
])

TARGET_SIZE = 112  # ArcFace canonical size


def align_face(bgr: np.ndarray, landmarks: list) -> Optional[np.ndarray]:
    """
    Affine-warp the face region to a 112×112 canonical alignment.
    *landmarks* is the 468-point list from MediaPipe.
    """
    h, w = bgr.shape[:2]
    src_pts = np.float32([
        [landmarks[i][0] * w, landmarks[i][1] * h]
        for i in _MP_ALIGN_IDX
    ])
    dst_pts = _TEMPLATE_5PT.copy()

    M = cv2.estimateAffinePartial2D(src_pts, dst_pts)[0]
    if M is None:
        return None

    aligned = cv2.warpAffine(bgr, M, (TARGET_SIZE, TARGET_SIZE))
    return aligned


# ---------------------------------------------------------------------------
# Stage 3 – ArcFace embedding (512-dim)
# ---------------------------------------------------------------------------

def get_embedding(aligned_face_bgr: np.ndarray) -> Optional[np.ndarray]:
    """
    Generate a 512-dim L2-normalised identity embedding via InsightFace.
    Input: aligned BGR face image (112×112 preferred).
    """
    try:
        app = _get_arcface()
        rgb = cv2.cvtColor(aligned_face_bgr, cv2.COLOR_BGR2RGB)
        # InsightFace expects at least a moderate-size image
        if rgb.shape[0] < 64:
            rgb = cv2.resize(rgb, (112, 112))
        faces = app.get(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        if not faces:
            # Fall back: embed the whole aligned chip
            return _embed_direct(rgb)
        emb = faces[0].normed_embedding  # already L2-normalised
        return emb.astype(np.float32)
    except Exception as exc:
        logger.warning("ArcFace embedding failed: %s", exc)
        return None


def _embed_direct(rgb: np.ndarray) -> Optional[np.ndarray]:
    """
    Direct embedding when InsightFace can't detect within the aligned crop.
    Uses the recognition model directly (bypasses detection).
    """
    try:
        from insightface.app import FaceAnalysis
        app = _get_arcface()
        rec = app.models.get('recognition')
        if rec is None:
            return None
        blob = cv2.resize(rgb, (112, 112))
        blob = (blob / 127.5 - 1.0).astype(np.float32)
        blob = blob.transpose(2, 0, 1)[np.newaxis]  # NCHW
        emb = rec.session.run(None, {rec.session.get_inputs()[0].name: blob})[0][0]
        emb /= np.linalg.norm(emb) + 1e-6
        return emb.astype(np.float32)
    except Exception as exc:
        logger.warning("Direct embedding failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Stage 4 – DBSCAN clustering
# ---------------------------------------------------------------------------

def cluster_faces(embeddings: List[np.ndarray], eps: float = 0.7, min_samples: int = 1):
    """
    Cluster a list of 512-dim embeddings using DBSCAN with cosine distance.
    Returns list of integer labels (−1 = noise).
    """
    if len(embeddings) < 2:
        return [0] * len(embeddings) if embeddings else []

    from sklearn.cluster import DBSCAN

    X = np.stack(embeddings)
    # Convert cosine distance to metric
    db = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = db.fit_predict(X)
    return labels.tolist()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-6)
    b = b / (np.linalg.norm(b) + 1e-6)
    return float(np.dot(a, b))


# ---------------------------------------------------------------------------
# Drawing utilities
# ---------------------------------------------------------------------------

def draw_detections(bgr: np.ndarray, faces: list) -> np.ndarray:
    """Draw bounding boxes and key landmarks on the image."""
    out = bgr.copy()
    for face in faces:
        x, y, w, h = face['bbox']
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 120), 2)
        cv2.putText(
            out,
            f"{face['confidence']:.2f}",
            (x, max(y - 6, 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 1, cv2.LINE_AA,
        )
        # Draw 5 alignment landmarks
        img_h, img_w = bgr.shape[:2]
        for idx in _MP_ALIGN_IDX:
            lm = face['landmarks'][idx]
            px, py = int(lm[0] * img_w), int(lm[1] * img_h)
            cv2.circle(out, (px, py), 2, (255, 80, 0), -1)
    return out


# ---------------------------------------------------------------------------
# Full pipeline entry-point
# ---------------------------------------------------------------------------

def process_image(uploaded_image_obj) -> dict:
    """
    Run the full pipeline on an UploadedImage model instance.
    Returns a summary dict.
    """
    from api.models import DetectedFace, FaceCluster

    img_path = os.path.join(settings.MEDIA_ROOT, uploaded_image_obj.original_image.name)
    bgr = cv2.imread(img_path)
    if bgr is None:
        raise ValueError(f"Could not read image: {img_path}")

    # --- Stage 1: Detect ---
    logger.info("Detecting faces in %s", uploaded_image_obj.filename)
    face_detections = detect_faces_mediapipe(bgr)
    logger.info("Found %d face(s)", len(face_detections))

    detected_faces = []
    embeddings = []

    for det in face_detections:
        x, y, w, h = det['bbox']
        landmarks = det['landmarks']
        confidence = det['confidence']

        # --- Stage 2: Align ---
        aligned = align_face(bgr, landmarks)

        # --- Stage 3: Embed ---
        emb = None
        if aligned is not None:
            emb = get_embedding(aligned)

        # Persist face record
        face = DetectedFace(
            image=uploaded_image_obj,
            bbox_x=x, bbox_y=y, bbox_w=w, bbox_h=h,
            confidence=confidence,
        )
        face.landmarks_json = json.dumps(landmarks)
        if emb is not None:
            face.set_embedding(emb)
            embeddings.append(emb)
        else:
            embeddings.append(None)

        # Save aligned thumbnail
        if aligned is not None:
            _, buf = cv2.imencode('.jpg', aligned)
            fname = f"faces/{uuid.uuid4().hex}.jpg"
            face.face_thumbnail.save(fname, ContentFile(buf.tobytes()), save=False)

        face.save()
        detected_faces.append(face)

    # --- Stage 4: Cluster all embeddings in the DB ---
    _recluster_all()

    # Draw annotated image
    annotated = draw_detections(bgr, face_detections)
    _, buf = cv2.imencode('.jpg', annotated)
    proc_name = f"processed/{uuid.uuid4().hex}.jpg"
    uploaded_image_obj.processed_image.save(proc_name, ContentFile(buf.tobytes()), save=False)
    uploaded_image_obj.face_count = len(face_detections)
    uploaded_image_obj.status = 'done'
    uploaded_image_obj.processed_at = timezone.now()
    uploaded_image_obj.save()

    return {
        'face_count': len(face_detections),
        'faces': [str(f.id) for f in detected_faces],
    }


def _recluster_all():
    """Re-run DBSCAN over all embeddings in the database."""
    from api.models import DetectedFace, FaceCluster

    faces = list(DetectedFace.objects.exclude(embedding_json=None))
    if not faces:
        return

    embs = [f.get_embedding() for f in faces]
    valid = [(i, e) for i, e in enumerate(embs) if e is not None]
    if not valid:
        return

    indices, vembs = zip(*valid)
    labels = cluster_faces(list(vembs))

    # Delete old clusters
    FaceCluster.objects.all().delete()

    # Build cluster objects
    label_to_cluster = {}
    for label in set(labels):
        cluster = FaceCluster.objects.create(label=label)
        label_to_cluster[label] = cluster
        # Compute centroid
        cluster_embs = [vembs[i] for i, l in enumerate(labels) if l == label]
        centroid = np.mean(cluster_embs, axis=0)
        centroid /= np.linalg.norm(centroid) + 1e-6
        cluster.set_centroid(centroid)
        cluster.save()

    # Assign faces to clusters
    for arr_idx, face_idx in enumerate(indices):
        label = labels[arr_idx]
        faces[face_idx].cluster = label_to_cluster[label]
        faces[face_idx].save(update_fields=['cluster'])

    logger.info("Reclustered %d faces into %d clusters.", len(valid), len(label_to_cluster))


def search_similar_faces(query_image_bytes: bytes, top_k: int = 10):
    """
    Given raw image bytes, detect + embed the first face and find the most
    similar faces in the database by cosine similarity.
    Returns list of (DetectedFace, similarity) sorted descending.
    """
    from api.models import DetectedFace

    nparr = np.frombuffer(query_image_bytes, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode query image")

    detections = detect_faces_mediapipe(bgr)
    if not detections:
        raise ValueError("No face detected in query image")

    aligned = align_face(bgr, detections[0]['landmarks'])
    if aligned is None:
        raise ValueError("Face alignment failed for query image")

    query_emb = get_embedding(aligned)
    if query_emb is None:
        raise ValueError("Could not generate embedding for query image")

    candidates = DetectedFace.objects.exclude(embedding_json=None)
    results = []
    for face in candidates:
        emb = face.get_embedding()
        if emb is not None:
            sim = cosine_similarity(query_emb, emb)
            results.append((face, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
