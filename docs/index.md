# Documentation Index

Welcome, evaluators. Here is the suggested roadmap based on what you are reviewing:
- **Live Demo & Artifacts**: [`live-demo.md`](live-demo.md) (How to view web results, 1-click runs, and artifact downloads)
- **Core Algorithms & Logic**: [`pseudocode.md`](pseudocode.md) and [`tool.md`](tool.md)
- **The Competitive Edge (Why Flag Checks Fail)**: [`challenge.md`](challenge.md) (6 deceptive servers, single-flag comparison)
- **Lab Architecture & Ground Truth**: [`lab.md`](lab.md) (23 containers, 20 seeded targets, two vantages)
- **Classifier & Reason Codes**: [`classifier.md`](classifier.md) (Rules R1–R4, reason codes)
- **Scoring & Fault Demo**: [`report.md`](report.md) (Confusion matrix, remediation, fault injection)
- **Safety & Tripwires**: [`safety-tests.md`](safety-tests.md) (Dry run, stop file, reply-size tripwire)
- **Hardening & Replay**: [`hardening.md`](hardening.md) (Preflight, cross-run stability, cryptographic replay)
- **Historical Evidence**: [`phase-0.md`](phase-0.md) through [`phase-7.md`](phase-7.md)

---

### Complete Document Map

| Document | Key Takeaway for Evaluators |
|---|---|
| [`live-demo.md`](live-demo.md) | How the GitHub Actions demo works and where to download artifacts |
| [`pseudocode.md`](pseudocode.md) | Structured pseudocode of probe, rate-limiting, and classification rules |
| [`challenge.md`](challenge.md) | The 6 deceptive servers proving ResolverLens 6/6 vs RA-flag 3/6 |
| [`tool.md`](tool.md) | Architecture of the probe engine, scope guard, and token buckets |
| [`lab.md`](lab.md) | 23 containers on isolated `rl-lab`, seeded ground truth, and vantage points |
| [`classifier.md`](classifier.md) | The 4-rule decision engine and reason codes (`CONFLICT`, `TIMEOUT`, etc.) |
| [`report.md`](report.md) | 9-section report, RFC 5358 remediation advice, and fault analysis |
| [`safety-tests.md`](safety-tests.md) | Proof of safety caps: dry run, stop file, and reply-size tripwire in Docker |
| [`hardening.md`](hardening.md) | Preflight self-checks, 3-run stability, and cryptographic replay verification |
| [`conventions.md`](conventions.md) | Pair-programming, network, and security conventions |
| [`README-level1.md`](README-level1.md) | Historical Level 1 submission document |
