import dns.exception

from conftest import make_reply
from resolverlens.cli import main
from resolverlens.runner import run_probe
from resolverlens.stability import stability


LINE = "25-Oct-2026 14:22:38.977 client @0x7f2ce000f2f8 10.10.0.11#58827 ({name}): query: {name} IN A -E(0)DC (10.10.0.5)\n"
LOG = {}


def ok(q, ip, timeout, source, tcp):
    """Answers with the marker and writes the canary log entry, like a real recursive server."""
    name = q.question[0].name.to_text().rstrip(".")
    if q.flags & 0x0100 and LOG.get("path"):
        with open(LOG["path"], "a") as f:
            f.write(LINE.format(name=name))
    return make_reply(q, ra=True, address="192.0.2.53")


def flaky(q, ip, timeout, source, tcp):
    if ip == "10.10.0.11":
        raise dns.exception.Timeout()
    return ok(q, ip, timeout, source, tcp)


def runs(lab_files, a, b):
    LOG["path"] = lab_files["log"]
    for rid, t in (("a", a), ("b", b)):
        run_probe(lab_files["config"], run_id=rid, out=lambda s: None, transport=t)
    base = lab_files["dir"] / "results"
    return [base / "a", base / "b"]


def test_identical_runs_are_stable(lab_files):
    res = stability(runs(lab_files, ok, ok))
    assert res["stable"] and res["unstable"] == []


def test_a_server_that_changes_is_flagged(lab_files):
    res = stability(runs(lab_files, ok, flaky))
    assert not res["stable"] and res["unstable"] == ["t01"]
    assert res["rows"][0]["values"][0] != res["rows"][0]["values"][1]


def test_cli_exit_codes(lab_files, capsys):
    a, b = runs(lab_files, ok, ok)
    assert main(["stability", str(a), str(b)]) == 0
    assert "3/3 servers keep the same label across 2 runs" in capsys.readouterr().out
    c = lab_files["dir"] / "results"
    LOG["path"] = lab_files["log"]
    run_probe(lab_files["config"], run_id="c", out=lambda s: None, transport=flaky)
    assert main(["stability", str(a), str(c / "c")]) == 1
    assert "UNSTABLE" in capsys.readouterr().out


def test_a_changing_reason_with_the_same_label_is_only_a_note(lab_files):
    def silent(q, ip, timeout, source, tcp):
        raise dns.exception.Timeout()

    def half(q, ip, timeout, source, tcp):           # one answered attempt among timeouts: CONFLICT instead of TIMEOUT
        if q.question[0].name.to_text().startswith("ns."):
            raise dns.exception.Timeout()
        half.n += 1
        if half.n == 1:
            return ok(q, ip, timeout, source, tcp)
        raise dns.exception.Timeout()
    half.n = 0
    res = stability(runs(lab_files, silent, half))
    t01 = res["rows"][0]
    assert t01["stable"] and t01["reason_varies"] and "t01" in res["reason_varies"]


def test_a_missing_target_counts_as_unstable(lab_files):
    LOG["path"] = lab_files["log"]
    run_probe(lab_files["config"], run_id="a", out=lambda s: None, transport=ok)
    run_probe(lab_files["config"], run_id="b", only="t01", out=lambda s: None, transport=ok)
    base = lab_files["dir"] / "results"
    res = stability([base / "a", base / "b"])
    assert set(res["unstable"]) == {"t06", "t19"}
