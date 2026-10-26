"""Command line entry point: rlens probe | rlens --version."""
import argparse

from resolverlens import __version__
from resolverlens.classify import classify_run
from resolverlens.compare import compare, expected_labels
from resolverlens.report import build_report
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
    if args.command == "classify":
        return _classify(args)
    if args.command == "probe":
        return run_probe(args.config, only=args.only, dry_run=args.dry_run, run_id=args.run_id)
    parser.print_help()
    return 0


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
