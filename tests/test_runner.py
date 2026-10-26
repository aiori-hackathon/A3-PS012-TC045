import json

from conftest import make_reply
from resolverlens.runner import EXIT_CONFIG, EXIT_INTERRUPTED, EXIT_OK, EXIT_SAFETY, run_probe


def ok_transport(q, ip, timeout, source, tcp):
    return make_reply(q, ra=True, address="192.0.2.53")


def quiet(*a, **k):
    pass


def test_full_run_writes_manifest_and_evidence(lab_files):
    code = run_probe(lab_files["config"], run_id="r1", out=quiet, transport=ok_transport)
    run = lab_files["dir"] / "results" / "r1"
    assert code == EXIT_OK
    lines = (run / "evidence.jsonl").read_text().splitlines()
    assert len(lines) == 3 * 4
    m = json.loads((run / "manifest.json").read_text())
    assert m["status"] == "completed" and m["probes"] == 12 and m["seed"] == 7 and len(m["config_digest"]) == 64
    assert all("expected" not in t for t in m["targets"])
    assert len((run / "audit.log").read_text().splitlines()) == 12


def test_only_selects_targets(lab_files):
    assert run_probe(lab_files["config"], only="t06", run_id="r2", out=quiet, transport=ok_transport) == EXIT_OK
    assert len((lab_files["dir"] / "results" / "r2" / "evidence.jsonl").read_text().splitlines()) == 4


def test_unknown_target_is_a_config_error(lab_files):
    assert run_probe(lab_files["config"], only="t99", out=quiet) == EXIT_CONFIG


def test_existing_run_folder_is_not_overwritten(lab_files):
    run_probe(lab_files["config"], run_id="r3", out=quiet, transport=ok_transport)
    assert run_probe(lab_files["config"], run_id="r3", out=quiet, transport=ok_transport) == EXIT_CONFIG


def test_dry_run_sends_and_writes_nothing(lab_files):
    sent = []
    code = run_probe(lab_files["config"], dry_run=True, run_id="r4", out=quiet, transport=lambda *a: sent.append(a))
    assert code == EXIT_OK and sent == [] and not (lab_files["dir"] / "results").exists()


def test_stop_file_ends_the_run_cleanly(lab_files):
    (lab_files["dir"] / "results").mkdir()
    (lab_files["dir"] / "results" / "STOP").write_text("")
    assert run_probe(lab_files["config"], run_id="r5", out=quiet, transport=ok_transport) == EXIT_INTERRUPTED
    m = json.loads((lab_files["dir"] / "results" / "r5" / "manifest.json").read_text())
    assert m["status"] == "stopped" and m["probes"] == 0


def test_tripwire_stops_the_run_and_is_recorded(lab_files):
    big = lambda q, ip, timeout, source, tcp: make_reply(q, ra=True, address="192.0.2.53", pad=12)
    assert run_probe(lab_files["config"], run_id="r6", out=quiet, transport=big) == EXIT_SAFETY
    m = json.loads((lab_files["dir"] / "results" / "r6" / "manifest.json").read_text())
    assert "tripwire" in m["stop_reason"]


def test_same_seed_and_run_id_give_the_same_names(lab_files):
    import shutil
    run_probe(lab_files["config"], run_id="same", out=quiet, transport=ok_transport)
    first = [json.loads(l)["qname"] for l in (lab_files["dir"] / "results" / "same" / "evidence.jsonl").read_text().splitlines()]
    shutil.rmtree(lab_files["dir"] / "results" / "same")
    run_probe(lab_files["config"], run_id="same", out=quiet, transport=ok_transport)
    second = [json.loads(l)["qname"] for l in (lab_files["dir"] / "results" / "same" / "evidence.jsonl").read_text().splitlines()]
    assert first == second


def test_manifest_records_the_canary_marker(lab_files):
    run_probe(lab_files["config"], run_id="r7", out=quiet, transport=ok_transport)
    m = json.loads((lab_files["dir"] / "results" / "r7" / "manifest.json").read_text())
    assert m["canary"] == {"zone": "canary.lab", "ip": "10.10.0.5", "marker_ip": "192.0.2.53"}
