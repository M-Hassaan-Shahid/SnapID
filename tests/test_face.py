import numpy as np
import pytest

from app.core.face import NoFaceError, detect_face


def test_detects_portrait(portrait_bgr):
    face = detect_face(portrait_bgr)
    assert face.confidence > 0.7
    # Eyes must sit above the chin and inside the box.
    assert face.eye_center[1] < face.chin_y
    x, y, w, h = face.box
    assert x <= face.eye_center[0] <= x + w


def test_geometry_relationships(portrait_bgr):
    face = detect_face(portrait_bgr)
    assert face.crown_y < face.eye_center[1] < face.chin_y
    assert face.head_height > 0


def test_no_face(blank_image):
    with pytest.raises(NoFaceError):
        detect_face(blank_image)


def test_large_image_downscale_path(portrait_bgr):
    import cv2

    big = cv2.resize(portrait_bgr, None, fx=4, fy=4)  # 2048px wide
    face_big = detect_face(big)
    face_small = detect_face(portrait_bgr)
    # Coordinates should map back to the original scale within tolerance.
    assert face_big.center_x / 4 == pytest.approx(face_small.center_x, abs=15)
