"""
Face detection using UniFace. Returns dicts with bbox, 5pt keypoints,
106pt landmarks, ArcFace embedding, confidence, and optional pose warning.
"""

import logging

import cv2
import numpy as np
from face_struct import align_face_to_112
from uniface import ArcFace, Landmark106, YOLOv8Face
from utils import get_ort_providers

logger = logging.getLogger(__name__)


class RobustFaceDetector:
    def __init__(self):
        providers = get_ort_providers()
        logger.info(f"Initializing detector with providers: {providers}")
        self.detector = YOLOv8Face(providers=providers)
        self.recognizer = ArcFace(providers=providers)
        self.landmarker = Landmark106(providers=providers)

        # Robustness Addition 2: UniFace API probe
        self._probe_uniface_api()

    def _probe_uniface_api(self):
        logger.info(
            f"ArcFace methods: {[m for m in dir(self.recognizer) if not m.startswith('_')]}"
        )
        logger.info(
            f"Landmark106 methods: {[m for m in dir(self.landmarker) if not m.startswith('_')]}"
        )

    def get_faces(self, img_bgr: np.ndarray, min_face_px: int = 80) -> list:
        """
        Detects all valid faces. Returns list of dicts sorted by area (largest first).
        Each dict contains: bbox, kps_5pt, lmks_106, embedding, det_score,
                            area, pose_warning.
        """

        # Robustness Addition 1: Retry logic
        raw_faces = None
        last_err = None

        for attempt in range(3):
            proc_img = _preprocess_retry(img_bgr, attempt)
            try:
                raw_faces = self.detector.detect(proc_img)
                if raw_faces:
                    # If we used a preprocessed image for detection,
                    # we still need to use the original for landmarks/embedding
                    # to avoid artifacts, OR we use the preprocessed one if it helps them too.
                    # Here we stick to proc_img for consistency in this attempt.
                    img_to_use = proc_img
                    break
            except Exception as e:
                last_err = e
                logger.warning(f"Detection attempt {attempt} failed: {e}")
                continue

        if not raw_faces:
            raise ValueError(
                "No face detected. Try a clearer photo with good lighting "
                "and a visible, unobstructed face."
            )

        logger.info(f"Found {len(raw_faces)} raw face candidates. Processing...")

        valid = []
        for face in raw_faces:
            x1, y1, x2, y2 = face.bbox
            w, h = x2 - x1, y2 - y1

            if w < min_face_px or h < min_face_px:
                logger.info(f"Rejected face: too small ({w}x{h} < {min_face_px})")
                continue
            if face.confidence < 0.50:
                logger.info(
                    f"Rejected face: low confidence ({face.confidence:.2f} < 0.50)"
                )
                continue

            # 5-point landmarks from detector (used for alignment + embedding)
            kps_5pt = np.array(face.landmarks, dtype=np.float32)
            if kps_5pt.shape != (5, 2):
                logger.warning(f"Rejected face: malformed landmarks {kps_5pt.shape}")
                continue  # malformed detection, skip

            # 106-point landmark refinement (used for masking)
            try:
                lmks_106 = self.landmarker.get_landmarks(img_to_use, face.bbox)
                if lmks_106 is None or lmks_106.shape[0] < 106:
                    lmks_106 = _estimate_106_from_5pt(kps_5pt, face.bbox)
            except Exception:
                lmks_106 = _estimate_106_from_5pt(kps_5pt, face.bbox)

            # ArcFace embedding
            # Identity Boost: Sharpen image before embedding to make features more prominent
            kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
            img_for_embed = cv2.filter2D(img_to_use, -1, kernel)

            embedding = None
            try:
                # Priority 1: Internal alignment (image + kps)
                embedding = self.recognizer.get_embedding(img_for_embed, kps_5pt)
                if embedding is not None:
                    embedding = np.array(embedding, dtype=np.float32).squeeze()
                    if embedding.size == 512:
                        logger.info("Embedding success (internal alignment)")
                    else:
                        embedding = None
            except Exception as e:
                logger.error(f"Internal alignment embedding failed: {e}")

            if embedding is None:
                try:
                    # Priority 2: Pre-aligned 112x112 crop
                    aligned_112 = align_face_to_112(img_to_use, kps_5pt)
                    embedding = self.recognizer.get_embedding(aligned_112)
                    if embedding is not None:
                        embedding = np.array(embedding, dtype=np.float32).squeeze()
                        if embedding.size == 512:
                            logger.info("Embedding success (manual alignment)")
                        else:
                            embedding = None
                except Exception as e:
                    logger.error(f"Manual alignment embedding failed: {e}")

            if embedding is None or embedding.size != 512:
                logger.warning("Rejected face: embedding invalid (None or size!=512)")
                continue

            # Pose estimation
            # Use kps_5pt for pose check as it's more robust than 106pt refinement
            pose_warning = _estimate_pose_warning(kps_5pt, face.bbox)

            # Log for debugging
            logger.info(
                f"Face at {face.bbox[:2]}: score={face.confidence:.2f}, pose={pose_warning}"
            )

            # DISABLE HARD REJECT for troubleshooting — convert to warning instead
            if pose_warning == "HARD_REJECT":
                pose_warning = "Extreme side angle detected — result may be poor."

            valid.append(
                {
                    "bbox": np.array(face.bbox, dtype=np.float32),
                    "kps_5pt": kps_5pt,
                    "lmks_106": lmks_106,
                    "embedding": embedding,
                    "det_score": float(face.confidence),
                    "area": float(w * h),
                    "pose_warning": pose_warning if pose_warning != "OK" else None,
                }
            )

        if not valid:
            raise ValueError(
                "Face detected but not usable — try a more frontal photo. "
                "Extreme side angles are not supported by the swap model."
            )

        return sorted(valid, key=lambda x: x["area"], reverse=True)

    def get_largest_face(self, img_bgr: np.ndarray, min_face_px: int = 80) -> dict:
        return self.get_faces(img_bgr, min_face_px)[0]


