"""Canary query names. They are unique per run, target and attempt, and repeatable from the seed."""
from __future__ import annotations

import hashlib


def canary_name(seed: int, run_id: str, target_id: str, attempt: int, zone: str) -> str:
    digest = hashlib.sha256(f"{seed}:{run_id}:{target_id}:{attempt}".encode()).hexdigest()[:10]
    return f"rl-{digest}.{zone}"
