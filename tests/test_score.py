from types import SimpleNamespace

from resolverlens.score import compliance, confusion, inconclusive_table, per_class, root_cause, summary


def row(exp, got, tid="t01"):
    return {"target_id": tid, "expected": exp, "label": got, "match": exp == got, "software": "bind", "reason": None}


ROWS = [row("recursive", "recursive")] * 4 + [row("recursive", "inconclusive"), row("refused", "refused"), row("refused", "recursive"),
        row("authoritative_only", "authoritative_only"), row("inconclusive", "inconclusive"), row("inconclusive", "inconclusive")]


def test_confusion_counts():
    m = confusion(ROWS)
    assert m["recursive"]["recursive"] == 4 and m["recursive"]["inconclusive"] == 1
    assert m["refused"]["recursive"] == 1 and m["inconclusive"]["inconclusive"] == 2
    assert sum(sum(v.values()) for v in m.values()) == len(ROWS)


def test_precision_recall_f1():
    pc = per_class(confusion(ROWS))["recursive"]
    assert (pc["tp"], pc["fp"], pc["fn"]) == (4, 1, 1)
    assert abs(pc["precision"] - 0.8) < 1e-9 and abs(pc["recall"] - 0.8) < 1e-9 and abs(pc["f1"] - 0.8) < 1e-9


def test_summary_numbers():
    s = summary(ROWS)
    assert s["total"] == 10 and s["correct"] == 8 and abs(s["accuracy"] - 0.8) < 1e-9
    assert s["decided"] == 7 and s["decided_correct"] == 6 and abs(s["accuracy_decided"] - 6 / 7) < 1e-9
    assert abs(s["coverage"] - 0.7) < 1e-9
    assert s["wrong_decisions"] == 1 and s["false_exposure"] == 1 and s["missed_exposure"] == 1
    assert s["abstained_correctly"] == 2 and s["abstained_wrongly"] == 1


def test_all_inconclusive_has_no_decided_accuracy():
    s = summary([row("inconclusive", "inconclusive")] * 3)
    assert s["accuracy_decided"] is None and s["coverage"] == 0
    pc = per_class(confusion([row("inconclusive", "inconclusive")]))
    assert pc["recursive"]["precision"] is None and pc["recursive"]["recall"] is None and pc["recursive"]["f1"] is None


def test_empty_input_does_not_divide_by_zero():
    s = summary([])
    assert s["accuracy"] is None and s["coverage"] is None


def V(reason=None):
    return SimpleNamespace(reason=reason)


def test_correct_verdict_has_no_root_cause():
    assert root_cause(row("recursive", "recursive"), V()) is None


def test_seeded_unusable_but_decided():
    c = root_cause(row("inconclusive", "recursive"), V())
    assert c["category"] == "impairment not effective"


def test_abstention_causes_follow_the_reason_code():
    r = row("recursive", "inconclusive")
    assert "packet loss" in root_cause(r, V("TIMEOUT"))["category"]
    assert root_cause(r, V("SERVFAIL"))["category"] == "upstream failure"
    assert root_cause(r, V("CONFLICT"))["category"] == "mixed evidence"
    assert root_cause(r, V("TC_FAIL"))["category"] == "truncated reply, TCP failed"
    assert root_cause(r, V("NO_DATA"))["category"] == "incomplete run"


def test_decided_versus_decided_pairs():
    assert root_cause(row("recursive", "refused"), V())["category"] == "ACL"
    assert root_cause(row("refused", "recursive"), V())["category"] == "ACL"
    assert root_cause(row("authoritative_only", "recursive"), V())["category"] == "recursion enabled"
    assert root_cause(row("recursive", "authoritative_only"), V())["category"] == "recursion not observed"


def ev(tid, ts, reply=100, query=40, ip=None):
    return {"target_id": tid, "target_ip": ip or f"10.10.0.{tid[1:]}", "ts": ts, "qtype": "A", "reply_bytes": reply, "query_bytes": query}


MAN = {"targets": [{"ip": "10.10.0.1"}, {"ip": "10.10.0.2"}], "config": {"rate": {"global": {"rate": 5.0}, "per_target": {"rate": 1.0}},
       "safety": {"max_reply_bytes": 1232, "max_ratio": 10.0}}, "stop_reason": "completed"}


def test_compliance_peak_rates_and_sizes():
    e = [ev("t1", "2026-10-26T00:00:00.000+00:00"), ev("t1", "2026-10-26T00:00:00.400+00:00"), ev("t2", "2026-10-26T00:00:00.800+00:00", reply=400),
         ev("t2", "2026-10-26T00:00:05.000+00:00")]
    c = compliance(e, MAN)
    assert c["probes"] == 4 and c["destinations"] == 2 and c["all_destinations_on_allowlist"]
    assert c["max_queries_per_second_all_targets"] == 3 and c["max_queries_per_second_one_target"] == 2
    assert c["max_reply_bytes"] == 400 and c["max_reply_to_query_ratio"] == 10.0 and c["query_types"] == ["A"]


def test_compliance_flags_an_address_off_the_allowlist():
    assert not compliance([ev("t9", "2026-10-26T00:00:00.000+00:00", ip="8.8.8.8")], MAN)["all_destinations_on_allowlist"]


def test_inconclusive_table_shows_seeded_behaviour():
    v = SimpleNamespace(label="inconclusive", target_id="t17", software="unbound", reason="TIMEOUT", late_hits=2)
    t = inconclusive_table([v], {"t17": "inconclusive"}, {"t17": "slow"})
    assert t[0]["seeded"] == "slow" and t[0]["expected_inconclusive"] and t[0]["late_hits"] == 2
