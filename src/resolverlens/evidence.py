"""Evidence files: evidence.jsonl (one record per probe), audit.log and manifest.json."""
from __future__ import annotations

import json
import os
from pathlib import Path


class EvidenceWriter:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self._ev = open(self.run_dir / "evidence.jsonl", "a", buffering=1)
        self._audit = open(self.run_dir / "audit.log", "a", buffering=1)

    def record(self, rec: dict) -> None:
        self._ev.write(json.dumps(rec, separators=(",", ":")) + "\n")

    def audit(self, line: str) -> None:
        self._audit.write(line + "\n")

    def close(self) -> None:
        self._ev.close()
        self._audit.close()


def write_manifest(run_dir: Path, manifest: dict) -> None:
    tmp = Path(run_dir) / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, Path(run_dir) / "manifest.json")


def read_evidence(path: str | Path):
    with open(path) as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
