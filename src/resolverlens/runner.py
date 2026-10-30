"""Runs one assessment: validates scope, probes each target in turn, and writes the run folder."""
from __future__ import annotations

import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from resolverlens import __version__
from resolverlens.canary import CanaryLog
from resolverlens.config import ConfigError, config_digest, load_config
from resolverlens.evidence import EvidenceWriter, sha256_file, write_manifest
from resolverlens.names import canary_name
from resolverlens.probe import Prober, SafetyStop
from resolverlens.ratelimit import RateController
from resolverlens.scope import ScopeError, ScopeGuard, load_lab

EXIT_OK, EXIT_CONFIG, EXIT_SAFETY, EXIT_PREFLIGHT, EXIT_INTERRUPTED = 0, 2, 3, 4, 130


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_probe(config_path, only=None, dry_run=False, run_id=None, out=print, transport=None, preflight=False) -> int:
    try:
        cfg = load_config(config_path)
        lab, targets = load_lab(cfg.targets_file)
        scope = ScopeGuard(lab, targets, cfg.max_targets)
        targets_text = Path(cfg.targets_file).read_text()
        if only:
            wanted = [x.strip() for x in only.split(",") if x.strip()]
            unknown = [w for w in wanted if w not in {t.id for t in targets}]
            if unknown:
                raise ConfigError(f"unknown target id(s): {', '.join(unknown)}")
            targets = [t for t in targets if t.id in wanted]
    except (ConfigError, ScopeError, OSError, KeyError) as e:
        out(f"error: {e}")
        return EXIT_CONFIG

    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    per_target = 1 + cfg.attempts
    total = per_target * len(targets)
    min_s = max(total / cfg.global_bucket.rate, per_target / cfg.per_target.rate) if targets else 0
    out(f"ResolverLens {__version__}  run {run_id}  seed {cfg.seed}")
    out(f"targets: {len(targets)}  queries per target: {per_target} (1 baseline + {cfg.attempts} canary)  total: {total}")
    out(f"limits: per target {cfg.per_target.rate}/s burst {cfg.per_target.burst}; global "
        f"{cfg.global_bucket.rate}/s burst {cfg.global_bucket.burst}; timeout {cfg.timeout_s}s")
    if dry_run:
        out(f"DRY RUN: nothing is sent. Minimum time at these limits: about {min_s:.0f} s (more if servers time out).")
        out("example canary names: " + ", ".join(canary_name(cfg.seed, run_id, targets[0].id, k, lab['canary']['zone'])
                                                for k in range(1, cfg.attempts + 1)) if targets else "no targets")
        return EXIT_OK

    if preflight:
        from resolverlens.preflight import run_preflight
        if not run_preflight(config_path, out=out, **({} if transport is None else {"transport": transport})):
            out("preflight failed: nothing was assessed. Fix the failing check, or use --no-preflight to skip it.")
            return EXIT_PREFLIGHT
    root = Path(cfg.output_dir)
    run_dir = root / run_id
    if run_dir.exists():
        out(f"error: {run_dir} already exists; choose another --run-id")
        return EXIT_CONFIG
    run_dir.mkdir(parents=True)
    manifest = {"tool_version": __version__, "run_id": run_id, "status": "running", "started_utc": _utc(),
                "seed": cfg.seed, "config_digest": config_digest(cfg, targets_text), "config": cfg.raw,
                "canary": {"zone": lab["canary"]["zone"], "ip": lab["canary"]["ip"], "marker_ip": lab["canary"]["marker_ip"]},
                "targets": [{"id": t.id, "ip": t.ip, "software": t.software} for t in targets],
                "python": platform.python_version()}
    write_manifest(run_dir, manifest)
    writer = EvidenceWriter(run_dir)
    kw = {} if transport is None else {"transport": transport}
    rate = RateController(cfg.per_target, cfg.global_bucket, cfg.jitter_ms, cfg.seed)
    prober = Prober(cfg, lab, scope, rate, CanaryLog(cfg.canary_log), writer, run_id, **kw)
    counts, hits, code, reason = Counter(), 0, EXIT_OK, "completed"
    t_start = time.monotonic()
    try:
        for t in targets:
            if (root / "STOP").exists():
                code, reason = EXIT_INTERRUPTED, "stop file found"
                break
            recs = prober.probe_target(t)
            counts.update(r["status"] for r in recs)
            n_hit = sum(1 for r in recs if r["canary_hit"])
            hits += n_hit
            out(f"{t.id:<4} {t.ip:<13} {t.software:<8} " + " ".join(f"{k}={v}" for k, v in
                Counter(r["status"] for r in recs).items()) + f"  canary_hits={n_hit}/{cfg.attempts}")
    except SafetyStop as e:
        code, reason = EXIT_SAFETY, f"safety tripwire: {e}"
    except ScopeError as e:
        code, reason = EXIT_CONFIG, f"scope violation: {e}"
    except KeyboardInterrupt:
        code, reason = EXIT_INTERRUPTED, "interrupted by user"
    finally:
        writer.close()
        manifest["files"] = {n: sha256_file(run_dir / n) for n in ("evidence.jsonl", "audit.log")}
        manifest.update({"status": "completed" if code == EXIT_OK else "stopped", "stop_reason": reason,
                         "finished_utc": _utc(), "duration_s": round(time.monotonic() - t_start, 1),
                         "probes": prober.seq, "status_counts": dict(counts), "canary_hits": hits})
        write_manifest(run_dir, manifest)
    out(f"{reason}: {prober.seq} probes in {manifest['duration_s']} s -> {run_dir}/")
    return code
