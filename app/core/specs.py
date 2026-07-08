"""Document photo presets.

Sizes, head-height ratios, eye-line positions, and background colors per
the published official guidelines:

- Pakistan CNIC/NICOP & Passport: 35x45 mm, white background, head
  70-80% of photo height (NADRA / DGIP photo requirements).
- US visa & passport: 2x2 in, white, head 50-69% of photo height, eye
  line 56-69% from the bottom (travel.state.gov composition template).
- Schengen visa: 35x45 mm, face 70-80%, plain light background (ICAO).
- UK passport/visa: 35x45 mm, crown-to-chin 29-34 mm of the 45 mm
  height, plain light-grey or cream background (HM Passport Office).

Requirements change — the UI tells users to cross-check with the
issuing authority.
"""
from dataclasses import dataclass

PRINT_DPI = 300
_MM_PER_INCH = 25.4


@dataclass(frozen=True)
class PhotoSpec:
    id: str
    name: str
    width_mm: float
    height_mm: float
    # Acceptable crown-to-chin head height as a fraction of photo height.
    head_min: float
    head_max: float
    # Eye line measured from the TOP of the photo, as a fraction of height.
    eye_from_top_min: float
    eye_from_top_max: float
    background_rgb: tuple[int, int, int]
    notes: str

    @property
    def head_target(self) -> float:
        return (self.head_min + self.head_max) / 2

    @property
    def eye_from_top_target(self) -> float:
        return (self.eye_from_top_min + self.eye_from_top_max) / 2

    def pixel_size(self, dpi: int = PRINT_DPI) -> tuple[int, int]:
        return (
            round(self.width_mm / _MM_PER_INCH * dpi),
            round(self.height_mm / _MM_PER_INCH * dpi),
        )


SPECS: dict[str, PhotoSpec] = {
    spec.id: spec
    for spec in [
        PhotoSpec(
            id="pk_cnic",
            name="Pakistan CNIC / NICOP",
            width_mm=35, height_mm=45,
            head_min=0.70, head_max=0.80,
            eye_from_top_min=0.35, eye_from_top_max=0.48,
            background_rgb=(255, 255, 255),
            notes="NADRA: plain white background, neutral expression, no headwear "
                  "except religious.",
        ),
        PhotoSpec(
            id="pk_passport",
            name="Pakistan Passport",
            width_mm=35, height_mm=45,
            head_min=0.70, head_max=0.80,
            eye_from_top_min=0.35, eye_from_top_max=0.48,
            background_rgb=(255, 255, 255),
            notes="DGIP: white background, face and top of shoulders visible.",
        ),
        PhotoSpec(
            id="us_visa",
            name="US Visa / Passport (2x2 in)",
            width_mm=50.8, height_mm=50.8,
            head_min=0.50, head_max=0.69,
            eye_from_top_min=0.31, eye_from_top_max=0.44,
            background_rgb=(255, 255, 255),
            notes="US DoS: head 1 to 1-3/8 in, eye line 1-1/8 to 1-3/8 in from "
                  "the bottom.",
        ),
        PhotoSpec(
            id="schengen_visa",
            name="Schengen Visa",
            width_mm=35, height_mm=45,
            head_min=0.70, head_max=0.80,
            eye_from_top_min=0.35, eye_from_top_max=0.48,
            background_rgb=(255, 255, 255),
            notes="ICAO composition; plain light background required.",
        ),
        PhotoSpec(
            id="uk_passport",
            name="UK Passport / Visa",
            width_mm=35, height_mm=45,
            head_min=0.64, head_max=0.76,       # 29-34 mm of 45 mm
            eye_from_top_min=0.35, eye_from_top_max=0.50,
            background_rgb=(240, 240, 240),
            notes="HMPO: crown-to-chin 29-34 mm, plain light-grey or cream "
                  "background.",
        ),
    ]
}


def get_spec(spec_id: str) -> PhotoSpec:
    try:
        return SPECS[spec_id]
    except KeyError:
        raise ValueError(f"Unknown spec '{spec_id}'.")
