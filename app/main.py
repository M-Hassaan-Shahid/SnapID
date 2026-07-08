"""SnapID — passport & CNIC photo maker.

FastAPI entry point: JSON API under /api, static web UI at the root.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="SnapID",
    description="Compliant passport, CNIC and visa photos — no photo shop needed.",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "snapid"}


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
