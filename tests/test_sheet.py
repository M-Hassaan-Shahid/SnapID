import numpy as np
import pytest

from app.core.sheet import PAPERS, make_sheet


@pytest.fixture
def photo():
    return np.full((531, 413, 3), 180, dtype=np.uint8)  # CNIC-sized


def test_4x6_sheet(photo):
    result = make_sheet(photo, 35, 45, paper="4x6")
    assert result.copies == 8  # standard 8-up: 4 cols x 2 rows on 6x4in
    assert result.image.size[0] > result.image.size[1]  # landscape


def test_a4_sheet(photo):
    result = make_sheet(photo, 35, 45, paper="a4")
    assert result.copies >= 20


def test_unknown_paper(photo):
    with pytest.raises(ValueError):
        make_sheet(photo, 35, 45, paper="letter")


def test_oversized_photo_rejected():
    huge = np.full((100, 100, 3), 0, dtype=np.uint8)
    with pytest.raises(ValueError):
        make_sheet(huge, 300, 300, paper="4x6")


def test_all_papers_defined():
    assert set(PAPERS) == {"4x6", "a4"}
