import textwrap

import dns.flags
import dns.message
import dns.rrset
import pytest

TARGETS_YAML = textwrap.dedent("""\
    lab:
      subnet: 10.10.0.0/16
      baseline_zone: lab.test
      trusted_range: 10.10.1.0/24
      canary: {name: rl-canary, ip: 10.10.0.5, zone: canary.lab, marker_ip: 192.0.2.53}
      clients:
        external: {name: rl-ext, ip: 10.10.2.10}
        control: {name: rl-ctl, ip: 10.10.1.10}
    targets:
      - {id: t01, ip: 10.10.0.11, software: bind, behavior: open_recursive, expected: recursive}
      - {id: t06, ip: 10.10.0.16, software: bind, behavior: policy_refusing, expected: refused}
      - {id: t19, ip: 10.10.0.29, software: dnsmasq, behavior: silent, expected: inconclusive}
""")

CONFIG_YAML = textwrap.dedent("""\
    targets_file: {targets}
    canary_log: {log}
    run: {{seed: 7, output_dir: {out}}}
    probe: {{timeout_s: 0.5, attempts: 3, tcp_retry: true, edns_payload: 1232, canary_wait_s: 0.0, source_address: null}}
    rate:
      per_target: {{rate: 5.0, burst: 10}}
      global: {{rate: 20.0, burst: 20}}
      jitter_ms: 0
    safety: {{max_targets: 20, max_reply_bytes: 1232, max_ratio: 10.0}}
""")


@pytest.fixture
def lab_files(tmp_path):
    targets = tmp_path / "targets.yaml"
    targets.write_text(TARGETS_YAML)
    log = tmp_path / "queries.log"
    log.write_text("")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(CONFIG_YAML.format(targets=targets, log=log, out=tmp_path / "results"))
    return {"dir": tmp_path, "targets": targets, "log": log, "config": cfg}


def make_reply(query, rcode="NOERROR", ra=False, aa=False, tc=False, address=None, pad=0):
    r = dns.message.make_response(query)
    r.set_rcode(__import__("dns.rcode", fromlist=["x"]).from_text(rcode))
    if ra:
        r.flags |= dns.flags.RA
    if aa:
        r.flags |= dns.flags.AA
    if tc:
        r.flags |= dns.flags.TC
    if address:
        r.answer.append(dns.rrset.from_text(query.question[0].name, 0, "IN", "A", address))
    for i in range(pad):
        r.additional.append(dns.rrset.from_text(f"pad{i}.example.", 0, "IN", "TXT", "x" * 200))
    return r
