"""Cloud-native Cisco Packet Tracer-style DNS topology & packet simulator for ResolverLens."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_dataset(run_dir: Path, targets_file: Path, report_prefix: str = "") -> dict:
    cfg = _load_yaml(targets_file)
    evidence = _load_jsonl(run_dir / "evidence.jsonl")
    verdicts = _load_jsonl(run_dir / "verdicts.jsonl")
    scores = json.loads((run_dir / "scores.json").read_text(encoding="utf-8")) if (run_dir / "scores.json").exists() else {}
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8")) if (run_dir / "manifest.json").exists() else {}

    by_target: dict[str, list[dict]] = {}
    for rec in evidence:
        by_target.setdefault(rec["target_id"], []).append(rec)

    verdict_map = {v["target_id"]: v for v in verdicts}
    ip_to_id = {t["ip"]: t["id"] for t in cfg.get("targets", [])}
    ip_to_id.setdefault("10.10.0.11", "t01")
    ip_to_id.setdefault("10.10.0.13", "t03")
    ip_to_id.setdefault("10.10.0.15", "t05")
    ip_to_id.setdefault("10.10.0.24", "t14")

    targets_out = []
    for t in cfg.get("targets", []):
        tid = t["id"]
        t_ev = by_target.get(tid, [])
        v = verdict_map.get(tid, {})
        hops = []
        if t.get("forward_to"):
            hops.append(t["forward_to"])
        elif t.get("forward_to_ip"):
            hop_id = ip_to_id.get(t["forward_to_ip"], t["forward_to_ip"])
            hops.append(hop_id)
            if hop_id == "t14":
                hops.append("t01")
        targets_out.append({
            "id": tid,
            "ip": t["ip"],
            "software": t["software"],
            "behavior": t["behavior"],
            "expected": t["expected"],
            "hops": hops,
            "verdict": v,
            "probes": t_ev,
        })

    return {
        "run_id": manifest.get("run_id", run_dir.name),
        "lab": cfg.get("lab", {}),
        "manifest": {
            "seed": manifest.get("seed", 1337),
            "duration_s": manifest.get("duration_s", 0),
            "probes": manifest.get("probes", len(evidence)),
            "canary_hits": manifest.get("canary_hits", 0),
        },
        "reports": {
            "html": f"{report_prefix}/report.html" if report_prefix and (run_dir / "report.html").exists() else "",
            "pdf": f"{report_prefix}/report.pdf" if report_prefix and (run_dir / "report.pdf").exists() else "",
        },
        "scores": scores,
        "targets": targets_out,
    }


def build_sim_bundle(repo_root: Path | str = ".") -> dict:
    root = Path(repo_root)
    datasets = {}
    results_dir = root / "results"
    if results_dir.exists():
        for d in sorted(results_dir.glob("demo-main-*"), reverse=True):
            if (d / "evidence.jsonl").exists():
                ds = load_dataset(d, root / "lab/targets.yaml", report_prefix=f"runs/{d.name}")
                ds["title"] = f"Live Cloud CI Run — Main Lab ({d.name})"
                datasets["live_main"] = ds
                break
        for d in sorted(results_dir.glob("demo-chal-*"), reverse=True):
            if (d / "evidence.jsonl").exists():
                ds = load_dataset(d, root / "lab/challenge.yaml", report_prefix=f"runs/{d.name}")
                ds["title"] = f"Live Cloud CI Run — Challenge Set ({d.name})"
                datasets["live_challenge"] = ds
                break

    specs = [
        ("main", "Main Lab — 20 Seeded Servers (phase5-main)", root / "docs/examples/phase5-main", root / "lab/targets.yaml", "examples/phase5-main"),
        ("challenge", "Challenge Lab — 6 Deceptive Servers (chal-a)", root / "docs/examples/chal-a", root / "lab/challenge.yaml", "examples/chal-a"),
        ("fault", "Fault Demo — rl-t18 Rate-Limit Removed (fault-t18)", root / "docs/examples/fault-t18", root / "lab/targets.yaml", "examples/fault-t18"),
        ("stab1", "Stability Run (stab-1)", root / "docs/examples/stab-1", root / "lab/targets.yaml", "examples/stab-1"),
    ]
    for key, title, rdir, tfile, prefix in specs:
        if rdir.exists() and tfile.exists() and (rdir / "evidence.jsonl").exists():
            ds = load_dataset(rdir, tfile, report_prefix=prefix)
            ds["title"] = title
            datasets[key] = ds

    meta = {
        "repo": os.environ.get("GITHUB_REPOSITORY", "aiori-hackathon/A3-PS012-TC045"),
        "sha": (os.environ.get("GITHUB_SHA") or "HEAD")[:7],
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    return {"meta": meta, "datasets": datasets}


def build_sim_html(out_path: Path | str = "docs/sim.html", repo_root: Path | str = ".", site_dir: Path | str | None = None) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    root = Path(repo_root)
    tpl_path = Path(__file__).with_name("sim_template.html")
    html_tpl = tpl_path.read_text(encoding="utf-8")
    bundle = build_sim_bundle(root)
    html = html_tpl.replace("__RLENS_SIM_DATA__", json.dumps(bundle, separators=(",", ":")))
    out.write_text(html, encoding="utf-8")

    if site_dir is not None:
        sdir = Path(site_dir)
        sdir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root / "docs", sdir, dirs_exist_ok=True)
        (sdir / "index.html").write_text(html, encoding="utf-8")
        (sdir / "sim.html").write_text(html, encoding="utf-8")
        results_dir = root / "results"
        if results_dir.exists():
            for d in results_dir.glob("demo-*"):
                if d.is_dir():
                    shutil.copytree(d, sdir / "runs" / d.name, dirs_exist_ok=True)
    return out
