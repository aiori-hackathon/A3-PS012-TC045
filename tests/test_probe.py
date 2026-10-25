import dns.exception
import pytest

from conftest import make_reply
from resolverlens.canary import CanaryLog
from resolverlens.config import load_config
from resolverlens.evidence import EvidenceWriter
from resolverlens.probe import Prober, SafetyStop
from resolverlens.ratelimit import RateController
from resolverlens.scope import ScopeError, ScopeGuard, Target, load_lab


class FakeCanary:
    def __init__(self, hits=()):
        self.hits, self.asked = set(hits), []

    def wait_for(self, name, timeout):
        self.asked.append((name, timeout))
        return ["10.10.0.11"] if name in self.hits or "*" in self.hits else []


def build(lab_files, transport, canary=None, tmp=None):
    cfg = load_config(lab_files["config"])
    lab, targets = load_lab(lab_files["targets"])
    run_dir = lab_files["dir"] / "run"
    run_dir.mkdir(exist_ok=True)
    w = EvidenceWriter(run_dir)
    rate = RateController(cfg.per_target, cfg.global_bucket, 0, cfg.seed)
    return Prober(cfg, lab, ScopeGuard(lab, targets), rate, canary or FakeCanary(), w, "r1", transport=transport), targets, w


def test_open_recursive_server_records_flags_answer_and_canary_hit(lab_files):
    def transport(q, ip, timeout, source, tcp):
        return make_reply(q, ra=True, address="192.0.2.53") if q.flags & 0x0100 else make_reply(q)
    p, targets, w = build(lab_files, transport, FakeCanary(hits={"*"}))
    recs = p.probe_target(targets[0])
    assert [r["phase"] for r in recs] == ["baseline", "canary", "canary", "canary"]
    assert recs[0]["rd"] is False and all(r["rd"] for r in recs[1:])
    c = recs[1]
    assert c["status"] == "NOERROR" and c["flags"]["ra"] and c["answers"] == ["192.0.2.53"] and c["canary_hit"]
    assert len({r["qname"] for r in recs[1:]}) == 3                      # a fresh name every attempt


def test_timeouts_are_recorded_without_crashing(lab_files):
    def transport(q, ip, timeout, source, tcp):
        raise dns.exception.Timeout()
    p, targets, w = build(lab_files, transport)
    recs = p.probe_target(targets[2])
    assert {r["status"] for r in recs} == {"TIMEOUT"} and not any(r["canary_hit"] for r in recs)


def test_truncated_reply_is_retried_over_tcp(lab_files):
    calls = []

    def transport(q, ip, timeout, source, tcp):
        calls.append(tcp)
        return make_reply(q, tc=not tcp, ra=True, address="192.0.2.53")
    p, targets, w = build(lab_files, transport)
    rec = p._send(targets[0], "x.canary.lab", True, "canary", 1)
    assert calls == [False, True] and rec["transport"] == "tcp" and rec["tcp_retry"] and rec["status"] == "NOERROR"


def test_tcp_failure_gives_tc_fail(lab_files):
    def transport(q, ip, timeout, source, tcp):
        if tcp:
            raise ConnectionRefusedError("no tcp")
        return make_reply(q, tc=True)
    p, targets, w = build(lab_files, transport)
    rec = p._send(targets[0], "x.canary.lab", True, "canary", 1)
    assert rec["status"] == "TC_FAIL" and "ConnectionRefusedError" in rec["error"]


def test_network_error_is_recorded(lab_files):
    def transport(q, ip, timeout, source, tcp):
        raise OSError(101, "Network is unreachable")
    p, targets, w = build(lab_files, transport)
    rec = p._send(targets[0], "x.canary.lab", True, "canary", 1)
    assert rec["status"] == "ERROR" and "unreachable" in rec["error"]


def test_off_allowlist_target_sends_nothing(lab_files):
    sent = []
    p, targets, w = build(lab_files, lambda *a: sent.append(a))
    with pytest.raises(ScopeError):
        p._send(Target("tx", "8.8.8.8", "bind"), "x.canary.lab", True, "canary", 1)
    assert sent == []


def test_oversized_reply_stops_the_run_after_recording_it(lab_files):
    def transport(q, ip, timeout, source, tcp):
        return make_reply(q, ra=True, address="192.0.2.53", pad=12)
    p, targets, w = build(lab_files, transport)
    with pytest.raises(SafetyStop):
        p.probe_target(targets[0])
    w.close()
    assert (lab_files["dir"] / "run" / "evidence.jsonl").read_text().count("\n") == 1


def test_queries_are_never_any_type(lab_files):
    seen = []

    def transport(q, ip, timeout, source, tcp):
        seen.append(q.question[0].rdtype)
        return make_reply(q)
    p, targets, w = build(lab_files, transport)
    p.probe_target(targets[0])
    assert set(seen) == {1}                                              # type A only
