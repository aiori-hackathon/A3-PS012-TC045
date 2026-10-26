"""Classifier: one verdict per target, computed from evidence.jsonl alone (so a replay gives the same result).

Rules are checked in order and the first match decides the class:
  1 Recursive          every canary attempt: NOERROR, RA set, marker answer, and the canary log shows the name
  2 Refused            baseline and every canary attempt are REFUSED
  3 Authoritative-only baseline answered with AA and an answer; every canary attempt got a reply with no answer,
                       no RA and no canary hit
  4 Inconclusive       anything else, with a reason code
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from resolverlens.evidence import read_evidence

RECURSIVE, REFUSED, AUTHORITATIVE_ONLY, INCONCLUSIVE = "recursive", "refused", "authoritative_only", "inconclusive"
LABELS = (RECURSIVE, AUTHORITATIVE_ONLY, REFUSED, INCONCLUSIVE)
REASONS = ("TIMEOUT", "SERVFAIL", "TC_FAIL", "CONFLICT", "ERROR", "NO_DATA")
NO_REPLY = ("TIMEOUT", "ERROR", "TC_FAIL")


@dataclass
class Verdict:
    target_id: str
    ip: str
    software: str
    label: str
    reason: str | None
    rule: str
    attempts: list = field(default_factory=list)       # status of each canary attempt
    canary_hits: int = 0
    canary_sources: list = field(default_factory=list)
    late_hits: int = 0                                   # canary lookups whose reply never reached us
    detail: str = ""
    evidence_seqs: list = field(default_factory=list)


def _replied(r) -> bool:
    return r["status"] not in NO_REPLY


def _recursion_proof(r, marker) -> bool:
    return r["status"] == "NOERROR" and bool(r["flags"].get("ra")) and marker in r["answers"] and bool(r["canary_hit"])


def decide(base, canaries, marker, expected_attempts):
    """Return (label, reason, rule, detail) for one target."""
    if base is None or len(canaries) < expected_attempts:
        return INCONCLUSIVE, "NO_DATA", "R4", "evidence is missing (run stopped early?)"
    n = len(canaries)
    if all(_recursion_proof(c, marker) for c in canaries):
        return RECURSIVE, None, "R1", f"{n}/{n} canary attempts: NOERROR, RA, marker answer, canary log hit"
    if base["status"] == "REFUSED" and all(c["status"] == "REFUSED" and not c["canary_hit"] for c in canaries):
        return REFUSED, None, "R2", f"REFUSED for the baseline and {n}/{n} canary attempts"
    if (base["status"] == "NOERROR" and base["flags"].get("aa") and base["answers"] and
            all(_replied(c) and c["status"] in ("REFUSED", "NOERROR") and not c["answers"] and not c["canary_hit"]
                and not c["flags"].get("ra") for c in canaries)):
        return AUTHORITATIVE_ONLY, None, "R3", f"baseline answered with AA; {n}/{n} canary attempts got no answer and no canary hit"
    statuses = [c["status"] for c in canaries]
    if any(s == "TC_FAIL" for s in statuses):
        return INCONCLUSIVE, "TC_FAIL", "R4", "a truncated reply could not be completed over TCP"
    if not any(_replied(c) for c in canaries):
        reason = "ERROR" if "ERROR" in statuses else "TIMEOUT"
        return INCONCLUSIVE, reason, "R4", f"no reply to any of the {n} canary attempts"
    if all(s in ("SERVFAIL", "TIMEOUT") for s in statuses):
        reason = "SERVFAIL" if "SERVFAIL" in statuses else "TIMEOUT"
        return INCONCLUSIVE, reason, "R4", f"canary attempts ended in {sorted(set(statuses))}"
    return INCONCLUSIVE, "CONFLICT", "R4", f"the evidence does not agree: canary statuses {statuses}"


def classify_target(target, records, marker, expected_attempts) -> Verdict:
    base = next((r for r in records if r["phase"] == "baseline"), None)
    canaries = sorted((r for r in records if r["phase"] == "canary"), key=lambda r: r["attempt"])
    label, reason, rule, detail = decide(base, canaries, marker, expected_attempts)
    late = sum(1 for c in canaries if not _replied(c) and c["canary_hit"])
    if late:
        detail += f"; {late} canary lookup(s) happened but the reply never reached us"
    sources = sorted({s for c in canaries for s in c["canary_sources"]})
    return Verdict(target["id"], target["ip"], target["software"], label, reason, rule,
                   [c["status"] for c in canaries], sum(1 for c in canaries if c["canary_hit"]), sources, late, detail,
                   [r["seq"] for r in records])


def _marker_from_targets(path) -> str:
    return yaml.safe_load(Path(path).read_text())["lab"]["canary"]["marker_ip"]


def classify_run(run_dir, targets_file=None) -> list[Verdict]:
    """Classify every target of a run and write verdicts.csv and verdicts.jsonl into the run folder."""
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    marker = (manifest.get("canary") or {}).get("marker_ip") or _marker_from_targets(
        targets_file or manifest["config"]["targets_file"])
    attempts = manifest["config"]["probe"]["attempts"]
    by: dict[str, list] = {}
    for r in read_evidence(run_dir / "evidence.jsonl"):
        by.setdefault(r["target_id"], []).append(r)
    verdicts = [classify_target(t, by.get(t["id"], []), marker, attempts) for t in manifest["targets"]]
    write_verdicts(run_dir, verdicts)
    return verdicts


def write_verdicts(run_dir, verdicts) -> None:
    run_dir = Path(run_dir)
    with open(run_dir / "verdicts.jsonl", "w") as f:
        for v in verdicts:
            f.write(json.dumps(asdict(v), separators=(",", ":")) + "\n")
    cols = ["target_id", "ip", "software", "label", "reason", "rule", "attempts", "canary_hits", "canary_sources", "late_hits", "detail"]
    with open(run_dir / "verdicts.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for v in verdicts:
            d = asdict(v)
            w.writerow([";".join(d[c]) if isinstance(d[c], list) else ("" if d[c] is None else d[c]) for c in cols])
