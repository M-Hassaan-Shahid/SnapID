# SnapID — Passport & CNIC Photo Maker

**Compliant passport, CNIC, and visa photos — no trip to the photo shop.**

Upload a selfie, pick a document type, and get a correctly sized, correctly
composed photo with the right background color — plus a print-ready sheet for
standard photo paper. Every preset is checked by an automated compliance report
before you download.

## Features

- **Auto face detection & crop** — OpenCV YuNet landmarks position the head at
  the exact ratio each document requires
- **Background replacement** — AI person segmentation (rembg), composited onto
  the required background color
- **Compliance report** — head-height ratio, eye-line position, horizontal
  centering, background uniformity, and resolution are all verified and shown
  as a checklist before download
- **Print sheets** — 4×6 inch or A4 layouts at 300 DPI with cut guides
- **No accounts** — ephemeral jobs, files auto-delete after 30 minutes

## Supported Presets

| Preset               | Size      | Background | Head height |
|----------------------|-----------|------------|-------------|
| Pakistan CNIC/NICOP  | 35×45 mm  | White      | 70–80%      |
| Pakistan Passport    | 35×45 mm  | White      | 70–80%      |
| US Visa / Passport   | 51×51 mm  | White      | 50–69%      |
| Schengen Visa        | 35×45 mm  | White      | 70–80%      |
| UK Visa / Passport   | 35×45 mm  | Light grey | 64–75%      |

Specs follow the published official guidelines (DGIP/NADRA, US DoS, EU, HM
Passport Office). **Always cross-check with the issuing authority before
submitting** — requirements change.

## Stack

FastAPI · OpenCV (YuNet face detection) · rembg (person segmentation) ·
Pillow (compositing & print sheets) · static HTML/CSS/JS frontend.

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload   # dev server on :8000
pytest                          # test suite
```

The first background-replacement call downloads the u2net model (~170 MB) to
`~/.u2net/`.

## Project Layout

```
app/
  main.py            FastAPI entry point
  api/routes.py      REST endpoints
  core/
    specs.py         Document presets (sizes, ratios, colors)
    face.py          YuNet face detection + landmarks
    crop.py          Crop-to-spec geometry
    background.py    Person segmentation + background color swap
    compliance.py    Automated checks
    sheet.py         Print-sheet generator (4x6 / A4)
  models/            YuNet ONNX model (Apache-2.0, from opencv_zoo)
static/              Web UI
tests/               pytest suite (fixture: public-domain NASA portrait)
```
