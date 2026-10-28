"""Single-flag baselines, judged on the same evidence, to show what the canary log adds.

The question is binary: does the server provide recursion to the external client?
"""
from __future__ import annotations

from resolverlens.classify import RECURSIVE

METHODS = [
    ("resolverlens", "ResolverLens", "flags, answer and canary evidence over 3 attempts"),
    ("flag_ra", "RA-flag check", "first RD=1 reply: NOERROR and RA set (what Nmap's dns-recursion script reads)"),
    ("flag_ra_aa", "RA + AA check", "first RD=1 reply: NOERROR, RA set, AA clear and an answer"),
]


def first_canary(records):
    return next((r for r in sorted(records, key=lambda r: r["attempt"]) if r["phase"] == "canary"), None)


def flag_ra(rec) -> bool:
    return bool(rec) and rec["status"] == "NOERROR" and bool(rec["flags"].get("ra"))


def flag_ra_aa(rec) -> bool:
    return flag_ra(rec) and not rec["flags"].get("aa") and bool(rec["answers"])


def evaluate(verdicts, evidence_by_target: dict, expected: dict, behaviors: dict | None = None) -> dict:
    stats = {k: {"key": k, "name": n, "rule": d, "correct": 0, "false_exposure": 0, "missed_exposure": 0, "wrong": []}
             for k, n, d in METHODS}
    rows = []
    for v in verdicts:
        truth = expected.get(v.target_id) == RECURSIVE
        first = first_canary(evidence_by_target.get(v.target_id, []))
        calls = {"resolverlens": v.label == RECURSIVE, "flag_ra": flag_ra(first), "flag_ra_aa": flag_ra_aa(first)}
        for k, called in calls.items():
            s = stats[k]
            if called == truth:
                s["correct"] += 1
            else:
                s["wrong"].append(v.target_id)
                s["false_exposure" if called else "missed_exposure"] += 1
        rows.append({"target_id": v.target_id, "seeded": (behaviors or {}).get(v.target_id, "-").replace("_", " "),
                     "truth": truth, **calls, "differs": len(set(calls.values())) > 1 or any(c != truth for c in calls.values())})
    total = len(verdicts)
    return {"total": total, "methods": [dict(s, total=total) for s in stats.values()],
            "rows": rows, "differences": [r for r in rows if r["differs"]]}
