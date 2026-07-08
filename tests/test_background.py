import numpy as np

from app.core.background import replace_background


def test_background_becomes_uniform_white(portrait_bgr):
    out = replace_background(portrait_bgr, (255, 255, 255))
    assert out.shape == portrait_bgr.shape
    assert out.dtype == np.uint8

    # Top corners must now be (near) pure white.
    h, w = out.shape[:2]
    m = h // 20
    for patch in (out[0:m, 0:m], out[0:m, w - m : w]):
        assert patch.mean() > 235, f"corner mean {patch.mean():.0f} not white"


def test_subject_preserved(portrait_bgr):
    """The face region must stay essentially unchanged."""
    from app.core.face import detect_face

    face = detect_face(portrait_bgr)
    x, y, w, h = [int(v) for v in face.box]
    out = replace_background(portrait_bgr, (255, 255, 255))
    before = portrait_bgr[y : y + h, x : x + w].astype(float)
    after = out[y : y + h, x : x + w].astype(float)
    assert np.abs(before - after).mean() < 10.0


def test_custom_background_color(portrait_bgr):
    out = replace_background(portrait_bgr, (240, 240, 240))  # light grey
    h, w = out.shape[:2]
    m = h // 20
    corner = out[0:m, 0:m].reshape(-1, 3).mean(axis=0)
    assert np.abs(corner - 240).max() < 12
