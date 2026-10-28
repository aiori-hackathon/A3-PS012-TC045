import json
from pathlib import Path

import pytest

from resolverlens.classify import AUTHORITATIVE_ONLY, INCONCLUSIVE, RECURSIVE, REFUSED, classify_run, classify_target, decide
from resolverlens.cli import main

MARKER = "192.0.2.53"
T = {"id": "t01", "ip": "10.10.0.11", "software": "bind"}


def rec(phase, attempt, status, ra=False, aa=False, answers=(), hit=False, sources=(), seq=1):
    return {"seq": seq, "target_id": "t01", "phase": phase, "attempt": attempt, "status": status,
            "flags": ({"ra": ra, "aa": aa} if status not in ("TIMEOUT", "ERROR", "TC_FAIL") else {}),
            "answers": list(answers), "canary_hit": hit, "canary_sources": list(sources)}


def base(status="NOERROR", aa=False, answers=()):
    return rec("baseline", 0, status, aa=aa, answers=answers)


def good(k):
    return rec("canary", k, "NOERROR", ra=True, answers=[MARKER], hit=True, sources=["10.10.0.11"])


def refused(k):
    return rec("canary", k, "REFUSED")


def silent(k, hit=False):
    return rec("canary", k, "TIMEOUT", hit=hit)


def run(base_rec, canaries):
    return decide(base_rec, canaries, MARKER, 3)


def test_open_recursive_is_recursive_even_when_the_baseline_is_refused():
    assert run(base("REFUSED"), [good(1), good(2), good(3)])[:3] == (RECURSIVE, None, "R1")


def test_forwarder_is_recursive_whatever_address_asked_the_canary():
    c = [dict(good(k), canary_sources=["10.10.0.99"]) for k in (1, 2, 3)]
    assert run(base(), c)[0] == RECURSIVE


def test_policy_refusing_is_refused():
    assert run(base("REFUSED"), [refused(1), refused(2), refused(3)])[:3] == (REFUSED, None, "R2")


def test_authoritative_only():
    b = base("NOERROR", aa=True, answers=["10.10.0.20"])
    assert run(b, [refused(1), refused(2), refused(3)])[:3] == (AUTHORITATIVE_ONLY, None, "R3")


def test_authoritative_only_needs_an_answered_baseline():
    assert run(base("NOERROR", aa=True), [refused(1), refused(2), refused(3)])[0] == INCONCLUSIVE


def test_authoritative_only_never_applies_if_ra_is_set():
    c = [rec("canary", k, "NOERROR", ra=True) for k in (1, 2, 3)]
    assert run(base("NOERROR", aa=True, answers=["1.1.1.1"]), c)[1] == "CONFLICT"


def test_all_timeouts_is_inconclusive_timeout():
    assert run(base("TIMEOUT"), [silent(1), silent(2), silent(3)])[:2] == (INCONCLUSIVE, "TIMEOUT")


def test_canary_hit_without_a_reply_is_not_recursion():          # the slow server t17
    label, reason, _, detail = run(base("TIMEOUT"), [silent(1, True), silent(2, True), silent(3, True)])
    assert (label, reason) == (INCONCLUSIVE, "TIMEOUT")


def test_late_hits_are_reported_in_the_verdict():
    v = classify_target(T, [base("TIMEOUT")] + [silent(k, True) for k in (1, 2, 3)], MARKER, 3)
    assert v.late_hits == 3 and "never reached us" in v.detail and v.label == INCONCLUSIVE


def test_rate_limited_server_is_timeout():
    assert run(base("NOERROR"), [silent(1), silent(2), silent(3)])[:2] == (INCONCLUSIVE, "TIMEOUT")


def test_servfail():
    c = [rec("canary", k, "SERVFAIL") for k in (1, 2, 3)]
    assert run(base(), c)[:2] == (INCONCLUSIVE, "SERVFAIL")


def test_servfail_mixed_with_timeouts_is_servfail():
    assert run(base(), [rec("canary", 1, "SERVFAIL"), silent(2), silent(3)])[1] == "SERVFAIL"


def test_truncated_reply_that_tcp_cannot_finish():
    assert run(base(), [rec("canary", 1, "TC_FAIL"), good(2), good(3)])[1] == "TC_FAIL"


def test_local_network_error():
    assert run(base("ERROR"), [rec("canary", k, "ERROR") for k in (1, 2, 3)])[1] == "ERROR"


def test_one_lost_attempt_among_good_ones_is_a_conflict():
    assert run(base(), [good(1), silent(2), good(3)])[:2] == (INCONCLUSIVE, "CONFLICT")


def test_marker_answer_without_canary_hit_is_a_conflict():
    c = [dict(good(k), canary_hit=False, canary_sources=[]) for k in (1, 2, 3)]
    assert run(base(), c)[:2] == (INCONCLUSIVE, "CONFLICT")


