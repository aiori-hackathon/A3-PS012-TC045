"""Preflight: check the setup before an assessment, including one real canary round trip through a reference server."""
from __future__ import annotations

import secrets
import shutil
from pathlib import Path

import dns.exception
import dns.flags
import dns.message

from resolverlens.canary import CanaryLog
from resolverlens.config import ConfigError, load_config
from resolverlens.names import canary_name
from resolverlens.probe import default_transport
from resolverlens.scope import ScopeError, ScopeGuard, load_lab

MIN_FREE_MB = 50


def run_preflight(config_path, out=print, transport=default_transport) -> bool:
    results = []

    def check(name, ok, note=""):
        results.append(ok)
        out(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""))

    out("preflight checks")
    try:
        cfg = load_config(config_path)
        check("settings are valid and inside the hard safety caps", True)
    except ConfigError as e:
        check("settings are valid and inside the hard safety caps", False, str(e))
        return False
    try:
        lab, targets = load_lab(cfg.targets_file)
        scope = ScopeGuard(lab, targets, cfg.max_targets)
        check("allowlist loads: private lab subnet, at most 20 targets", True, f"{len(targets)} targets")
    except (ScopeError, OSError, KeyError) as e:
        check("allowlist loads: private lab subnet, at most 20 targets", False, str(e))
        return False
    root = Path(cfg.output_dir)
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe_file = root / ".preflight-write-test"
        probe_file.write_text("x")
        probe_file.unlink()
        free = shutil.disk_usage(root).free // (1 << 20)
        check("results folder is writable and has free space", free >= MIN_FREE_MB, f"{free} MB free")
    except OSError as e:
        check("results folder is writable and has free space", False, str(e))
    check("no stop file is present", not (root / "STOP").exists())
    log = Path(cfg.canary_log)
    try:
        log.stat()
        check("canary query log is readable", log.is_file() and bool(log.open("rb").read(1) is not None))
    except OSError as e:
        check("canary query log is readable", False, str(e))
    ref = next((t for t in targets if t.id == cfg.reference_target), None)
    if ref is None:
        check(f"reference target {cfg.reference_target} is in the allowlist", False)
    else:
        scope.check(ref.ip)
        name = canary_name(cfg.seed, f"preflight-{secrets.token_hex(4)}", ref.id, 0, lab["canary"]["zone"])
        q = dns.message.make_query(name, "A", use_edns=0, payload=cfg.edns_payload, flags=dns.flags.RD)
        marker = lab["canary"]["marker_ip"]
        try:
            r = transport(q, ref.ip, cfg.timeout_s, cfg.source_address, False)
            answers = [rr.address for s in r.answer for rr in s if s.rdtype == 1]
            hit = CanaryLog(log).wait_for(name, max(cfg.canary_wait_s, 0.5))
            check(f"canary round trip through {ref.id}: marker answer and a canary log entry",
                  marker in answers and bool(hit), f"answer {answers or 'none'}, canary saw it from {hit or 'nobody'}")
        except (OSError, dns.exception.DNSException) as e:
            check(f"canary round trip through {ref.id}: marker answer and a canary log entry", False, f"{type(e).__name__}: {e}")
    ok = all(results)
    out("preflight " + ("passed" if ok else "FAILED"))
    return ok
