"""Command line entry point for ResolverLens (filled in during Phase 2)."""
import argparse

from resolverlens import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="rlens",
        description="ResolverLens: authorised DNS resolver exposure assessment",
    )
    parser.add_argument("--version", action="version", version=f"rlens {__version__}")
    parser.parse_args(argv)
    print("ResolverLens: no command implemented yet (Phase 0 skeleton).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
