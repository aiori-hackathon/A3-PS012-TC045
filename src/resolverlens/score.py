"""Scoring: confusion matrix, per-class metrics, coverage, compliance figures, and a root cause for every false result."""
from __future__ import annotations

import bisect
from datetime import datetime

from resolverlens.classify import AUTHORITATIVE_ONLY, INCONCLUSIVE, LABELS, RECURSIVE, REFUSED


def confusion(rows) -> dict:
    m = {e: {r: 0 for r in LABELS} for e in LABELS}
    for r in rows:
        m[r["expected"]][r["label"]] += 1
    return m


def per_class(m) -> dict:
    out = {}
    for c in LABELS:
        tp = m[c][c]
        fp = sum(m[e][c] for e in LABELS if e != c)
        fn = sum(m[c][r] for r in LABELS if r != c)
        p = tp / (tp + fp) if tp + fp else None
        rc = tp / (tp + fn) if tp + fn else None
        f1 = None if p is None or rc is None else (0.0 if p + rc == 0 else 2 * p * rc / (p + rc))
        out[c] = {"support": tp + fn, "reported": tp + fp, "tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": rc, "f1": f1}
    return out


def summary(rows) -> dict:
    total = len(rows)
    correct = sum(1 for r in rows if r["match"])
    decided = [r for r in rows if r["label"] != INCONCLUSIVE]
    dec_ok = sum(1 for r in decided if r["match"])
    return {
        "total": total, "correct": correct, "accuracy": correct / total if total else None,
        "decided": len(decided), "decided_correct": dec_ok,
        "accuracy_decided": dec_ok / len(decided) if decided else None,
        "coverage": len(decided) / total if total else None,
        "wrong_decisions": len(decided) - dec_ok,
        "false_exposure": sum(1 for r in rows if r["label"] == RECURSIVE and r["expected"] != RECURSIVE),
        "missed_exposure": sum(1 for r in rows if r["expected"] == RECURSIVE and r["label"] != RECURSIVE),
        "abstained_correctly": sum(1 for r in rows if r["expected"] == INCONCLUSIVE and r["label"] == INCONCLUSIVE),
        "abstained_wrongly": sum(1 for r in rows if r["label"] == INCONCLUSIVE and r["expected"] != INCONCLUSIVE),
    }


REASON_MEANING = {
    "TIMEOUT": ("packet loss, rate limiting or filtering", "No reply to any canary attempt. A silent drop looks the same as packet loss, so the tool does not guess."),
    "SERVFAIL": ("upstream failure", "The server answered but could not complete the lookup, for example its upstream was unreachable."),
    "TC_FAIL": ("truncated reply, TCP failed", "The reply was truncated and the retry over TCP did not complete."),
    "CONFLICT": ("mixed evidence", "The attempts disagreed or the flags, answer and canary log contradicted each other (caching, a forwarder chain or loss)."),
    "ERROR": ("local network error", "The probe host could not send the queries."),
    "NO_DATA": ("incomplete run", "Evidence is missing, for example the run was stopped early."),
}

_DECIDED_PAIRS = {
    (RECURSIVE, REFUSED): ("ACL", "The server refused our external vantage although it is meant to recurse: an access rule is blocking the probe client."),
    (RECURSIVE, AUTHORITATIVE_ONLY): ("recursion not observed", "The server answered its own zone but did not recurse: recursion is off or its upstream is unreachable."),
    (REFUSED, RECURSIVE): ("ACL", "The server recursed for the external client although it is meant to refuse: the access rule is not enforced."),
    (REFUSED, AUTHORITATIVE_ONLY): ("ACL", "The server answered the baseline query for our client: its query ACL is looser than seeded."),
    (AUTHORITATIVE_ONLY, RECURSIVE): ("recursion enabled", "The server recursed although it is meant to be authoritative-only."),
    (AUTHORITATIVE_ONLY, REFUSED): ("ACL", "The server refused every query, including its own zone: the baseline is blocked for our client."),
}


def root_cause(row, verdict) -> dict | None:
    """Explain a false result. Returns None for a correct verdict."""
    if row["match"]:
        return None
    exp, got = row["expected"], row["label"]
    if exp == INCONCLUSIVE:
        return {"category": "impairment not effective",
                "explanation": f"The server was seeded to be unusable (slow, limited, silent or broken) but gave a decisive answer ({got}). "
                               "Check the lab impairment or the seeded label."}
    if got == INCONCLUSIVE:
        cat, text = REASON_MEANING.get(verdict.reason, ("unclassified", "See the evidence card."))
        return {"category": cat, "explanation": f"The tool abstained ({verdict.reason}). {text}"}
    cat, text = _DECIDED_PAIRS.get((exp, got), ("unclassified", "See the evidence card."))
    return {"category": cat, "explanation": text}


def inconclusive_table(verdicts, expected: dict, behaviors: dict | None = None) -> list[dict]:
    rows = []
    for v in verdicts:
        if v.label != INCONCLUSIVE:
            continue
        cat, text = REASON_MEANING.get(v.reason, ("unclassified", ""))
        rows.append({"target_id": v.target_id, "software": v.software, "reason": v.reason, "likely_cause": cat,
                     "meaning": text, "expected_inconclusive": expected.get(v.target_id) == INCONCLUSIVE,
                     "seeded": (behaviors or {}).get(v.target_id, "-").replace("_", " "),
                     "late_hits": v.late_hits})
    return rows


def _max_window(ts) -> int:
    ts = sorted(ts)
    return max((bisect.bisect_left(ts, t + 1.0) - i for i, t in enumerate(ts)), default=0)


def compliance(evidence, manifest) -> dict:
    """Figures computed from the evidence that show the run stayed bounded and inside the lab."""
    stamps = [(r["target_id"], datetime.fromisoformat(r["ts"]).timestamp()) for r in evidence]
    by: dict[str, list] = {}
    for tid, t in stamps:
        by.setdefault(tid, []).append(t)
    ratios = [r["reply_bytes"] / r["query_bytes"] for r in evidence if r.get("reply_bytes") and r.get("query_bytes")]
    cfg = manifest.get("config", {})
    allowed = {t["ip"] for t in manifest.get("targets", [])}
    return {
        "probes": len(evidence),
        "destinations": len({r["target_ip"] for r in evidence}),
        "all_destinations_on_allowlist": {r["target_ip"] for r in evidence} <= allowed,
        "query_types": sorted({r["qtype"] for r in evidence}),
        "max_queries_per_second_all_targets": _max_window([t for _, t in stamps]),
        "max_queries_per_second_one_target": max((_max_window(v) for v in by.values()), default=0),
        "max_reply_bytes": max((r["reply_bytes"] for r in evidence if r.get("reply_bytes")), default=0),
        "max_reply_to_query_ratio": round(max(ratios), 2) if ratios else 0.0,
        "limits": {"global_rate": cfg.get("rate", {}).get("global", {}).get("rate"),
                   "per_target_rate": cfg.get("rate", {}).get("per_target", {}).get("rate"),
                   "max_reply_bytes": cfg.get("safety", {}).get("max_reply_bytes"),
                   "max_ratio": cfg.get("safety", {}).get("max_ratio")},
        "stop_reason": manifest.get("stop_reason"),
    }


REMEDIATION = {
    "bind": "allow-recursion { <your clients>; localhost; };  allow-query-cache { <your clients>; localhost; };",
    "unbound": "access-control: 0.0.0.0/0 refuse   then   access-control: <your clients> allow",
    "dnsmasq": "local-service   (or  interface=<internal interface>  with  bind-interfaces)",
    "nsd": "NSD does not recurse; no change is needed.",
}