def _preprocess_retry(img, attempt):
    if attempt == 1:
        # CLAHE contrast enhancement
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    elif attempt == 2:
        # Slight sharpening
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        return cv2.filter2D(img, -1, kernel)
    return img


def _estimate_pose_warning(kps_5pt: np.ndarray, bbox) -> str:
    """
    Estimate yaw from eye landmark symmetry.
    Returns 'OK', a warning string, or 'HARD_REJECT'.
    """
    try:
        left_eye = kps_5pt[0]
        right_eye = kps_5pt[1]

        # Use Euclidean distance to handle tilted heads
        eye_width = np.linalg.norm(right_eye - left_eye)
        face_width = abs(bbox[2] - bbox[0]) + 1e-6
        ratio = eye_width / face_width

        logger.info(
            f"Pose check: eye_dist={eye_width:.1f}, face_w={face_width:.1f}, ratio={ratio:.3f}"
        )

        # ratio ~0.42 = frontal, drops toward 0 at profile
        # Hard reject at ratio < 0.08 (~75° yaw) — lowered from 0.12 to be more permissive
        if ratio < 0.08:
            return "HARD_REJECT"
        elif ratio < 0.18:
            return "Face is angled sideways — result quality may be reduced."
        return "OK"
    except Exception:
        return "OK"  # don't block on pose estimation failure


def _estimate_106_from_5pt(kps_5pt: np.ndarray, bbox) -> np.ndarray:
    """
    Fallback: approximate 106pt landmarks from 5pt detections.
    Only used when Landmark106 fails. Not accurate but prevents crashes.
    Returns array of shape (106, 2) filled with bbox-anchored estimates.
    """
    x1, y1, x2, y2 = bbox
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    lmks = np.full((106, 2), [cx, cy], dtype=np.float32)
    # Anchor the 5 canonical points at their correct indices
    # Left eye region: indices 33-42
    for i in range(33, 43):
        lmks[i] = kps_5pt[0]
    # Right eye region: indices 87-96
    for i in range(87, 97):
        lmks[i] = kps_5pt[1]
    lmks[54] = kps_5pt[2]  # nose tip
    lmks[76] = kps_5pt[3]  # mouth left
    lmks[82] = kps_5pt[4]  # mouth right
    return lmks
