from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"


def _portrait_upload():
    return ("file", ("portrait.png", (FIXTURES / "portrait.png").read_bytes(), "image/png"))


def test_list_specs():
    resp = client.get("/api/specs")
    assert resp.status_code == 200
    ids = {s["id"] for s in resp.json()}
    assert {"pk_cnic", "pk_passport", "us_visa"} <= ids


def test_process_full_pipeline():
    resp = client.post(
        "/api/process",
        files=[_portrait_upload()],
        data={"spec_id": "pk_cnic", "paper": "4x6"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["compliance"]["passed"] is True
    assert body["sheet_copies"] >= 6

    photo = client.get(body["photo_url"])
    assert photo.status_code == 200
    assert photo.content[:8] == b"\x89PNG\r\n\x1a\n"

    sheet = client.get(body["sheet_url"])
    assert sheet.status_code == 200
    assert sheet.content[:5] == b"%PDF-"


def test_process_unknown_spec():
    resp = client.post(
        "/api/process", files=[_portrait_upload()], data={"spec_id": "nope"}
    )
    assert resp.status_code == 400


def test_process_no_face():
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (600, 600), "gray").save(buf, format="PNG")
    resp = client.post(
        "/api/process",
        files=[("file", ("gray.png", buf.getvalue(), "image/png"))],
        data={"spec_id": "pk_cnic"},
    )
    assert resp.status_code == 422
    assert "face" in resp.json()["detail"].lower()


def test_process_garbage_bytes():
    resp = client.post(
        "/api/process",
        files=[("file", ("x.png", b"not an image at all", "image/png"))],
        data={"spec_id": "pk_cnic"},
    )
    assert resp.status_code == 400


def test_download_expired():
    resp = client.get("/api/download/deadbeefdeadbeefdeadbeefdeadbeef/photo.png")
    assert resp.status_code == 404
