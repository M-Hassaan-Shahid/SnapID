"""Crop-to-spec geometry.

Given a detected face and a document spec, compute the crop rectangle
that puts the head at the spec's target height ratio with the eye line
at the target position, then resize to exact pixel dimensions.
"""
from dataclasses import dataclass

import cv2
import numpy as np

from app.core.face import Face
from app.core.specs import PRINT_DPI, PhotoSpec


class CropOutOfBoundsError(ValueError):
    """The subject is too close to the edge for a compliant crop."""


@dataclass
class CropResult:
    image: np.ndarray  # BGR, exact spec pixel size
    crop_box: tuple[int, int, int, int]  # x0, y0, x1, y1 in source pixels


def compute_crop_box(
    face: Face, spec: PhotoSpec, image_size: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Crop rectangle (x0, y0, x1, y1) in source pixel coordinates."""
    img_w, img_h = image_size

    crop_h = face.head_height / spec.head_target
    crop_w = crop_h * (spec.width_mm / spec.height_mm)

    eye_y = face.eye_center[1]
    y0 = eye_y - spec.eye_from_top_target * crop_h
    x0 = face.center_x - crop_w / 2

    return (round(x0), round(y0), round(x0 + crop_w), round(y0 + crop_h))


def crop_to_spec(
    image_bgr: np.ndarray,
    face: Face,
    spec: PhotoSpec,
    dpi: int = PRINT_DPI,
    allow_padding: bool = True,
) -> CropResult:
    """Crop and resize to the spec's exact pixel size.

    When the ideal crop extends past the source image, the edges are
    padded by replicating border pixels (safe here because ID photo
    backgrounds are replaced with a uniform color anyway). Set
    ``allow_padding=False`` to fail instead.
    """
    img_h, img_w = image_bgr.shape[:2]
    x0, y0, x1, y1 = compute_crop_box(face, spec, (img_w, img_h))

    pad_left = max(0, -x0)
    pad_top = max(0, -y0)
    pad_right = max(0, x1 - img_w)
    pad_bottom = max(0, y1 - img_h)

    if any((pad_left, pad_top, pad_right, pad_bottom)):
        if not allow_padding:
            raise CropOutOfBoundsError(
                "The face is too close to the photo edge for this document's "
                "framing. Step back from the camera and leave space above "
                "your head."
            )
        # Cap padding at 25% of the crop on any side — beyond that the
        # source truly doesn't contain enough scene to work with.
        crop_w, crop_h = x1 - x0, y1 - y0
        if max(pad_left, pad_right) > 0.25 * crop_w or max(pad_top, pad_bottom) > 0.25 * crop_h:
            raise CropOutOfBoundsError(
                "Too much of the required framing falls outside the photo. "
                "Retake with more space around your head and shoulders."
            )
        image_bgr = cv2.copyMakeBorder(
            image_bgr, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_REPLICATE
        )
        x0 += pad_left
        x1 += pad_left
        y0 += pad_top
        y1 += pad_top

    cropped = image_bgr[y0:y1, x0:x1]
    target = spec.pixel_size(dpi)
    resized = cv2.resize(cropped, target, interpolation=cv2.INTER_AREA)
    return CropResult(image=resized, crop_box=(x0, y0, x1, y1))
