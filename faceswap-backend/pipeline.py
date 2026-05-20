"""
End-to-end swap pipeline. Orchestrates all stages in correct order.
inswapper is called here — it was missing entirely in the broken version.
"""

import os
import time

import cv2
import numpy as np
from blender import FaceBlender
from detector import RobustFaceDetector
from face_struct import build_face_struct
from restorer import FaceRestorer
from swapper import FaceSwapper
from utils import resize_if_too_large


class SwapPipeline:
    def __init__(self, models_dir: str):
        print("[pipeline] Initializing detector (UniFace auto-downloads)...")
        self.detector = RobustFaceDetector()

        print("[pipeline] Loading inswapper_128.onnx...")
        self.swapper = FaceSwapper(os.path.join(models_dir, "inswapper_128.onnx"))

        print("[pipeline] Initializing blender (XSeg/BiSeNet)...")
        self.blender = FaceBlender()

        print("[pipeline] Loading GFPGAN restorer...")
        self.restorer = FaceRestorer(os.path.join(models_dir, "gfpgan_1.4.onnx"))

        self.models_loaded = True
        print("[pipeline] All models ready.")

    def run(
        self,
        source_img_bgr: np.ndarray,
        target_img_bgr: np.ndarray,
        enhance: bool = True,
    ) -> tuple:
        """
        Full pipeline. Returns (result_bgr, warnings_list).

        Stage order:
          1. Resize inputs to max 1024px
          2. Detect source face → get identity
          3. Detect target face → get swap region
          4. Build inswapper-compatible FaceStructs
          5. Call inswapper → identity transfer with paste_back
          6. Generate blend mask from TARGET face on SWAPPED image
          7. Color correct + Poisson blend seam
          8. GFPGAN restoration on target face region
          9. Mild unsharp mask for final crispness
        """
        warnings = []
        timings = {}

        # ── STAGE 1: Resize ──────────────────────────────────────────
        source_img_bgr = resize_if_too_large(source_img_bgr, 1024)
        target_img_bgr = resize_if_too_large(target_img_bgr, 1024)

        # ── STAGE 2 & 3: Detect faces ────────────────────────────────
        t = time.time()
        try:
            source_face = self.detector.get_largest_face(source_img_bgr)
        except ValueError as e:
            raise ValueError(f"Source image: {e}")

        try:
            target_face = self.detector.get_largest_face(target_img_bgr)
        except ValueError as e:
            raise ValueError(f"Template image: {e}")
        timings["detect"] = time.time() - t

        # Collect any pose warnings
        if source_face.get("pose_warning"):
            warnings.append("Source: " + source_face["pose_warning"])
        if target_face.get("pose_warning"):
            warnings.append("Template: " + target_face["pose_warning"])

        # ── STAGE 4: Build FaceStructs ───────────────────────────────
        source_struct = build_face_struct(source_face)
        target_struct = build_face_struct(target_face)

        # Validate structs before passing to inswapper
        _validate_face_struct(source_struct, "source")
        _validate_face_struct(target_struct, "target")

        # ── STAGE 5: Identity transfer (THE ACTUAL SWAP) ─────────────
        t = time.time()
        swapped = self.swapper.swap(target_img_bgr, target_struct, source_struct)
        timings["swap"] = time.time() - t
        print(f"[pipeline] swap: {timings['swap']:.2f}s")

        # ── STAGE 6 & 7: Blend seam ───────────────────────────────────
        # Pass target_face (not source_face) — the mask covers the TARGET
        # face region where the seam needs to be blended
        t = time.time()
        blended = self.blender.blend(swapped, target_img_bgr, target_face)
        timings["blend"] = time.time() - t
        print(f"[pipeline] blend: {timings['blend']:.2f}s")

        # ── STAGE 8: Face restoration ─────────────────────────────────
        if enhance and self.restorer.is_available():
            t = time.time()
            try:
                blended = self.restorer.restore(blended, target_face["bbox"])
                timings["restore"] = time.time() - t
                print(f"[pipeline] restore: {timings['restore']:.2f}s")
            except Exception as e:
                print(f"[pipeline] GFPGAN failed (non-fatal): {e}")
                warnings.append(
                    "Restoration step failed — returning unrestored result."
                )
        elif enhance and not self.restorer.is_available():
            warnings.append(
                "GFPGAN model not found. Place gfpgan_1.4.onnx in models/ for better quality."
            )

        # ── STAGE 9: Unsharp mask (Aggressive for better feature definition) ──
        gaussian = cv2.GaussianBlur(blended, (0, 0), 3)
        blended = cv2.addWeighted(blended, 1.6, gaussian, -0.6, 0)
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        print(f"[pipeline] total: {sum(timings.values()):.2f}s | stages: {timings}")
        return blended, warnings


def _validate_face_struct(struct, name: str):
    """
    Validate that a FaceStruct has the correct shapes for inswapper.
    Raises ValueError with clear message if anything is wrong.
    """
    if struct.kps is None or struct.kps.shape != (5, 2):
        raise ValueError(
            f"{name} face keypoints invalid. "
            f"Expected shape (5,2), got {struct.kps.shape if struct.kps is not None else None}. "
            "Try a clearer, more frontal photo."
        )
    if struct.embedding is None or struct.embedding.shape != (512,):
        raise ValueError(
            f"{name} face embedding invalid. "
            f"Expected shape (512,), got {struct.embedding.shape if struct.embedding is not None else None}."
        )
    emb_norm = np.linalg.norm(struct.embedding)
    if emb_norm < 0.1:
        raise ValueError(
            f"{name} face embedding is near-zero (norm={emb_norm:.4f}). "
            "Face recognition failed — try a clearer photo."
        )
