"""Face detection with OpenCV YuNet.

YuNet returns a face box plus five landmarks (eyes, nose tip, mouth
corners), which is exactly what the crop geometry needs. The model file
(232 KB, Apache-2.0) ships with the repo — no download at runtime.
"""
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "face_detection_yunet_2023mar.onnx"


class NoFaceError(ValueError):
    """No usable face found in the image."""


class MultipleFacesError(ValueError):
    """More than one face found — ID photos must contain exactly one."""


@dataclass
class Face:
    # Face bounding box (x, y, w, h) — covers roughly eyebrows to chin.
    box: tuple[float, float, float, float]
    right_eye: tuple[float, float]
    left_eye: tuple[float, float]
    nose: tuple[float, float]
    confidence: float

    @property
    def eye_center(self) -> tuple[float, float]:
        return (
            (self.right_eye[0] + self.left_eye[0]) / 2,
            (self.right_eye[1] + self.left_eye[1]) / 2,
        )

    @property
    def chin_y(self) -> float:
        return self.box[1] + self.box[3]

    @property
    def crown_y(self) -> float:
        """Estimated top of the head including hair.

        YuNet's box starts near the eyebrows. Anthropometric rule of
        thumb: the eyes sit roughly halfway between crown and chin, so
        crown ≈ eye_line - (chin - eye_line).
        """
        eye_y = self.eye_center[1]
        return eye_y - (self.chin_y - eye_y)

    @property
    def head_height(self) -> float:
        return self.chin_y - self.crown_y

    @property
    def center_x(self) -> float:
        return self.box[0] + self.box[2] / 2


_detector = None


def _get_detector(size: tuple[int, int]) -> cv2.FaceDetectorYN:
    global _detector
    if _detector is None:
        _detector = cv2.FaceDetectorYN.create(
            str(MODEL_PATH), "", size, score_threshold=0.7
        )
    _detector.setInputSize(size)
    return _detector


def detect_face(image_bgr: np.ndarray) -> Face:
    """Find exactly one face. Raises NoFaceError / MultipleFacesError."""
    h, w = image_bgr.shape[:2]

    # YuNet degrades on very large inputs; detect on a bounded copy.
    scale = 1.0
    max_side = 1280
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        small = cv2.resize(image_bgr, (round(w * scale), round(h * scale)))
    else:
        small = image_bgr

    detector = _get_detector((small.shape[1], small.shape[0]))
    _, faces = detector.detect(small)
    if faces is None or len(faces) == 0:
        raise NoFaceError(
            "No face detected. Use a clear, well-lit, front-facing photo."
        )
    if len(faces) > 1:
        raise MultipleFacesError(
            f"Found {len(faces)} faces — the photo must contain exactly one person."
        )

    f = faces[0] / scale  # back to original coordinates
    conf = float(faces[0][14])
    return Face(
        box=(float(f[0]), float(f[1]), float(f[2]), float(f[3])),
        right_eye=(float(f[4]), float(f[5])),
        left_eye=(float(f[6]), float(f[7])),
        nose=(float(f[8]), float(f[9])),
        confidence=conf,
    )
