import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

GEN = Path("lab/generate.py")


def load_module():
    spec = importlib.util.spec_from_file_location("rl_generate", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_gen(args, tmp_path):
    return subprocess.run([sys.executable, str(GEN), *args], capture_output=True, text=True, cwd=Path.cwd())


def test_main_profile_has_20_targets_and_23_services(tmp_path):
    r = run_gen(["--out", str(tmp_path / "g")], tmp_path)
    assert r.returncode == 0, r.stderr
    d = yaml.safe_load((tmp_path / "g" / "docker-compose.yml").read_text())
    assert len(d["services"]) == 23 and d["name"] == "rl" and d["networks"]["rl-lab"]["internal"] is True


def test_challenge_profile_attaches_to_the_existing_network(tmp_path):
    r = run_gen(["--attach", "--targets", "lab/challenge.yaml", "--out", str(tmp_path / "c")], tmp_path)
    assert r.returncode == 0, r.stderr
    d = yaml.safe_load((tmp_path / "c" / "docker-compose.yml").read_text())
    assert d["name"] == "rlc" and d["networks"]["rl-lab"] == {"name": "rl-lab", "external": True}
    assert sorted(d["services"]) == [f"rl-c0{i}" for i in range(1, 7)]
    assert "rl-canary" not in d["services"] and "depends_on" not in d["services"]["rl-c01"]
    assert d["services"]["rl-c05"]["environment"]["RL_DELAY_MS"] == "500" and "NET_ADMIN" in d["services"]["rl-c05"]["cap_add"]


def test_sinkhole_gets_a_response_policy_zone_and_no_recursion_path(tmp_path):
    run_gen(["--attach", "--targets", "lab/challenge.yaml", "--out", str(tmp_path / "c")], tmp_path)
    conf = (tmp_path / "c" / "targets" / "c06" / "named.conf").read_text()
    assert "response-policy" in conf and "qname-wait-recurse no" in conf and "static-stub" not in conf
    assert "*.canary.lab.rpz.lab. IN A 192.0.2.53" in (tmp_path / "c" / "targets" / "c06" / "rpz.zone").read_text()


def test_liar_never_forwards_to_the_canary_server(tmp_path):
    run_gen(["--attach", "--targets", "lab/challenge.yaml", "--out", str(tmp_path / "c")], tmp_path)
    c01 = (tmp_path / "c" / "targets" / "c01" / "dnsmasq.conf").read_text()
    assert "address=/canary.lab/192.0.2.53" in c01 and "server=/canary.lab/10.10.0.5" not in c01
    assert "address=/#/192.0.2.53" in (tmp_path / "c" / "targets" / "c02" / "dnsmasq.conf").read_text()


def edited(tmp_path, fn):
    d = yaml.safe_load(Path("lab/challenge.yaml").read_text())
    fn(d)
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(d))
    return run_gen(["--attach", "--targets", str(p), "--out", str(tmp_path / "o")], tmp_path)


def test_wrong_software_for_a_behaviour_is_rejected(tmp_path):
    r = edited(tmp_path, lambda d: d["targets"][0].update(software="bind"))
    assert r.returncode != 0 and "cannot be" in r.stderr


def test_expected_label_must_match_behaviour(tmp_path):
    r = edited(tmp_path, lambda d: d["targets"][0].update(expected="recursive"))
    assert r.returncode != 0 and "does not match" in r.stderr


def test_forwarder_needs_a_target(tmp_path):
    r = edited(tmp_path, lambda d: d["targets"][3].pop("forward_to_ip"))
    assert r.returncode != 0 and "forward_to" in r.stderr


def test_no_run_exceeds_twenty_targets(tmp_path):
    def many(d):
        for i in range(30):
            d["targets"].append({"id": f"x{i}", "ip": f"10.10.1.{100 + i}", "software": "bind", "behavior": "open_recursive", "expected": "recursive"})
    assert edited(tmp_path, many).returncode != 0


def test_challenge_ips_do_not_clash_with_the_main_lab():
    main = {t["ip"] for t in yaml.safe_load(Path("lab/targets.yaml").read_text())["targets"]}
    chal = {t["ip"] for t in yaml.safe_load(Path("lab/challenge.yaml").read_text())["targets"]}
    assert not (main & chal)
