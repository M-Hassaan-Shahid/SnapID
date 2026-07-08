import numpy as np
import pytest

from app.core.background import replace_background
from app.core.compliance import check_photo
from app.core.crop import crop_to_spec
from app.core.face import detect_face
from app.core.specs import get_spec


@pytest.fixture(scope="module")
def finished_photo(portrait_bgr_module):
    """Full pipeline output: background swap → crop to CNIC spec."""
    spec = get_spec("pk_cnic")
    clean = replace_background(portrait_bgr_module, spec.background_rgb)
    face = detect_face(clean)
    return crop_to_spec(clean, face, spec).image


@pytest.fixture(scope="module")
def portrait_bgr_module():
    from pathlib import Path

    import cv2

    img = cv2.imread(str(Path(__file__).parent / "fixtures" / "portrait.png"))
    assert img is not None
    return img


def test_pipeline_output_passes_compliance(finished_photo):
    report = check_photo(finished_photo, get_spec("pk_cnic"))
    failed = [c for c in report.checks if not c.passed]
    assert report.passed, f"failed checks: {[(c.id, c.detail) for c in failed]}"


def test_raw_photo_fails_compliance(portrait_bgr_module):
    """The unprocessed source (wrong size, busy background) must fail."""
    report = check_photo(portrait_bgr_module, get_spec("pk_cnic"))
    assert not report.passed


def test_blank_image_fails():
    blank = np.full((531, 413, 3), 255, dtype=np.uint8)
    report = check_photo(blank, get_spec("pk_cnic"))
    assert not report.passed
    assert report.checks[0].id == "face"
    assert not report.checks[0].passed


def test_report_serializes(finished_photo):
    report = check_photo(finished_photo, get_spec("pk_cnic"))
    d = report.as_dict()
    assert isinstance(d["passed"], bool)
    assert {c["id"] for c in d["checks"]} >= {"face", "head_size", "background"}
