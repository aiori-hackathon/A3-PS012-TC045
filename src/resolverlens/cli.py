"""Command line entry point: rlens probe | rlens --version."""
import argparse

from resolverlens import __version__
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
    args = parser.parse_args(argv)
    if args.command == "probe":
        return run_probe(args.config, only=args.only, dry_run=args.dry_run, run_id=args.run_id)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
