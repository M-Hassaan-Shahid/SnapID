"""Background replacement: person segmentation + uniform color fill.

rembg (u2net) produces an alpha matte for the subject; the photo is then
composited over the spec's required background color. A light Gaussian
blur on the matte edge avoids halo artifacts around hair.
"""
import cv2
import numpy as np


def replace_background(
    image_bgr: np.ndarray, background_rgb: tuple[int, int, int]
) -> np.ndarray:
    from rembg import remove  # heavy import (onnxruntime); keep it local

    rgba = remove(
        cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB),
        post_process_mask=True,
    )
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)[:, :, np.newaxis]

    subject_bgr = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2BGR).astype(np.float32)
    bg = np.empty_like(subject_bgr)
    bg[:] = background_rgb[::-1]  # RGB → BGR

    out = subject_bgr * alpha + bg * (1.0 - alpha)
    return out.clip(0, 255).astype(np.uint8)
