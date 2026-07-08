"""Automated compliance checks on the final composed photo.

Re-detects the face on the *output* image (not the source), so the
checks validate what the user actually downloads.
"""
from dataclasses import dataclass

import numpy as np

from app.core import face as face_mod
from app.core.specs import PhotoSpec


@dataclass
class Check:
    id: str
    label: str
    passed: bool
    detail: str


@dataclass
class ComplianceReport:
    checks: list[Check]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "checks": [
                {"id": c.id, "label": c.label, "passed": c.passed, "detail": c.detail}
                for c in self.checks
            ],
        }


def _background_uniformity(image_bgr: np.ndarray, expected_rgb) -> Check:
    """Sample the top corners — always background in a compliant ID photo."""
    h, w = image_bgr.shape[:2]
    m = max(4, h // 20)
    patches = np.concatenate(
        [
            image_bgr[0:m, 0:m].reshape(-1, 3),
            image_bgr[0:m, w - m : w].reshape(-1, 3),
        ]
    ).astype(np.float32)
    std = float(patches.std(axis=0).mean())
    expected_bgr = np.array(expected_rgb[::-1], dtype=np.float32)
    dist = float(np.abs(patches.mean(axis=0) - expected_bgr).mean())
    ok = std < 12.0 and dist < 25.0
    return Check(
        id="background",
        label="Background is uniform and the required color",
        passed=ok,
        detail=f"variation {std:.1f} (limit 12), color offset {dist:.1f} (limit 25)",
    )


def check_photo(image_bgr: np.ndarray, spec: PhotoSpec) -> ComplianceReport:
    h, w = image_bgr.shape[:2]
    checks: list[Check] = []

    try:
        f = face_mod.detect_face(image_bgr)
    except face_mod.MultipleFacesError as exc:
        checks.append(Check("face", "Exactly one face", False, str(exc)))
        return ComplianceReport(checks)
    except face_mod.NoFaceError as exc:
        checks.append(Check("face", "Exactly one face", False, str(exc)))
        return ComplianceReport(checks)

    checks.append(
        Check("face", "Exactly one face detected", True, f"confidence {f.confidence:.2f}")
    )

    head_ratio = f.head_height / h
    checks.append(
        Check(
            "head_size",
            f"Head height {spec.head_min:.0%}–{spec.head_max:.0%} of photo",
            spec.head_min <= head_ratio <= spec.head_max,
            f"measured {head_ratio:.0%}",
        )
    )

    eye_pos = f.eye_center[1] / h
    checks.append(
        Check(
            "eye_line",
            "Eye line in the required band",
            spec.eye_from_top_min <= eye_pos <= spec.eye_from_top_max,
            f"eyes at {eye_pos:.0%} from top "
            f"(required {spec.eye_from_top_min:.0%}–{spec.eye_from_top_max:.0%})",
        )
    )

    offset = abs(f.center_x - w / 2) / w
    checks.append(
        Check(
            "centering",
            "Face horizontally centered",
            offset <= 0.05,
            f"offset {offset:.1%} of width (limit 5%)",
        )
    )

    checks.append(_background_uniformity(image_bgr, spec.background_rgb))

    target_w, target_h = spec.pixel_size()
    checks.append(
        Check(
            "resolution",
            f"Print resolution {target_w}×{target_h}px (300 DPI)",
            (w, h) == (target_w, target_h),
            f"actual {w}×{h}px",
        )
    )

    return ComplianceReport(checks)
