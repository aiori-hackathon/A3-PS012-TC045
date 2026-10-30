# Hardening (Phase 6): preflight, replay, stability, safety tests

## Preflight (`rlens preflight`, and automatically at the start of `rlens probe`)

Checks the setup before anything is assessed. It sends exactly one query, to a reference server that must be recursive.

| Check | Why |
|---|---|
| Settings are valid and inside the hard safety caps | A mistyped rate cannot exceed 20 queries/s overall or 5/s per server |
| Allowlist loads: private lab subnet, at most 20 targets | The scope guard is armed before the first packet |
| Results folder is writable with free space | A run cannot die halfway for lack of disk |
| No stop file present | A stale `results/STOP` would stop the run at once |
| Canary query log is readable | The evidence source exists |
| Canary round trip through the reference server | A fresh name must come back with the marker answer **and** appear in the canary log, which proves the whole evidence path works before the assessment starts |

If any check fails, nothing is assessed (exit code 4). `--no-preflight` skips it. The reference server is set in `config.yaml` (`preflight.reference_target`).

## Replay (`rlens replay results/<run>`)

Proves that a stored run is intact and that its verdicts follow from its evidence.

- Evidence sequence numbers run 1..N without gaps; the record count matches the manifest; one audit line per probe.
- Every destination was on the allowlist; only type A queries were sent.
- `evidence.jsonl` and `audit.log` still have the sha256 recorded in the manifest when the run finished (runs made before hashing was added are checked through the next point only).
- The verdicts re-derived from `evidence.jsonl` alone are byte-identical to the stored `verdicts.jsonl` and `verdicts.csv`.

Edited evidence is caught twice: by the stored hash and by the verdict re-derivation (tested on a real run).

## Stability (`rlens stability results/a results/b ...`, or `make repeat PREFIX=stab N=3`)

Compares repeated runs. A server is **unstable** if its label changes between runs; exit code 1. A reason code that changes while the label stays the same
is shown as `STABLE*` and explained, not flagged. This happens for rate-limited servers such as t18, which accepts one packet per minute: whether the baseline or a
canary query gets that packet depends on timing, so the reason is TIMEOUT in one run and CONFLICT in another, and the label is Inconclusive in both.

## Safety tests (Docker)

`docs/safety-tests.md` records two tests run in the lab: the stop file ends a run cleanly between servers, and the reply-size tripwire ends a run after the first
oversized reply. The dry run sends nothing. All three are also covered by unit tests.

## CI feasibility

`.github/workflows/netem-check.yml` is a manual workflow that checks whether GitHub's runners support `tc netem` and `iptables` inside containers, which decides
whether the lab can run as a hosted demo.

## Verification status

Checked: 139 unit tests; preflight, two runs, stability and replay on a full run of the sandbox lab; replay against a tampered copy of a real run.
Phase 6 is complete when the same commands have been run in the Docker lab and the safety tests are recorded.
