from resolverlens.baseline import evaluate, flag_ra, flag_ra_aa
from resolverlens.classify import Verdict


def rec(status="NOERROR", ra=True, aa=False, answers=("192.0.2.53",), attempt=1, phase="canary"):
    return {"phase": phase, "attempt": attempt, "status": status, "flags": {"ra": ra, "aa": aa} if status != "TIMEOUT" else {}, "answers": list(answers)}


def verdict(tid, label):
    return Verdict(tid, "10.10.0.1", "bind", label, None, "R1")


def test_flag_checks():
    assert flag_ra(rec()) and not flag_ra(rec(ra=False)) and not flag_ra(rec("REFUSED")) and not flag_ra(rec("TIMEOUT")) and not flag_ra(None)
    assert flag_ra_aa(rec()) and not flag_ra_aa(rec(aa=True)) and not flag_ra_aa(rec(answers=()))


def test_only_the_first_canary_attempt_is_read():
    ev = {"t1": [rec(attempt=2), rec("TIMEOUT", attempt=1), rec(phase="baseline", attempt=0)]}
    out = evaluate([verdict("t1", "inconclusive")], ev, {"t1": "inconclusive"})
    assert out["methods"][1]["correct"] == 1                       # first attempt timed out: not exposed


def test_sinkhole_fools_both_flag_checks_but_not_resolverlens():
    ev = {"t1": [rec(aa=False)]}                                    # NOERROR, RA, AA clear, answer: looks like a real resolver
    out = evaluate([verdict("t1", "inconclusive")], ev, {"t1": "inconclusive"}, {"t1": "sinkhole_rewriter"})
    m = {x["key"]: x for x in out["methods"]}
    assert m["resolverlens"]["correct"] == 1
    assert m["flag_ra"]["false_exposure"] == 1 and m["flag_ra_aa"]["false_exposure"] == 1
    assert out["differences"][0]["seeded"] == "sinkhole rewriter"


def test_local_answer_liar_with_aa_set_fools_only_the_ra_check():
    ev = {"t1": [rec(aa=True)]}
    out = evaluate([verdict("t1", "inconclusive")], ev, {"t1": "inconclusive"})
    m = {x["key"]: x for x in out["methods"]}
    assert m["flag_ra"]["false_exposure"] == 1 and m["flag_ra_aa"]["correct"] == 1


def test_missed_exposure_is_counted():
    ev = {"t1": [rec("TIMEOUT")]}
    out = evaluate([verdict("t1", "inconclusive")], ev, {"t1": "recursive"})
    assert all(m["missed_exposure"] == 1 for m in out["methods"])


def test_all_agree_gives_no_differences():
    ev = {"t1": [rec()]}
    out = evaluate([verdict("t1", "recursive")], ev, {"t1": "recursive"})
    assert out["differences"] == [] and all(m["correct"] == 1 for m in out["methods"])
