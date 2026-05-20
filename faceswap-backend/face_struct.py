import cv2
import numpy as np


class FaceStruct:
    """
    Mimics InsightFace Face object. inswapper reads these attributes directly.
    """

    def __init__(self, bbox, kps_5pt, embedding, det_score):
        self.bbox = np.array(bbox, dtype=np.float32)  # (4,)
        self.kps = np.array(kps_5pt, dtype=np.float32)  # (5, 2)
        self.embedding = np.array(embedding, dtype=np.float32)  # (512,)
        self.normed_embedding = self.embedding / (np.linalg.norm(self.embedding) + 1e-6)
        self.det_score = float(det_score)
        self.gender = None  # not used by inswapper
        self.age = None  # not used by inswapper


def build_face_struct(face_dict: dict) -> FaceStruct:
    """
    Takes the dict from RobustFaceDetector and returns an inswapper-compatible FaceStruct.
    """
    return FaceStruct(
        bbox=face_dict["bbox"],
        kps_5pt=face_dict["kps_5pt"],
        embedding=face_dict["embedding"],
        det_score=face_dict["det_score"],
    )


def align_face_to_112(img_bgr: np.ndarray, kps_5pt: np.ndarray) -> np.ndarray:
    """
    Affine-warp face region to canonical 112x112 using the 5 keypoints.
    """
    dst = np.array(
        [
            [38.2946, 51.6963],
            [73.5318, 51.5014],
            [56.0252, 71.7366],
            [41.5493, 92.3655],
            [70.7299, 92.2041],
        ],
        dtype=np.float32,
    )

    M, _ = cv2.estimateAffinePartial2D(kps_5pt, dst)
    if M is None:
        raise ValueError("Could not compute face alignment transform.")

    aligned = cv2.warpAffine(
        img_bgr, M, (112, 112), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT
    )
    return aligned
