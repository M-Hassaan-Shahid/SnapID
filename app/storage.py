"""Ephemeral job storage — per-job directories that expire after 30 min.

Cleanup runs lazily on job creation; ids are uuid4 hex only, which also
blocks path traversal on the download route.
"""
import shutil
import time
import uuid
from pathlib import Path

TTL_MINUTES = 30

_BASE = Path(__file__).resolve().parent.parent / "data" / "jobs"


def _job_dir(job_id: str) -> Path:
    if not (len(job_id) == 32 and all(c in "0123456789abcdef" for c in job_id)):
        raise KeyError(job_id)
    return _BASE / job_id


def create_job() -> str:
    job_id = uuid.uuid4().hex
    _job_dir(job_id).mkdir(parents=True, exist_ok=True)
    return job_id


def job_path(job_id: str, filename: str) -> Path:
    directory = _job_dir(job_id)
    if not directory.is_dir():
        raise KeyError(f"Job {job_id} not found or expired.")
    return directory / Path(filename).name


def cleanup_expired(ttl_minutes: int = TTL_MINUTES) -> int:
    if not _BASE.is_dir():
        return 0
    cutoff = time.time() - ttl_minutes * 60
    removed = 0
    for entry in _BASE.iterdir():
        if entry.is_dir() and entry.stat().st_mtime < cutoff:
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
    return removed
