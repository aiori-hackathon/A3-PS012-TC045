"""Configuration loading and validation. Hard safety caps cannot be raised from the config file."""
from __future__ import annotations

import hashlib
import ipaddress
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

HARD_MAX_TARGETS = 20
HARD_MAX_GLOBAL_RATE = 20.0   # queries per second, all targets together
HARD_MAX_TARGET_RATE = 5.0    # queries per second, one target


class ConfigError(ValueError):
    """The configuration file is invalid or unsafe."""


@dataclass(frozen=True)
class BucketCfg:
    rate: float
    burst: int


@dataclass(frozen=True)
class Config:
    seed: int
    output_dir: str
    targets_file: str
    canary_log: str
    timeout_s: float
    attempts: int
    tcp_retry: bool
    edns_payload: int
    canary_wait_s: float
    source_address: str | None
    per_target: BucketCfg
    global_bucket: BucketCfg
    jitter_ms: int
    max_targets: int
    max_reply_bytes: int
    max_ratio: float
    raw: dict


def _get(d: dict, key: str, lo: float, hi: float, cast=float):
    if key not in d:
        raise ConfigError(f"missing setting: {key}")
    try:
        v = cast(d[key])
    except (TypeError, ValueError):
        raise ConfigError(f"{key} must be a number") from None
    if not lo <= v <= hi:
        raise ConfigError(f"{key}={v} is outside the allowed range {lo} to {hi}")
    return v


def load_config(path: str | Path) -> Config:
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except OSError as e:
        raise ConfigError(f"cannot read {path}: {e}") from None
    if not isinstance(raw, dict):
        raise ConfigError("config file must be a YAML mapping")
    run, probe, rate, safety = (raw.get(k) or {} for k in ("run", "probe", "rate", "safety"))
    src = probe.get("source_address")
    if src is not None:
        try:
            ipaddress.ip_address(src)
        except ValueError:
            raise ConfigError(f"probe.source_address is not an IP address: {src}") from None
    pt, gl = rate.get("per_target") or {}, rate.get("global") or {}
    cfg = Config(
        seed=_get(run, "seed", 0, 2**31 - 1, int),
        output_dir=str(run.get("output_dir", "results")),
        targets_file=str(raw.get("targets_file", "lab/targets.yaml")),
        canary_log=str(raw.get("canary_log", "/canary-logs/queries.log")),
        timeout_s=_get(probe, "timeout_s", 0.2, 10.0),
        attempts=_get(probe, "attempts", 1, 5, int),
        tcp_retry=bool(probe.get("tcp_retry", True)),
        edns_payload=_get(probe, "edns_payload", 512, 4096, int),
        canary_wait_s=_get(probe, "canary_wait_s", 0.0, 10.0),
        source_address=src,
        per_target=BucketCfg(_get(pt, "rate", 0.01, HARD_MAX_TARGET_RATE), _get(pt, "burst", 1, 10, int)),
        global_bucket=BucketCfg(_get(gl, "rate", 0.01, HARD_MAX_GLOBAL_RATE), _get(gl, "burst", 1, 20, int)),
        jitter_ms=_get(rate, "jitter_ms", 0, 500, int),
        max_targets=_get(safety, "max_targets", 1, HARD_MAX_TARGETS, int),
        max_reply_bytes=_get(safety, "max_reply_bytes", 512, 4096, int),
        max_ratio=_get(safety, "max_ratio", 1.0, 100.0),
        raw=raw,
    )
    return cfg


def config_digest(cfg: Config, targets_text: str) -> str:
    """Hash of the settings and the targets file, stored in every run manifest for reproducibility."""
    blob = json.dumps(cfg.raw, sort_keys=True) + "\n" + targets_text
    return hashlib.sha256(blob.encode()).hexdigest()