def test_ra_without_the_marker_is_a_conflict():
    c = [rec("canary", k, "NOERROR", ra=True) for k in (1, 2, 3)]
    assert run(base(), c)[1] == "CONFLICT"


def test_refused_and_answered_attempts_mixed_is_a_conflict():
    assert run(base("REFUSED"), [refused(1), good(2), refused(3)])[1] == "CONFLICT"


def test_missing_evidence_is_no_data():
    assert run(None, [])[:2] == (INCONCLUSIVE, "NO_DATA")
    assert run(base(), [good(1)])[1] == "NO_DATA"


def liar(k, aa=False):
    return rec("canary", k, "NOERROR", ra=True, aa=aa, answers=[MARKER], hit=False)


def test_local_answer_liar_is_a_conflict_not_recursion():
    assert run(base("TIMEOUT"), [liar(1, True), liar(2, True), liar(3, True)])[:3] == (INCONCLUSIVE, "CONFLICT", "R4")


def test_sinkhole_with_aa_clear_is_a_conflict_not_recursion():
    assert run(base("SERVFAIL"), [liar(1), liar(2), liar(3)])[:2] == (INCONCLUSIVE, "CONFLICT")


def test_wildcard_hijacker_that_also_answers_the_baseline_is_a_conflict():
    b = base("NOERROR", aa=True, answers=[MARKER])
    assert run(b, [liar(1, True), liar(2, True), liar(3, True)])[1] == "CONFLICT"


@pytest.mark.parametrize("ra", [False, True])
def test_refuser_is_refused_whatever_its_ra_bit(ra):
    c = [rec("canary", k, "REFUSED", ra=ra) for k in (1, 2, 3)]
    assert run(base("REFUSED"), c)[:3] == (REFUSED, None, "R2")


def make_run(tmp_path, records, targets=None, attempts=3, with_canary=True):
    d = tmp_path / "run"
    d.mkdir()
    m = {"targets": targets or [T], "config": {"probe": {"attempts": attempts}, "targets_file": str(tmp_path / "t.yaml")}}
    if with_canary:
        m["canary"] = {"marker_ip": MARKER}
    (d / "manifest.json").write_text(json.dumps(m))
    (d / "evidence.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    return d


def test_classify_run_writes_both_verdict_files_deterministically(tmp_path):
    d = make_run(tmp_path, [base(), good(1), good(2), good(3)])
    v = classify_run(d)
    assert v[0].label == RECURSIVE
    first = (d / "verdicts.csv").read_bytes(), (d / "verdicts.jsonl").read_bytes()
    classify_run(d)
    assert first == ((d / "verdicts.csv").read_bytes(), (d / "verdicts.jsonl").read_bytes())
    assert (d / "verdicts.csv").read_text().splitlines()[0].startswith("target_id,ip,software,label,reason")


def test_target_without_any_evidence_is_no_data(tmp_path):
    d = make_run(tmp_path, [], targets=[T, {"id": "t02", "ip": "10.10.0.12", "software": "bind"}])
    assert [x.reason for x in classify_run(d)] == ["NO_DATA", "NO_DATA"]


def test_marker_falls_back_to_the_targets_file(tmp_path):
    (tmp_path / "t.yaml").write_text("lab: {canary: {marker_ip: 192.0.2.53}}\ntargets: []\n")
    d = make_run(tmp_path, [base(), good(1), good(2), good(3)], with_canary=False)
    assert classify_run(d)[0].label == RECURSIVE


def test_cli_check_reports_matches_and_mismatches(tmp_path, capsys):
    (tmp_path / "t.yaml").write_text("lab: {canary: {marker_ip: 192.0.2.53}}\ntargets:\n  - {id: t01, expected: recursive}\n")
    d = make_run(tmp_path, [base(), good(1), good(2), good(3)])
    assert main(["classify", str(d), "--check"]) == 0
    assert "1/1 verdicts match" in capsys.readouterr().out
    (tmp_path / "t.yaml").write_text("lab: {canary: {marker_ip: 192.0.2.53}}\ntargets:\n  - {id: t01, expected: refused}\n")
    assert main(["classify", str(d), "--check"]) == 1


REAL = Path("docs/examples/phase2-first")


@pytest.mark.skipif(not (REAL / "evidence.jsonl").exists(), reason="Docker evidence not in this checkout")
def test_the_real_docker_run_is_classified_correctly(tmp_path):
    import shutil
    shutil.copytree(REAL, tmp_path / "r")
    verdicts = classify_run(tmp_path / "r", "lab/targets.yaml")
    from resolverlens.compare import compare, expected_labels
    rows = compare(verdicts, expected_labels("lab/targets.yaml"))
    wrong = [(r["target_id"], r["expected"], r["label"], r["reason"]) for r in rows if not r["match"]]
    assert not wrong, wrong
    assert len(rows) == 20
