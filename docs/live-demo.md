# Live Demo Guide for Evaluators

This guide explains how the automated GitHub Actions **Live Demo** works, where to view its outputs directly in your browser, how to trigger a fresh run, and how to download the complete evidence artifacts.

## 1. Quick Access: Viewing a Finished Run (Zero Setup)
You do not need to clone the repository or run Docker locally to evaluate ResolverLens. The complete pipeline runs automatically on GitHub's hosted runners.

1. Open the [Actions &rarr; Live demo workflow](https://github.com/aiori-hackathon/A3-PS012-TC045/actions/workflows/demo.yml).
2. Click on the latest workflow run (marked with a green checkmark).
3. Scroll down to the **Summary** section at the bottom of the page.
   - The full evaluation summary is rendered right there in Markdown.
   - You can review the **Main lab** (20 servers) confusion matrix, metrics, and per-server verdicts.
   - You can review the **Challenge set** (6 deceptive servers) single-flag comparison (ResolverLens vs RA-flag vs RA+AA checks).

## 2. Triggering a Fresh Run (1-Click)
Evaluators can re-run the entire live demo on a fresh disposable runner at any time:

1. Go to [Actions &rarr; Live demo](https://github.com/aiori-hackathon/A3-PS012-TC045/actions/workflows/demo.yml).
2. Click the **Run workflow** dropdown on the right side of the screen.
3. Select branch: `main` and click the green **Run workflow** button.
4. The workflow takes about 2 to 3 minutes to build the lab, execute probes, classify, score, export reports, and verify replays.

## 3. What the Demo Does (Step-by-Step)
On an `ubuntu-24.04` runner, the workflow:
1. **Loads kernel module**: `sudo modprobe sch_netem` to support traffic delay simulation for slow servers.
2. **Builds the environment**: Sets up Python 3.12, creates `.venv`, builds container images (`rl-dns:1` and `rl-client:1`).
3. **Installs PDF renderer**: Installs `weasyprint` so that PDF reports are exported alongside HTML.
4. **Starts the lab**: Boots 23 containers on the isolated `rl-lab` network (`make lab-up`).
5. **Starts the challenge set**: Boots the 6 deceptive servers (`make challenge-up`).
6. **Preflight self-test**: Validates configuration, scope guard, disk space, and tests a canary query round-trip through `rl-t01`.
7. **Verifies targets from vantage points**: Runs `verify.py` from `rl-ext` (external outsider) and `rl-ctl` (internal control client).
8. **Probes and scores the main lab**: Evaluates all 20 targets, generates `report.html`, `report.pdf`, `summary.md`, and `scores.json`.
9. **Probes and scores the challenge set**: Evaluates the 6 deceptive targets against single-flag baselines.
10. **Replays evidence**: Cryptographically verifies the evidence files (`evidence.jsonl`, `audit.log`) against manifest SHA256 hashes and re-derives verdicts byte-for-byte.

## 4. Downloading the Complete Evidence (`demo-results`)
At the bottom of any finished workflow run page, find the **Artifacts** section:
- Click **demo-results** to download the ZIP archive.

### Contents of `demo-results.zip`:
The archive contains the outputs of both runs (`demo-main-<timestamp>/` and `demo-chal-<timestamp>/`):
- `report.html` & `report.pdf`: The full 9-section A4 exposure assessment report (confusion matrix, remediation instructions, compliance data, per-probe evidence).
- `summary.md`: Concise Markdown summary with the verdict table and single-flag comparisons.
- `scores.json`: Machine-readable metrics (accuracy, coverage, precision, recall, F1 per class, root cause analysis for misclassifications).
- `verdicts.csv` & `verdicts.jsonl`: Final classified labels and reasons (`CONFLICT`, `TIMEOUT`, etc.) per server.
- `evidence.jsonl`: Complete, raw probe-by-probe telemetry (every DNS query, response flags, status, RTT, and canary log hits).
- `manifest.json`: Cryptographic integrity manifest (run metadata, configuration digest, and SHA256 hashes of all evidence files).
- `audit.log`: Chronological log of every outbound packet written before it left the probe client.

## 5. Running the Demo Locally
If you prefer running the evaluation on your local machine:
```bash
git clone https://github.com/aiori-hackathon/A3-PS012-TC045.git
cd A3-PS012-TC045
sudo modprobe sch_netem
make bootstrap    # builds Python venv and Docker images
make demo         # runs lab, preflight, checks, assessment, reports, and replay
make demo-down    # tears down all containers
```
Results will be saved in `results/demo-main-<timestamp>/` and `results/demo-chal-<timestamp>/`.
