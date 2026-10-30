import dns.exception
import yaml

from conftest import make_reply
from resolverlens.preflight import run_preflight
from resolverlens.runner import EXIT_OK, EXIT_PREFLIGHT, run_probe

LINE = "25-Oct-2026 14:22:38.977 client @0x7f2ce000f2f8 10.10.0.11#58827 ({name}): query: {name} IN A -E(0)DC (10.10.0.5)\n"


def good_transport(log_path):
    def t(q, ip, timeout, source, tcp):
        name = q.question[0].name.to_text().rstrip(".")
        with open(log_path, "a") as f:
            f.write(LINE.format(name=name))
        return make_reply(q, ra=True, address="192.0.2.53")
    return t


def lines():
    buf = []
    return buf, buf.append


def test_all_checks_pass(lab_files):
    buf, out = lines()
    assert run_preflight(lab_files["config"], out=out, transport=good_transport(lab_files["log"]))
    assert buf[-1] == "preflight passed" and not any("FAIL" in l for l in buf)


def test_timeout_from_the_reference_target_fails(lab_files):
    def t(q, ip, timeout, source, tcp):
        raise dns.exception.Timeout()
    buf, out = lines()
    assert not run_preflight(lab_files["config"], out=out, transport=t)
    assert any("FAIL" in l and "canary round trip" in l for l in buf)


def test_marker_answer_without_a_canary_log_entry_fails(lab_files):
    t = lambda q, ip, timeout, source, tcp: make_reply(q, ra=True, address="192.0.2.53")
    buf, out = lines()
    assert not run_preflight(lab_files["config"], out=out, transport=t)
    assert any("nobody" in l for l in buf)


def test_wrong_answer_fails(lab_files):
    def t(q, ip, timeout, source, tcp):
        good_transport(lab_files["log"])(q, ip, timeout, source, tcp)
        return make_reply(q, ra=True, address="203.0.113.9")
    assert not run_preflight(lab_files["config"], out=lambda s: None, transport=t)


def test_stop_file_fails(lab_files):
    root = lab_files["dir"] / "results"
    root.mkdir()
    (root / "STOP").write_text("")
    buf, out = lines()
    assert not run_preflight(lab_files["config"], out=out, transport=good_transport(lab_files["log"]))
    assert any("FAIL" in l and "stop file" in l for l in buf)


def test_missing_canary_log_fails(lab_files):
    lab_files["log"].unlink()
    buf, out = lines()
    assert not run_preflight(lab_files["config"], out=out, transport=good_transport(lab_files["log"]))
    assert any("FAIL" in l and "canary query log" in l for l in buf)


def test_unknown_reference_target_fails(lab_files):
    d = yaml.safe_load(lab_files["config"].read_text())
    d["preflight"] = {"reference_target": "t99"}
    lab_files["config"].write_text(yaml.safe_dump(d))
    assert not run_preflight(lab_files["config"], out=lambda s: None, transport=good_transport(lab_files["log"]))


def test_invalid_config_stops_early(lab_files):
    d = yaml.safe_load(lab_files["config"].read_text())
    d["rate"]["global"]["rate"] = 500
    lab_files["config"].write_text(yaml.safe_dump(d))
    buf, out = lines()
    assert not run_preflight(lab_files["config"], out=out, transport=good_transport(lab_files["log"]))
    assert len(buf) == 2


def test_probe_refuses_to_start_when_preflight_fails(lab_files):
    t = lambda q, ip, timeout, source, tcp: (_ for _ in ()).throw(dns.exception.Timeout())
    assert run_probe(lab_files["config"], run_id="p1", out=lambda s: None, transport=t, preflight=True) == EXIT_PREFLIGHT
    assert not (lab_files["dir"] / "results" / "p1").exists()


def test_probe_runs_after_a_passing_preflight(lab_files):
    assert run_probe(lab_files["config"], run_id="p2", out=lambda s: None, transport=good_transport(lab_files["log"]), preflight=True) == EXIT_OK
    assert (lab_files["dir"] / "results" / "p2" / "manifest.json").exists()
