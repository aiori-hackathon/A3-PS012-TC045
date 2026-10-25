# The ResolverLens tool, Phase 2: probe and evidence

`rlens probe` sends a baseline query and three canary queries to each lab server, one server at a time,
and records everything it sees. It does not decide any verdict yet: classification is Phase 3.

## Modules and the architecture slide

| Architecture component | File | What it does |
|---|---|---|
| Scope Guard | `src/resolverlens/scope.py` | Allowlist from `lab/targets.yaml` (max 20, private subnet only). Any other address raises ScopeError before a packet is sent. |
| Rate Controller | `src/resolverlens/ratelimit.py` | One token bucket per target and one global bucket; seeded jitter. A query needs a token from both. |
| Probe Engine | `src/resolverlens/probe.py` | Builds type-A queries (never ANY), sends over UDP, retries over TCP when the reply is truncated, checks the reply-size tripwire. |
| Evidence Collector | `src/resolverlens/canary.py`, `evidence.py` | Reads the canary server's query log; writes `evidence.jsonl`, `audit.log` and `manifest.json`. |
| Names | `src/resolverlens/names.py` | Canary name = `rl-` + 10 hex digits of sha256(seed, run id, target, attempt) + `.canary.lab`. Fresh for every attempt, repeatable from the seed. |
| Settings | `src/resolverlens/config.py`, `config/config.yaml` | Validated settings. Hard caps (20 targets, 20 queries/s overall, 5 queries/s per target) cannot be raised from the file. |
| Run control | `src/resolverlens/runner.py`, `cli.py` | Plan, dry run, run folder, stop file, exit codes. |

## What one run produces: `results/<run id>/`

| File | Content |
|---|---|
| `evidence.jsonl` | One JSON line per probe: target, phase (baseline or canary), attempt, query name, RD flag, transport, status (RCODE name, TIMEOUT, TC_FAIL or ERROR), flags (aa, tc, rd, ra), answers, round-trip time, query and reply sizes, canary hit and the source addresses that asked the canary server |
| `audit.log` | One line per query, written before the query is sent |
| `manifest.json` | Run id, seed, config digest (settings plus targets file), the target list without expected labels, counts, duration, and how the run ended |

The tool never reads the expected labels. Comparing verdicts with them happens in Phase 4.

## Commands

    make test               # unit tests on the host
    make probe-dry          # show the plan, send nothing
    make probe RUN=first    # real run from rl-ext against all 20 targets (about 1 to 3 minutes)
    docker exec rl-ext python3 -m resolverlens.cli probe --config config/config.yaml --only t01,t06

Exit codes: 0 completed, 2 configuration or scope error, 3 safety tripwire, 130 stopped by the user or by a `results/STOP` file.
To stop a run cleanly from another terminal, create the file `results/STOP`.

## Safety behaviour (all covered by tests)

- A target address that is not on the allowlist is refused before anything is sent.
- A reply larger than `max_reply_bytes`, or more than `max_ratio` times its query, ends the run after the reply is recorded.
- The first query of a repeated run with the same seed and run id uses the same names, so runs can be compared.
- A run folder is never overwritten.

## Notes for the classifier (Phase 3)

- Verdicts must come from `evidence.jsonl` alone, so that replay gives the same result.
- A canary hit with no reply is a TIMEOUT, not recursion (the slow server t17 does this in Docker).
- Baseline `AA` counts only with status NOERROR and a non-empty answer.
- A baseline of REFUSED together with REFUSED canary queries is the Refused rule; a baseline answer with AA followed by REFUSED canary queries is Authoritative-only.

## Verification status

Checked: 51 unit tests; one full run against the sandbox copy of the lab (all 20 servers, 80 probes, rate limits
respected, tripwire and stop file tested). Not yet checked: a run inside the Docker lab. Phase 2 is complete when
`make probe` finishes in Docker and its run folder has been inspected.
