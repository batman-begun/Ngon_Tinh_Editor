import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from omni_novel_editor.config import JOBS_DIR


def create_job_dir(original_name: str) -> Path:
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in original_name).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir = JOBS_DIR / f"{timestamp}_{safe_name}_{uuid4().hex[:8]}"
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")
