import json
import shutil
from pathlib import Path

import pytest
import yaml

from resolverlens.cli import main
from resolverlens.report import build_report

MARK = "192.0.2.53"


def _rec(tid, ip, seq, phase, attempt, status, ra=False, aa=False, answers=(), hit=False, sources=(), rd=True, ts=0.0):
    return {"run_id": "r1", "seq": seq, "ts": f"2026-10-26T00:00:{int(ts):02d}.000+00:00", "target_id": tid, "target_ip": ip, "phase": phase,
            "attempt": attempt, "qname": f"rl-{tid}{attempt}.canary.lab", "qtype": "A", "rd": rd, "transport": "udp", "status": status,
            "rcode": None, "flags": {"ra": ra, "aa": aa} if status not in ("TIMEOUT",) else {}, "answers": list(answers), "rtt_ms": 1.0,
            "query_bytes": 40, "reply_bytes": None if status == "TIMEOUT" else 90, "tcp_retry": False, "error": None,
            "canary_hit": hit, "canary_sources": list(sources), "canary_wait_ms": 0.0}


def make_run(tmp_path, expected=("recursive", "refused", "inconclusive"), software=("bind", "bind", "dnsmasq")):
    ids = [("t01", "10.10.0.11"), ("t02", "10.10.0.12"), ("t03", "10.10.0.13")]
    targets = tmp_path / "targets.yaml"
    targets.write_text(yaml.safe_dump({"lab": {"canary": {"marker_ip": MARK, "zone": "canary.lab", "ip": "10.10.0.5"}, "subnet": "10.10.0.0/16"},
        "targets": [{"id": i, "ip": ip, "software": s, "behavior": b, "expected": e} for (i, ip), s, e, b in
                    zip(ids, software, expected, ("open_recursive", "policy_refusing", "silent"))]}))
    ev, seq = [], 0
    for tid, ip in ids:
        seq += 1
        if tid == "t01":
            ev.append(_rec(tid, ip, seq, "baseline", 0, "NOERROR", rd=False, ts=0))
            ev += [_rec(tid, ip, seq + k, "canary", k, "NOERROR", ra=True, answers=[MARK], hit=True, sources=[ip], ts=k) for k in (1, 2, 3)]
        elif tid == "t02":
            ev.append(_rec(tid, ip, seq, "baseline", 0, "REFUSED", rd=False, ts=4))
            ev += [_rec(tid, ip, seq + k, "canary", k, "REFUSED", ts=4 + k) for k in (1, 2, 3)]
        else:
            ev.append(_rec(tid, ip, seq, "baseline", 0, "TIMEOUT", rd=False, ts=8))
            ev += [_rec(tid, ip, seq + k, "canary", k, "TIMEOUT", ts=8 + k) for k in (1, 2, 3)]
        seq += 3
    d = tmp_path / "run"
    d.mkdir()
    for i, r in enumerate(ev, 1):
        r["seq"] = i
    (d / "evidence.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ev))
    (d / "manifest.json").write_text(json.dumps({"run_id": "r1", "started_utc": "2026-10-26T00:00:00+00:00", "seed": 7, "probes": len(ev),
        "duration_s": 12.0, "config_digest": "ab" * 32, "stop_reason": "completed", "tool_version": "0.2.0",
        "canary": {"marker_ip": MARK, "zone": "canary.lab", "ip": "10.10.0.5"},
        "config": {"targets_file": str(targets), "probe": {"attempts": 3, "timeout_s": 2.0, "edns_payload": 1232},
                   "rate": {"global": {"rate": 5.0}, "per_target": {"rate": 1.0}}, "safety": {"max_reply_bytes": 1232, "max_ratio": 10.0}},
        "targets": [{"id": i, "ip": ip, "software": s} for (i, ip), s in zip(ids, software)]}))
    return d


def test_report_files_and_key_content(tmp_path):
    d = make_run(tmp_path)
    out = build_report(d)
    for k in ("html", "summary", "scores"):
        assert out[k].exists()
    html = out["html"].read_text()
    assert "DNS Resolver Exposure Assessment Report" in html and "No false results" in html
    assert all(t in html for t in ("t01", "t02", "t03"))
    assert "Expected \\ Reported" in html
    assert "1 of 3</b> servers provide recursion" in html
    s = json.loads(out["scores"].read_text())
    assert s["summary"]["correct"] == 3 and s["confusion"]["recursive"]["recursive"] == 1 and s["false_results"] == []
    assert s["inconclusive"][0]["seeded"] == "silent"


def test_report_is_deterministic(tmp_path):
    d = make_run(tmp_path)
    a = build_report(d)["html"].read_bytes()
    b = build_report(d)["html"].read_bytes()
    assert a == b


def test_wrong_expected_label_appears_as_a_false_result_with_a_cause(tmp_path):
    d = make_run(tmp_path, expected=("recursive", "recursive", "inconclusive"))
    out = build_report(d)
    html = out["html"].read_text()
    assert "False results" in html and "ACL" in html and "No false results" not in html
    s = json.loads(out["scores"].read_text())
    assert s["false_results"][0]["target_id"] == "t02" and s["false_results"][0]["cause"]["category"] == "ACL"
    assert s["summary"]["missed_exposure"] == 1


def test_remediation_is_software_specific(tmp_path):
    d = make_run(tmp_path, software=("unbound", "bind", "dnsmasq"))
    assert "access-control: 0.0.0.0/0 refuse" in build_report(d)["html"].read_text()


def test_html_is_escaped(tmp_path):
    d = make_run(tmp_path, software=("<script>alert(1)</script>", "bind", "dnsmasq"))
    html = build_report(d)["html"].read_text()
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_pdf_is_optional_and_never_crashes(tmp_path):
    out = build_report(make_run(tmp_path), pdf=True)
    assert "pdf" in out or "pdf_error" in out


def test_cli_report_exit_code(tmp_path, capsys):
    d = make_run(tmp_path)
    assert main(["report", str(d)]) == 0
    assert "3/3 verdicts match" in capsys.readouterr().out
    d2 = make_run(tmp_path / "x" if (tmp_path / "x").mkdir() is None else tmp_path, expected=("recursive", "recursive", "inconclusive"))
    assert main(["report", str(d2)]) == 1


REAL = Path("docs/examples/phase2-first")


@pytest.mark.skipif(not (REAL / "evidence.jsonl").exists(), reason="Docker evidence not in this checkout")
def test_report_on_the_real_docker_run(tmp_path):
    shutil.copytree(REAL, tmp_path / "r")
    out = build_report(tmp_path / "r", "lab/targets.yaml")
    s = json.loads(out["scores"].read_text())["summary"]
    assert s["total"] == 20 and s["correct"] == 20 and s["wrong_decisions"] == 0 and abs(s["coverage"] - 0.8) < 1e-9
