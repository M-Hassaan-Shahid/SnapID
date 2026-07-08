import pytest

from app.core.specs import SPECS, get_spec


def test_all_specs_have_sane_geometry():
    for spec in SPECS.values():
        assert 0 < spec.head_min < spec.head_max <= 1
        assert 0 < spec.eye_from_top_min < spec.eye_from_top_max < 1
        assert spec.width_mm > 0 and spec.height_mm > 0
        assert all(0 <= c <= 255 for c in spec.background_rgb)


def test_pk_cnic_matches_official_spec():
    spec = get_spec("pk_cnic")
    assert (spec.width_mm, spec.height_mm) == (35, 45)
    assert spec.background_rgb == (255, 255, 255)
    assert (spec.head_min, spec.head_max) == (0.70, 0.80)


def test_pixel_size_300dpi():
    w, h = get_spec("pk_cnic").pixel_size(300)
    assert (w, h) == (413, 531)  # 35mm, 45mm at 300 dpi


def test_us_visa_square():
    w, h = get_spec("us_visa").pixel_size(300)
    assert w == h == 600  # 2x2 inches


def test_unknown_spec():
    with pytest.raises(ValueError):
        get_spec("mars_visa")
