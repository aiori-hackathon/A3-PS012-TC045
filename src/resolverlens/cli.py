"""Command line entry point: rlens probe | rlens --version."""
import argparse

from resolverlens import __version__
from resolverlens.classify import classify_run
from resolverlens.compare import compare, expected_labels
from resolverlens.replay import replay
from resolverlens.report import build_report
from resolverlens.stability import stability
from resolverlens.preflight import run_preflight
from resolverlens.runner import run_probe


def main(argv=None):
    parser = argparse.ArgumentParser(prog="rlens", description="ResolverLens: authorised DNS resolver exposure assessment")
    parser.add_argument("--version", action="version", version=f"rlens {__version__}")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("probe", help="send the baseline and canary queries to the lab servers and record evidence")
    p.add_argument("--config", default="config/config.yaml")
    p.add_argument("--only", help="comma-separated target ids, e.g. t01,t06")
    p.add_argument("--dry-run", action="store_true", help="print the plan and send nothing")
    p.add_argument("--run-id", help="name of the run folder (default: UTC timestamp)")
    p.add_argument("--no-preflight", action="store_true", help="skip the preflight checks (not recommended)")
    pf = sub.add_parser("preflight", help="check the setup, including one canary round trip, and send nothing else")
    pf.add_argument("--config", default="config/config.yaml")
    rp = sub.add_parser("replay", help="check a stored run is intact and re-derive its verdicts from the evidence")
    rp.add_argument("run_dir")
    rp.add_argument("--targets")
    st = sub.add_parser("stability", help="compare the verdicts of several runs")
    st.add_argument("run_dirs", nargs="+")
    st.add_argument("--targets")
    c = sub.add_parser("classify", help="turn the evidence of a run into one verdict per target")
    c.add_argument("run_dir", help="run folder, e.g. results/phase2-first")
    c.add_argument("--targets", help="targets file (default: the one recorded in the run)")
    c.add_argument("--check", action="store_true", help="compare verdicts with the expected labels (exit 1 on any mismatch)")
    r = sub.add_parser("report", help="classify a run and write report.html, summary.md and scores.json")
    r.add_argument("run_dir")
    r.add_argument("--targets", help="targets file (default: the one recorded in the run)")
    r.add_argument("--pdf", action="store_true", help="also write report.pdf (needs the optional weasyprint package)")
    args = parser.parse_args(argv)
    if args.command == "report":
        return _report(args)
    if args.command == "preflight":
        return 0 if run_preflight(args.config) else 4
    if args.command == "replay":
        return _replay(args)
    if args.command == "stability":
        return _stability(args)
    if args.command == "classify":
        return _classify(args)
    if args.command == "probe":
        return run_probe(args.config, only=args.only, dry_run=args.dry_run, run_id=args.run_id, preflight=not args.no_preflight)
    parser.print_help()
    return 0


def _replay(args):
    try:
        res = replay(args.run_dir, args.targets)
    except (OSError, KeyError, ValueError) as e:
        print(f"error: {e}")
        return 2
    for c in res["checks"]:
        print(f"  {'PASS' if c['ok'] else 'FAIL'}  {c['check']}" + (f"  ({c['note']})" if c["note"] else ""))
    print("REPLAY OK: the run is intact and its verdicts reproduce exactly" if res["ok"] else "REPLAY FAILED")
    return 0 if res["ok"] else 1


def _stability(args):
    try:
        res = stability(args.run_dirs, args.targets)
    except (OSError, KeyError, ValueError) as e:
        print(f"error: {e}")
        return 2
    for r in res["rows"]:
        vals = " | ".join("missing" if v is None else f"{v[0]}{'/' + v[1] if v[1] else ''}" for v in r["values"])
        tag = "UNSTABLE" if not r["stable"] else ("STABLE*" if r["reason_varies"] else "STABLE ")
        print(f"{r['target_id']:<4} {tag:<8} {vals}")
    n = len(res["rows"])
    print(f"{n - len(res['unstable'])}/{n} servers keep the same label across {len(res['runs'])} runs ({', '.join(res['runs'])})")
    if res["reason_varies"]:
        print(f"* the reason code varies for {', '.join(res['reason_varies'])} while the label stays the same (expected for rate-limited servers)")
    return 0 if res["stable"] else 1


def _report(args):
    try:
        out = build_report(args.run_dir, args.targets, args.pdf)
    except (OSError, KeyError, ValueError) as e:
        print(f"error: {e}")
        return 2
    sm = out["summary_numbers"]
    for k in ("html", "summary", "scores", "pdf"):
        if k in out:
            print(f"wrote {out[k]}")
    if "pdf_error" in out:
        print(f"PDF not written ({out['pdf_error']}). Open report.html in a browser and print to PDF instead.")
    print(f"{sm['correct']}/{sm['total']} verdicts match the expected labels; coverage {sm['coverage']:.0%}")
    return 0 if sm["correct"] == sm["total"] else 1


def _classify(args):
    import json
    from pathlib import Path
    try:
        verdicts = classify_run(args.run_dir, args.targets)
    except (OSError, KeyError, ValueError) as e:
        print(f"error: {e}")
        return 2
    exp = None
    if args.check:
        tf = args.targets or json.loads((Path(args.run_dir) / "manifest.json").read_text())["config"]["targets_file"]
        exp = {r["target_id"]: r for r in compare(verdicts, expected_labels(tf))}
    for v in verdicts:
        line = f"{v.target_id:<4} {v.software:<8} {v.label:<19} {(v.reason or '-'):<9} {v.rule}  hits={v.canary_hits}/{len(v.attempts)}"
        if exp:
            r = exp[v.target_id]
            line += f"  expected={r['expected']:<19} {'OK' if r['match'] else 'MISMATCH'}"
        print(line)
    print(f"wrote {args.run_dir}/verdicts.csv and verdicts.jsonl")
    if exp:
        ok = sum(1 for r in exp.values() if r["match"])
        print(f"{ok}/{len(exp)} verdicts match the expected labels")
        return 0 if ok == len(exp) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
