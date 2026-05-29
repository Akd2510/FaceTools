import base64
import logging
import os

import cv2
import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)


def get_ort_providers():
    """
    Returns a list of available ONNX Runtime providers,
    prioritizing CUDAExecutionProvider if available.
    """
    available = ort.get_available_providers()
    providers = []
    if "CUDAExecutionProvider" in available:
        providers.append("CUDAExecutionProvider")
    providers.append("CPUExecutionProvider")
    return providers


def read_image_from_upload(file_bytes: bytes) -> np.ndarray:
    """
    Decodes bytes from an upload to a BGR numpy array.
    """
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image. Supported formats: JPG, PNG, WEBP.")
    if img.shape[0] < 100 or img.shape[1] < 100:
        raise ValueError("Image too small. Minimum size is 100x100 pixels.")
    return img


def numpy_to_base64_png(img_bgr: np.ndarray) -> str:
    """
    Encodes a BGR image to a base64-encoded PNG string.
    """
    success, buf = cv2.imencode(".png", img_bgr)
    if not success:
        raise RuntimeError("Failed to encode result image.")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def resize_if_too_large(img: np.ndarray, max_dim: int = 1024) -> np.ndarray:
    """
    Resizes the image if its longest side exceeds max_dim.
    """
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def verify_model_file(path: str, name: str) -> bool:
    """
    Verifies if a model file exists and logs its size.
    """
    if not os.path.exists(path):
        logger.warning(f"{name} not found at {path}")
        return False
    size_mb = os.path.getsize(path) / 1e6
    logger.info(f"{name} loaded — {size_mb:.1f} MB")
    return True
