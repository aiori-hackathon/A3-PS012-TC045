"""Stability: do repeated runs agree? A server whose label changes between runs is flagged.

A reason code that varies while the label stays the same (for example a rate-limited server, where it depends on which
query gets the one allowed packet) is reported as a note, not as instability.
"""
from __future__ import annotations

from pathlib import Path

from resolverlens.classify import classify_run


def stability(run_dirs, targets_file=None) -> dict:
    runs = []
    for d in run_dirs:
        d = Path(d)
        verdicts = classify_run(d, targets_file)
        runs.append({"run": d.name, "verdicts": {v.target_id: (v.label, v.reason) for v in verdicts}})
    ids = sorted({t for r in runs for t in r["verdicts"]})
    rows = []
    for t in ids:
        vals = [r["verdicts"].get(t) for r in runs]
        labels = {v[0] if v else None for v in vals}
        stable = len(labels) == 1 and None not in labels
        rows.append({"target_id": t, "values": vals, "stable": stable,
                     "reason_varies": stable and len({v[1] for v in vals}) > 1})
    return {"runs": [r["run"] for r in runs], "rows": rows,
            "unstable": [r["target_id"] for r in rows if not r["stable"]],
            "reason_varies": [r["target_id"] for r in rows if r["reason_varies"]],
            "stable": all(r["stable"] for r in rows)}
