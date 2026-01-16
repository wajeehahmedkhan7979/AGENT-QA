from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from config import settings


@dataclass
class ArtifactRecord:
    name: str
    type: str
    path: str  # path relative to storage root, e.g. "job_123/dom.json"


class LocalFSStorageAdapter:
    """
    Minimal local filesystem storage adapter for demo purposes.

    This is intentionally simple so it can be replaced with an S3-backed
    implementation that respects the same contract.
    """

    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        path = self.root / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_bytes(self, job_id: str, filename: str, data: bytes) -> str:
        job_dir = self.job_dir(job_id)
        file_path = job_dir / filename
        file_path.write_bytes(data)
        rel_path = f"{job_id}/{filename}"
        return rel_path

    def save_json(self, job_id: str, filename: str, obj: object) -> str:
        serialized = json.dumps(obj, indent=2).encode("utf-8")
        return self.save_bytes(job_id, filename, serialized)

    def load_manifest(self, job_id: str) -> List[ArtifactRecord]:
        manifest_path = self.root / job_id / "manifest.json"
        if not manifest_path.exists():
            return []
        raw = manifest_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return [ArtifactRecord(**item) for item in data]

    def save_manifest(self, job_id: str, records: List[ArtifactRecord]) -> str:
        manifest_data = [asdict(r) for r in records]
        return self.save_json(job_id, "manifest.json", manifest_data)


storage_adapter = LocalFSStorageAdapter(settings.storage_root)

