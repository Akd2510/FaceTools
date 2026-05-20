"""
Blending pipeline: XSeg mask → color correction → alpha/Poisson blend.
Mask is generated from TARGET face region on the SWAPPED image.
"""

import cv2
import numpy as np

try:
    from uniface.parsing import XSeg

    PARSER_CLASS = XSeg
    PARSER_NAME = "XSeg"
except ImportError:
    try:
        from uniface.parsing import BiSeNet

        PARSER_CLASS = BiSeNet
        PARSER_NAME = "BiSeNet"
    except ImportError:
        PARSER_CLASS = None
        PARSER_NAME = "None"


class FaceBlender:
    def __init__(self):
        if PARSER_CLASS is not None:
            self.segmenter = PARSER_CLASS(providers=["CPUExecutionProvider"])
            print(f"[blender] Using {PARSER_NAME} for face masking.")
        else:
            self.segmenter = None
            print(
                "[blender] WARNING: No segmenter available — using bbox fallback mask."
            )

    def get_mask(
        self, img_bgr: np.ndarray, face_dict: dict, padding_ratio: float = 0.25
    ) -> np.ndarray:
        """
        Generate a soft face mask from the TARGET face region on the SWAPPED image.
        Robustness Addition 4: 3-tier fallback chain.
        """
        bbox = face_dict["bbox"]
        lmks_106 = face_dict.get("lmks_106")
        h_img, w_img = img_bgr.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in bbox]
        fw, fh = x2 - x1, y2 - y1

        # Expand bbox for context
        pad_x = int(fw * padding_ratio)
        pad_y = int(fh * padding_ratio)
        cx1 = max(0, x1 - pad_x)
        cy1 = max(0, y1 - pad_y)
        cx2 = min(w_img, x2 + pad_x)
        cy2 = min(h_img, y2 + pad_y)

        crop = img_bgr[cy1:cy2, cx1:cx2]
        crop_h, crop_w = crop.shape[:2]

        mask_crop = None

        # Tier 1: XSeg/BiSeNet segmentation
        if self.segmenter is not None:
            mask_crop = _run_segmenter(self.segmenter, crop)
            if mask_crop is not None:
                # For multi-class outputs (BiSeNet), threshold to face classes only
                if len(np.unique(mask_crop)) > 3:
                    mask_crop = np.where(
                        (mask_crop >= 1) & (mask_crop <= 13), 1.0, 0.0
                    ).astype(np.float32)
                else:
                    mask_crop = np.where(mask_crop > 0.3, 1.0, 0.0).astype(np.float32)

        # Tier 2: Convex hull of 106pt landmarks
        if mask_crop is None and lmks_106 is not None:
            print("[blender] Tier 1 failed, falling back to Tier 2 (Landmark Hull)")
            # Adjust landmarks to crop coordinates
            crop_lmks = lmks_106 - [cx1, cy1]
            mask_crop = _landmark_hull_mask(crop_lmks, (crop_h, crop_w))

        # Tier 3: Ellipse fitted to bbox
        if mask_crop is None:
            print("[blender] Tier 1 & 2 failed, falling back to Tier 3 (Bbox Ellipse)")
            mask_crop = _bbox_ellipse_mask(
                [pad_x, pad_y, pad_x + fw, pad_y + fh], (crop_h, crop_w)
            )

        # Ensure float [0,1]
        mask_crop = np.clip(mask_crop, 0.0, 1.0).astype(np.float32)

        # Expand mask to include forehead (shift up by 15% of face height)
        shift_px = int(fh * 0.15)
        mask_crop = np.roll(mask_crop, -shift_px, axis=0)
        mask_crop[-shift_px:, :] = 0.0

        # Dilate to cover hairline and temples
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        mask_crop = cv2.dilate(mask_crop, kernel, iterations=2)

        # Gaussian feather for invisible seam
        mask_crop = cv2.GaussianBlur(mask_crop, (51, 51), 20)
        mask_crop = np.clip(mask_crop, 0.0, 1.0)

        # Place crop mask back into full-image space
        full_mask = np.zeros((h_img, w_img), dtype=np.float32)
        full_mask[cy1:cy2, cx1:cx2] = mask_crop

        return full_mask

    def color_correct(
        self, swapped: np.ndarray, target: np.ndarray, mask: np.ndarray
    ) -> np.ndarray:
        """
        Match skin tone of swapped face region to target image lighting.
        """
        mask_idx = mask > 0.5
        if not np.any(mask_idx):
            return swapped

        swapped_lab = cv2.cvtColor(swapped, cv2.COLOR_BGR2LAB).astype(np.float32)
        target_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)

        corrected_lab = swapped_lab.copy()
        for ch in range(3):
            swp_vals = swapped_lab[:, :, ch][mask_idx]
            tgt_vals = target_lab[:, :, ch][mask_idx]

            swp_mean, swp_std = swp_vals.mean(), swp_vals.std()
            tgt_mean, tgt_std = tgt_vals.mean(), tgt_vals.std()

            if swp_std > 1e-6:
                corrected_lab[:, :, ch] = (swapped_lab[:, :, ch] - swp_mean) * (
                    tgt_std / swp_std
                ) + tgt_mean
            else:
                corrected_lab[:, :, ch] = swapped_lab[:, :, ch] + (tgt_mean - swp_mean)

        corrected_lab = np.clip(corrected_lab, 0, 255).astype(np.uint8)
        corrected_bgr = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)

        # Only apply correction within mask region
        mask_3ch = np.stack([mask] * 3, axis=-1)
        result = (corrected_bgr * mask_3ch + swapped * (1.0 - mask_3ch)).astype(
            np.uint8
        )
        return result

    def poisson_blend(
        self, swapped: np.ndarray, target: np.ndarray, mask: np.ndarray, center: tuple
    ) -> np.ndarray:
        """
        Poisson seamless clone — smooths gradient discontinuity at seam.
        """
        mask_u8 = (mask * 255).astype(np.uint8)

        # Erode slightly to pull boundary inward
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_eroded = cv2.erode(mask_u8, kernel, iterations=2)

        h, w = target.shape[:2]
        cx = max(1, min(center[0], w - 2))
        cy = max(1, min(center[1], h - 2))

        try:
            result = cv2.seamlessClone(
                swapped, target, mask_eroded, (cx, cy), cv2.NORMAL_CLONE
            )
            return result
        except cv2.error as e:
            print(f"[blender] seamlessClone failed ({e}), falling back to alpha blend.")
            mask_3ch = np.stack([mask] * 3, axis=-1)
            return (swapped * mask_3ch + target * (1.0 - mask_3ch)).astype(np.uint8)

    def blend(
        self, swapped: np.ndarray, target: np.ndarray, target_face_dict: dict
    ) -> np.ndarray:
        """
        Full blend pipeline.
        """
        bbox = target_face_dict["bbox"]
        x1, y1, x2, y2 = [int(v) for v in bbox]

        # Generate mask from SWAPPED image using TARGET face region
        mask = self.get_mask(swapped, target_face_dict)

        # Color correct
        color_corrected = self.color_correct(swapped, target, mask)

        # Poisson blend — center of target face bbox
        center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
        result = self.poisson_blend(color_corrected, target, mask, center)

        return result


