"""
inswapper_128.onnx wrapper using InsightFace's model_zoo loader.
This is the ONLY file in the project that imports insightface.
"""

import logging

import insightface
import numpy as np
from utils import get_ort_providers

logger = logging.getLogger(__name__)


class FaceSwapper:
    def __init__(self, model_path: str):
        """
        Load inswapper_128.onnx via InsightFace's model_zoo.
        This handles the model's internal ArcFace emap subgraph and
        custom tensor layout — not reproducible with plain onnxruntime.
        """
        providers = get_ort_providers()
        logger.info(f"Loading FaceSwapper with providers: {providers}")

        self.model = insightface.model_zoo.get_model(model_path, providers=providers)
        # Prepare model for inference.
        # Use ctx_id=0 if CUDA is available, else -1 for CPU.
        ctx_id = 0 if "CUDAExecutionProvider" in providers else -1

        if hasattr(self.model, "prepare"):
            self.model.prepare(ctx_id=ctx_id)

    def swap(
        self,
        target_img_bgr: np.ndarray,
        target_face,  # FaceStruct with .bbox, .kps, .embedding
        source_face,  # FaceStruct with .bbox, .kps, .embedding
    ) -> np.ndarray:
        """
        Transfer source identity onto target face region.

        paste_back=True: InsightFace handles the alignment, inference, and
        pasting the swapped face back onto the full target image internally.
        Returns full-resolution BGR image — same size as target_img_bgr.

        The output still has seam artifacts and possible color mismatch.
        That is blender.py's job to fix.
        """
        result = self.model.get(
            target_img_bgr, target_face, source_face, paste_back=True
        )

        # Robustness Addition 3: Swapper input/output logging
        logger.info(
            f"INPUTS: target_img.shape={target_img_bgr.shape}, "
            f"target_face.kps.shape={target_face.kps.shape if target_face.kps is not None else None}, "
            f"source_face.embedding.shape={source_face.embedding.shape if source_face.embedding is not None else None}"
        )

        if result is not None:
            logger.info(
                f"OUTPUT: result.shape={result.shape}, result.dtype={result.dtype}, "
                f"min={result.min()}, max={result.max()}"
            )
        else:
            logger.warning("OUTPUT: result is None")

        if result is None:
            raise ValueError(
                "inswapper returned None. Check that source and target "
                "face structs have valid .kps (5x2) and .embedding (512,) arrays."
            )
        return result
