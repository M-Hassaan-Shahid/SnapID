from pathlib import Path

import cv2
import numpy as np
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def portrait_bgr() -> np.ndarray:
    """Public-domain NASA portrait (Eileen Collins, via scikit-image data)."""
    img = cv2.imread(str(FIXTURES / "portrait.png"))
    assert img is not None, "missing tests/fixtures/portrait.png"
    return img


@pytest.fixture(scope="session")
def blank_image() -> np.ndarray:
    return np.full((480, 640, 3), 200, dtype=np.uint8)
