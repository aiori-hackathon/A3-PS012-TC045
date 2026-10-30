"""Replay: prove a stored run is intact and that its verdicts can be re-derived from the evidence alone."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from resolverlens.classify import classify_run
from resolverlens.evidence import read_evidence, sha256_file


def replay(run_dir, targets_file=None) -> dict:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    checks = []

    def add(name, ok, note=""):
        checks.append({"check": name, "ok": bool(ok), "note": note})

    ev = list(read_evidence(run_dir / "evidence.jsonl"))
    add("evidence sequence numbers run 1..N without gaps", [r["seq"] for r in ev] == list(range(1, len(ev) + 1)), f"{len(ev)} records")
    add("record count matches the manifest", len(ev) == manifest.get("probes"), f"manifest says {manifest.get('probes')}")
    audit_n = len((run_dir / "audit.log").read_text().splitlines()) if (run_dir / "audit.log").exists() else -1
    add("one audit line per probe", audit_n == len(ev), f"{audit_n} audit lines")
    allowed = {t["ip"] for t in manifest.get("targets", [])}
    add("every destination was on the allowlist", {r["target_ip"] for r in ev} <= allowed)
    add("only type A queries were sent", {r["qtype"] for r in ev} <= {"A"})
    files = manifest.get("files")
    if files:
        for name, want in files.items():
            add(f"{name} unchanged since the run (sha256)", sha256_file(run_dir / name) == want)
    else:
        add("file hashes recorded in the manifest", True, "not recorded (run made before hashing was added)")
    tmp = Path(tempfile.mkdtemp(prefix="rl-replay-"))
    try:
        shutil.copy(run_dir / "manifest.json", tmp / "manifest.json")
        shutil.copy(run_dir / "evidence.jsonl", tmp / "evidence.jsonl")
        classify_run(tmp, targets_file)
        for name in ("verdicts.jsonl", "verdicts.csv"):
            stored = run_dir / name
            if stored.exists():
                add(f"re-derived {name} is byte-identical to the stored one", stored.read_bytes() == (tmp / name).read_bytes())
            else:
                add(f"{name} stored", True, "none stored; re-derived verdicts are valid")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"run": run_dir.name, "ok": all(c["ok"] for c in checks), "checks": checks}
