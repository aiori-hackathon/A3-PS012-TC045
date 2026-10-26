# The classifier (Phase 3)

`rlens classify results/<run>` turns the evidence of a run into one verdict per target. It reads only the run's
`manifest.json` and `evidence.jsonl`, so the same evidence always gives the same verdicts (this is what replay will rely on).
Expected labels are read in one place only, `compare.py`, and only when `--check` is used.

## Rules (checked in order; the first match decides)

| Rule | Label | Condition (all canary attempts, normally 3) |
|---|---|---|
| R1 | Recursive | Every canary attempt is NOERROR with RA set, the marker answer (192.0.2.53), and a hit in the canary log |
| R2 | Refused | The baseline and every canary attempt are REFUSED, with no canary hit |
| R3 | Authoritative-only | The baseline is NOERROR with AA and a non-empty answer; every canary attempt got a reply with no answer, no RA and no canary hit |
| R4 | Inconclusive | Anything else, with one reason code |

## Reason codes for Inconclusive

| Code | Meaning | Example in the lab |
|---|---|---|
| TIMEOUT | No reply to any canary attempt | t17 (slow), t18 (rate-limited), t19 (silent), t20 (broken upstream) |
| SERVFAIL | Canary attempts ended in SERVFAIL (timeouts allowed) | a resolver whose upstream fails quickly |
| TC_FAIL | A truncated reply could not be completed over TCP | |
| CONFLICT | The evidence disagrees, for example one lost attempt among good ones, or a marker answer without a canary hit | |
| ERROR | A local network error stopped every attempt | |
| NO_DATA | Evidence is missing, for example the run was stopped early | |

The first four are on the presentation slides. ERROR and NO_DATA are edge cases for broken runs.

## Decisions worth knowing

- A canary hit without a reply is not recursion. The slow server t17 does contact the canary, but its reply arrives after our timeout, so the verdict is Inconclusive (TIMEOUT) and `late_hits` records it.
- Rule 1 comes first, so an open resolver whose baseline query is REFUSED (dnsmasq) is still Recursive.
- Attempts must agree. One lost attempt among good ones gives CONFLICT, because a wrong label is worse than an honest Inconclusive.
- A forwarder is Recursive; its canary hits come from the upstream server's address, which the verdict records in `canary_sources`.

## Outputs

`verdicts.csv` and `verdicts.jsonl` in the run folder: target, address, software, label, reason, rule, attempt statuses,
canary hits, canary sources, late hits, a one-line explanation, and the evidence sequence numbers behind the verdict.

## Commands

    make classify RUN=phase2-first        # writes verdicts and compares them with the expected labels
    .venv/bin/python -m resolverlens.cli classify results/phase2-first --check

Exit code 0 means every verdict matches its expected label, 1 means at least one does not.

## Verification status

Checked: 76 unit tests, including every rule, every reason code, and the committed Docker run
(`docs/examples/phase2-first`) classified 20 of 20 against the expected labels. Phase 3 is complete when the same
holds for a fresh run in the Docker lab.
