# Phase 7: CI, live demo and final documentation

Date: 2026-10-31   Run by: Aditya V J & Dinesh Babu R S

## Unit tests (CI workflow & local)
139 passed


## GitHub Actions live demo (`demo.yml` on `main` commit `34416f2`)
- Runner: `ubuntu-24.04` (Python 3.12.15, `sch_netem` loaded, Docker images `rl-dns:1` and `rl-client:1` built from clean checkout)
- Preflight (`make preflight`): 6/6 checks `PASS` (including canary round-trip through `t01`)
- Main lab verification (`make lab-check-ext`): `20/20 checked targets match their expected profile, 0 failed`
- Challenge lab verification (`make challenge-check`): `6/6 checked targets match their expected profile, 0 failed`
- Main lab assessment (`demo-main-1031-1150`): 80 probes in 70.6 s -> `20/20 verdicts match the expected labels; coverage 80%` (`report.html`, `report.pdf`, `summary.md`, `scores.json`)
- Challenge assessment (`demo-chal-1031-1150`): 24 probes in 27.2 s -> `6/6 verdicts match the expected labels; coverage 50%` (`report.html`, `report.pdf`, `summary.md`, `scores.json`)
- Cryptographic replay (`make replay`):
  - `demo-main-1031-1150`: 9/9 checks `PASS` (`REPLAY OK: the run is intact and its verdicts reproduce exactly`)
  - `demo-chal-1031-1150`: 9/9 checks `PASS` (`REPLAY OK: the run is intact and its verdicts reproduce exactly`)
- Artifact uploaded: `demo-results` (18 files, 130,885 bytes, SHA256 `fbfe7aefbd0ce7df8ec6164567b26252df17c3865e511b9b2ca361427427cdba`)
