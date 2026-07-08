"""REST endpoints: one-shot photo processing plus spec listing."""
import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app import storage
from app.core import face as face_mod
from app.core.background import replace_background
from app.core.compliance import check_photo
from app.core.crop import CropOutOfBoundsError, crop_to_spec
from app.core.sheet import make_sheet
from app.core.specs import SPECS, get_spec

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@router.get("/specs")
def list_specs() -> list[dict]:
    return [
        {
            "id": s.id,
            "name": s.name,
            "size_mm": [s.width_mm, s.height_mm],
            "background_rgb": list(s.background_rgb),
            "notes": s.notes,
        }
        for s in SPECS.values()
    ]


@router.post("/process")
async def process(
    file: UploadFile = File(...),
    spec_id: str = Form(...),
    paper: str = Form("4x6"),
):
    storage.cleanup_expired()
    try:
        spec = get_spec(spec_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File exceeds the 25 MB limit.")

    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(400, "Could not read the image — use a JPG or PNG photo.")

    # Pipeline: background first (segmentation works best on the full
    # frame), then face-detect on the clean image, then crop to spec.
    clean = replace_background(image, spec.background_rgb)
    try:
        detected = face_mod.detect_face(clean)
    except (face_mod.NoFaceError, face_mod.MultipleFacesError) as exc:
        raise HTTPException(422, str(exc))
    try:
        result = crop_to_spec(clean, detected, spec)
    except CropOutOfBoundsError as exc:
        raise HTTPException(422, str(exc))

    report = check_photo(result.image, spec)

    job_id = storage.create_job()
    photo_path = storage.job_path(job_id, "photo.png")
    cv2.imwrite(str(photo_path), result.image)

    sheet = make_sheet(result.image, spec.width_mm, spec.height_mm, paper=paper)
    sheet_path = storage.job_path(job_id, "print_sheet.pdf")
    sheet.image.save(sheet_path, format="PDF", resolution=300)

    return {
        "job_id": job_id,
        "photo_url": f"/api/download/{job_id}/photo.png",
        "sheet_url": f"/api/download/{job_id}/print_sheet.pdf",
        "sheet_copies": sheet.copies,
        "spec": {"id": spec.id, "name": spec.name, "notes": spec.notes},
        "compliance": report.as_dict(),
    }


@router.get("/download/{job_id}/{filename}")
def download(job_id: str, filename: str):
    try:
        path = storage.job_path(job_id, filename)
    except KeyError:
        raise HTTPException(404, "This download has expired.")
    if not path.is_file():
        raise HTTPException(404, "This download has expired.")
    return FileResponse(path, filename=filename)
