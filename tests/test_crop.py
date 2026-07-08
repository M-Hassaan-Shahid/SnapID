import pytest

from app.core.crop import CropOutOfBoundsError, crop_to_spec
from app.core.face import detect_face
from app.core.specs import SPECS, get_spec


def test_crop_exact_pixel_size(portrait_bgr):
    face = detect_face(portrait_bgr)
    spec = get_spec("pk_cnic")
    result = crop_to_spec(portrait_bgr, face, spec)
    w, h = spec.pixel_size()
    assert result.image.shape[:2] == (h, w)


@pytest.mark.parametrize("spec_id", list(SPECS))
def test_crop_head_ratio_hits_target(portrait_bgr, spec_id):
    """After cropping, the re-detected head must sit inside the spec band."""
    spec = get_spec(spec_id)
    face = detect_face(portrait_bgr)
    result = crop_to_spec(portrait_bgr, face, spec)

    out_face = detect_face(result.image)
    out_h = result.image.shape[0]
    head_ratio = out_face.head_height / out_h
    # Allow a small detector-variance margin around the spec band.
    assert spec.head_min - 0.06 <= head_ratio <= spec.head_max + 0.06, (
        f"{spec_id}: head ratio {head_ratio:.2f} outside "
        f"[{spec.head_min}, {spec.head_max}]"
    )


def test_crop_eye_line(portrait_bgr):
    spec = get_spec("pk_cnic")
    face = detect_face(portrait_bgr)
    result = crop_to_spec(portrait_bgr, face, spec)
    out_face = detect_face(result.image)
    eye_pos = out_face.eye_center[1] / result.image.shape[0]
    assert spec.eye_from_top_min - 0.05 <= eye_pos <= spec.eye_from_top_max + 0.05


def test_tight_source_pads_and_still_complies(portrait_bgr):
    """A face-box-tight source needs border padding; result must still hit spec size."""
    face = detect_face(portrait_bgr)
    x, y, w, h = [int(v) for v in face.box]
    tight = portrait_bgr[max(0, y) : y + h, max(0, x) : x + w]
    tight_face = detect_face(tight)
    spec = get_spec("pk_cnic")

    # Padding disabled → the impossible framing must raise, not distort.
    with pytest.raises(CropOutOfBoundsError):
        crop_to_spec(tight, tight_face, spec, allow_padding=False)

    # Padding enabled → exact spec size comes back.
    result = crop_to_spec(tight, tight_face, spec, allow_padding=True)
    w_px, h_px = spec.pixel_size()
    assert result.image.shape[:2] == (h_px, w_px)
