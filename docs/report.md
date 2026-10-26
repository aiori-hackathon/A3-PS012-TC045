# Scoring and the exposure report (Phase 4)

`rlens report results/<run>` classifies a run (Phase 3), compares the verdicts with the expected labels, and writes
four files into the run folder:

| File | Content |
|---|---|
| `report.html` | The exposure assessment report (9 sections, A4 print layout) |
| `report.pdf` | The same report as PDF (only with `--pdf` and the optional `weasyprint` package) |
| `summary.md` | A short Markdown summary that GitHub shows in the browser |
| `scores.json` | All numbers for other tools: summary, confusion matrix, per-class metrics, compliance figures, false results, inconclusive table |

## What the report contains

1. Summary: how many servers provide recursion to the external client, accuracy, coverage, a verdict bar.
2. Findings per server: verdict, reason, which address asked the canary server, the seeded ground truth, match.
3. Evaluation: confusion matrix (rows expected, columns reported), precision, recall and F1 per class, accuracy, accuracy on decided cases, coverage, wrong decisions, false and missed exposure, correct abstentions.
4. False and inconclusive result analysis: every false result with a likely cause (ACL, recursion enabled, impairment not effective, packet loss, upstream failure, mixed evidence); every Inconclusive result with its reason and what the server was seeded as.
5. Exposure and remediation: for each Recursive server, the configuration change that restricts recursion (RFC 5358), by software.
6. Safety and compliance, measured from the evidence: destinations, query types, peak query rates, largest reply and reply-to-query ratio, how the run ended.
7. Evidence per server: every query, status, flags, answer and canary log entry.
8. Reproducibility: seed, config digest, settings, how to re-run.
9. Method: the four rules.

The report is deterministic: the same run folder gives a byte-identical `report.html`.

## Definitions

- Accuracy on decided cases: correct verdicts among servers where the tool gave a decisive label (not Inconclusive).
- Coverage: the share of servers that received a decisive label.
- Wrong decision: a decisive verdict that disagrees with the expected label. This is the costly error; an honest Inconclusive is not counted as one.
- False exposure: reported Recursive when the server is not meant to be. Missed exposure: failed to report Recursive when it is.

## Commands

    make report RUN=phase4-a              # HTML, summary.md and scores.json
    make report RUN=phase4-a PDF=1        # also report.pdf (pip install -e ".[pdf]" first)
    make assess RUN=phase4-a PDF=1        # probe and report in one go
    make fault-demo                       # break rl-t18 on purpose, show the false-result analysis, restore it

Exit code of `rlens report`: 0 if every verdict matches its expected label, 1 otherwise.

## Fault injection (`make fault-demo`)

The report is only convincing if it can explain errors, so `lab/fault_demo.sh` creates one on purpose: it removes the
rate limit from rl-t18, which is meant to be unusable. The tool then reaches the canary server through t18 and reports it
as Recursive, a false exposure. The report lists it under false results with the cause "impairment not effective".
The script restarts rl-t18 afterwards, which re-applies the rate limit.

## Verification status

Checked: 96 unit tests; the report built from a run shaped like the Docker run (20 of 20 matching, coverage 80%);
the fault experiment on the sandbox lab (a removed impairment appears as a false exposure with the right cause);
PDF export in the sandbox. Phase 4 is complete when `make assess RUN=... PDF=1` and `make fault-demo` have run in Docker.