def _run_segmenter(segmenter, crop: np.ndarray) -> np.ndarray:
    crop_h, crop_w = crop.shape[:2]
    for method_name in ("segment", "predict", "parse", "forward"):
        fn = getattr(segmenter, method_name, None)
        if fn is None:
            continue
        try:
            result = fn(crop)
            if result is not None:
                if isinstance(result, np.ndarray):
                    if result.shape[:2] != (crop_h, crop_w):
                        result = cv2.resize(
                            result.astype(np.float32),
                            (crop_w, crop_h),
                            interpolation=cv2.INTER_LINEAR,
                        )
                    return result.astype(np.float32)
        except Exception as e:
            print(f"[blender] segmenter.{method_name}() failed: {e}")
            continue
    return None


def _bbox_ellipse_mask(bbox, img_shape):
    h, w = img_shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    x1, y1, x2, y2 = [int(v) for v in bbox]
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    rx, ry = (x2 - x1) // 2, (y2 - y1) // 2
    cv2.ellipse(mask, (cx, cy), (rx, ry), 0, 0, 360, 1.0, -1)
    return mask


def _landmark_hull_mask(lmks_106, img_shape):
    if lmks_106 is None:
        return None
    h, w = img_shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    # Use jawline points for the hull
    pts = lmks_106[:33].astype(np.int32)
    hull = cv2.convexHull(pts)
    cv2.fillConvexPoly(mask, hull, 1.0)
    return mask
