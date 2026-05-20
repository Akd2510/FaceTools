"""
GFPGAN v1.4 ONNX face restoration.
Fixes quality loss from inswapper's 128px internal processing.
Input: 512x512 RGB float32 normalized to [-1, 1]
Output: 512x512 RGB float32 normalized to [-1, 1]
"""

import os

import cv2
import numpy as np
import onnxruntime as ort


class FaceRestorer:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            print(
                f"[restorer] GFPGAN not found at {model_path} — restoration disabled."
            )
            self.session = None
            return

        self.session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self.input_size = 512
        print(f"[restorer] GFPGAN loaded ({os.path.getsize(model_path) / 1e6:.0f} MB)")

    def restore(
        self, img_bgr: np.ndarray, bbox: np.ndarray, padding_ratio: float = 0.25
    ) -> np.ndarray:
        """
        Restore face quality in the bbox region.
        Operates on the full-resolution face crop — do NOT resize to 128 before calling.
        """
        if self.session is None:
            return img_bgr

        h_img, w_img = img_bgr.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in bbox]
        fw, fh = x2 - x1, y2 - y1

        # Skip if face too small
        if fw < 80 or fh < 80:
            return img_bgr

        # Expand bbox
        pad_x = int(fw * padding_ratio)
        pad_y = int(fh * padding_ratio)
        cx1 = max(0, x1 - pad_x)
        cy1 = max(0, y1 - pad_y)
        cx2 = min(w_img, x2 + pad_x)
        cy2 = min(h_img, y2 + pad_y)

        crop = img_bgr[cy1:cy2, cx1:cx2].copy()
        orig_h, orig_w = crop.shape[:2]

        # Preprocess for GFPGAN
        resized = cv2.resize(
            crop, (self.input_size, self.input_size), interpolation=cv2.INTER_LANCZOS4
        )
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = (rgb.astype(np.float32) / 255.0 - 0.5) / 0.5  # [-1, 1]
        tensor = tensor.transpose(2, 0, 1)[np.newaxis, ...]  # (1,3,512,512)

        # Inference
        try:
            out = self.session.run(None, {self.input_name: tensor})[0][0]
        except Exception as e:
            print(f"[restorer] GFPGAN inference failed: {e}")
            return img_bgr

        # Postprocess
        out = out.transpose(1, 2, 0)  # (512,512,3)
        out = np.clip((out + 1) / 2.0 * 255.0, 0, 255).astype(np.uint8)
        out = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)

        # Resize restored patch back to original crop dimensions
        restored_crop = cv2.resize(
            out, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4
        )

        # Feathered paste
        result = img_bgr.copy()
        border_px = max(5, int(min(orig_w, orig_h) * 0.08))

        feather = np.ones((orig_h, orig_w), dtype=np.float32)
        feather[:border_px, :] = np.linspace(0, 1, border_px)[:, np.newaxis]
        feather[-border_px:, :] = np.linspace(1, 0, border_px)[:, np.newaxis]
        feather[:, :border_px] *= np.linspace(0, 1, border_px)[np.newaxis, :]
        feather[:, -border_px:] *= np.linspace(1, 0, border_px)[np.newaxis, :]
        feather_3ch = np.stack([feather] * 3, axis=-1)

        result[cy1:cy2, cx1:cx2] = (
            restored_crop * feather_3ch
            + img_bgr[cy1:cy2, cx1:cx2] * (1.0 - feather_3ch)
        ).astype(np.uint8)

        return result

    def is_available(self) -> bool:
        return self.session is not None
