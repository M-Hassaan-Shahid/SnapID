"""Print-sheet generator.

Lays out multiple copies of the finished photo on standard photo paper
with thin cut guides, at 300 DPI.
"""
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from app.core.specs import PRINT_DPI

_MM_PER_INCH = 25.4

PAPERS = {
    "4x6": (152.4, 101.6),   # landscape 6x4 in — the default photo-shop paper
    "a4": (210.0, 297.0),
}

GAP_MM = 2.0
# Near-borderless margins: 2 mm fits the standard 8-up layout of 35x45 mm
# photos on 4x6 paper, matching what photo shops actually print.
MARGIN_MM = 2.0


@dataclass
class SheetResult:
    image: Image.Image
    copies: int
    paper: str


def _mm_to_px(mm: float, dpi: int = PRINT_DPI) -> int:
    return round(mm / _MM_PER_INCH * dpi)


def make_sheet(
    photo_bgr: np.ndarray,
    photo_width_mm: float,
    photo_height_mm: float,
    paper: str = "4x6",
) -> SheetResult:
    if paper not in PAPERS:
        raise ValueError(f"Unknown paper '{paper}'. Choose from {sorted(PAPERS)}.")
    paper_w_mm, paper_h_mm = PAPERS[paper]

    sheet_w, sheet_h = _mm_to_px(paper_w_mm), _mm_to_px(paper_h_mm)
    photo_w, photo_h = _mm_to_px(photo_width_mm), _mm_to_px(photo_height_mm)
    gap, margin = _mm_to_px(GAP_MM), _mm_to_px(MARGIN_MM)

    cols = (sheet_w - 2 * margin + gap) // (photo_w + gap)
    rows = (sheet_h - 2 * margin + gap) // (photo_h + gap)
    if cols < 1 or rows < 1:
        raise ValueError("Photo does not fit on the selected paper.")

    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    photo = Image.fromarray(photo_bgr[:, :, ::-1])  # BGR → RGB
    photo = photo.resize((photo_w, photo_h), Image.LANCZOS)

    # Center the grid on the sheet.
    grid_w = cols * photo_w + (cols - 1) * gap
    grid_h = rows * photo_h + (rows - 1) * gap
    x_start = (sheet_w - grid_w) // 2
    y_start = (sheet_h - grid_h) // 2

    for r in range(rows):
        for c in range(cols):
            x = x_start + c * (photo_w + gap)
            y = y_start + r * (photo_h + gap)
            sheet.paste(photo, (x, y))
            draw.rectangle(
                [x - 1, y - 1, x + photo_w, y + photo_h],
                outline=(190, 190, 190),
                width=1,
            )

    return SheetResult(image=sheet, copies=int(cols * rows), paper=paper)
