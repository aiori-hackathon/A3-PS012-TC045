# Conventions (A3-PS012-TC045)

## Names
- Team code and repo: A3-PS012-TC045. Python package: resolverlens. Command: rlens.
- Docker network: rl-lab, 10.10.0.0/16, internal (no Internet). Container names start with rl-.
- Zones: canary.lab (canary zone), lab.test (baseline zone on some targets).

## Addresses
| Machine | Address |
|---|---|
| Canary server | 10.10.0.5 |
| Targets t01 to t20 | 10.10.0.11 to 10.10.0.30 |
| Control client | 10.10.1.10 |
| External probe client | 10.10.2.10 |

## Targets
t01-t05 open recursive, t06-t09 policy-refusing, t10-t13 authoritative-only,
t14-t16 forwarders, t17-t18 slow or rate-limited, t19-t20 broken or silent.

## Git
- One clone at ~/work/A3-PS012-TC045. Run `git-as aditya` or `git-as dinesh` before committing.
- Run `git-as status` to confirm who the next commit will be made as.
- Branches: <author>/phase-N-name. Merge to main with --no-ff, then tag (v0.N-phaseN).
- Commit style: feat(lab): ..., fix(probe): ..., docs: ..., test: ..., chore: ...
- Pairing: add a "Co-authored-by: Name <email>" line to the commit message.

## Safety
- No published ports, no privileged containers, no host networking.
- NET_ADMIN only on containers that impair traffic. Config mounted read-only.
- The tool only sends to addresses in lab/targets.yaml.
