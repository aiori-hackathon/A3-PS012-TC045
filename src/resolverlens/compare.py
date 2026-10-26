"""Compares verdicts with the expected labels. This is the only module that reads the expected labels."""
from __future__ import annotations

from pathlib import Path

import yaml


def expected_labels(targets_file) -> dict:
    data = yaml.safe_load(Path(targets_file).read_text())
    return {t["id"]: t["expected"] for t in data["targets"]}


def behaviors(targets_file) -> dict:
    data = yaml.safe_load(Path(targets_file).read_text())
    return {t["id"]: t["behavior"] for t in data["targets"]}


def compare(verdicts, expected: dict) -> list[dict]:
    rows = []
    for v in verdicts:
        exp = expected.get(v.target_id)
        rows.append({"target_id": v.target_id, "software": v.software, "expected": exp, "label": v.label,
                     "reason": v.reason, "rule": v.rule, "match": exp == v.label})
    return rows
