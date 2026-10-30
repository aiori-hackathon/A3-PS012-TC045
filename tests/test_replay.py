import json

from conftest import make_reply
from resolverlens.classify import classify_run
from resolverlens.replay import replay
from resolverlens.runner import run_probe


def ok(q, ip, timeout, source, tcp):
    return make_reply(q, ra=True, address="192.0.2.53")


def make(lab_files, rid="r1"):
    run_probe(lab_files["config"], run_id=rid, out=lambda s: None, transport=ok)
    return lab_files["dir"] / "results" / rid


def failed(res):
    return [c["check"] for c in res["checks"] if not c["ok"]]


def test_clean_run_replays(lab_files):
    d = make(lab_files)
    res = replay(d)
    assert res["ok"], failed(res)
    classify_run(d)                                     # store verdicts, then replay must reproduce them byte for byte
    assert replay(d)["ok"]


def test_manifest_records_file_hashes(lab_files):
    m = json.loads((make(lab_files) / "manifest.json").read_text())
    assert set(m["files"]) == {"evidence.jsonl", "audit.log"} and all(len(v) == 64 for v in m["files"].values())


def test_tampered_evidence_is_detected(lab_files):
    d = make(lab_files)
    lines = (d / "evidence.jsonl").read_text().splitlines()
    rec = json.loads(lines[1])
    rec["status"] = "REFUSED"
    lines[1] = json.dumps(rec)
    (d / "evidence.jsonl").write_text("\n".join(lines) + "\n")
    res = replay(d)
    assert not res["ok"] and any("sha256" in c for c in failed(res))


def test_deleted_record_is_detected(lab_files):
    d = make(lab_files)
    lines = (d / "evidence.jsonl").read_text().splitlines()
    del lines[3]
    (d / "evidence.jsonl").write_text("\n".join(lines) + "\n")
    f = failed(replay(d))
    assert any("without gaps" in c for c in f) and any("record count" in c for c in f)


def test_altered_stored_verdicts_are_detected(lab_files):
    d = make(lab_files)
    classify_run(d)
    (d / "verdicts.csv").write_text((d / "verdicts.csv").read_text().replace("conflict", "recursive").replace("inconclusive", "recursive"))
    assert any("verdicts.csv" in c for c in failed(replay(d)))


def test_older_run_without_hashes_still_replays(lab_files):
    d = make(lab_files)
    m = json.loads((d / "manifest.json").read_text())
    del m["files"]
    (d / "manifest.json").write_text(json.dumps(m))
    res = replay(d)
    assert res["ok"] and any("not recorded" in c["note"] for c in res["checks"])


def test_destination_off_the_allowlist_is_detected(lab_files):
    d = make(lab_files)
    m = json.loads((d / "manifest.json").read_text())
    del m["files"]
    m["targets"] = m["targets"][:1]
    (d / "manifest.json").write_text(json.dumps(m))
    assert any("allowlist" in c for c in failed(replay(d)))
