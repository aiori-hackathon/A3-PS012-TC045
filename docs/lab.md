# Lab design (Phase 1)

The lab is described once, in `lab/targets.yaml` (input D1). `lab/generate.py` turns it into
`lab/generated/` (one Docker Compose file and one config folder per DNS server). Never edit
`lab/generated/` by hand: change `targets.yaml` or the templates in `generate.py` and run `make lab-gen`.

## Machines (23 containers on the isolated network rl-lab, 10.10.0.0/16, no Internet)

| Container | Address | Role |
|---|---|---|
| rl-canary | 10.10.0.5 | Canary server: authoritative for canary.lab, answers any name with 192.0.2.53, logs every query |
| rl-t01 to rl-t20 | 10.10.0.11 to 10.10.0.30 | Target servers under assessment |
| rl-ctl | 10.10.1.10 | Control client (inside the trusted range 10.10.1.0/24) |
| rl-ext | 10.10.2.10 | External probe client (the outsider; the tool runs here) |

## Target behaviours (expected label is the seeded ground truth)

| Targets | Software | Behaviour | How it is made | Expected label |
|---|---|---|---|---|
| t01, t02 | BIND | open recursive | recursion on, any client | Recursive |
| t03, t04 | Unbound | open recursive | access-control allow all | Recursive |
| t05 | dnsmasq | open recursive | default behaviour | Recursive |
| t06, t07 | BIND | policy-refusing | queries and recursion only for 10.10.1.0/24 | Refused |
| t08, t09 | Unbound | policy-refusing | refuse all, allow 10.10.1.0/24 | Refused |
| t10, t11 | BIND | authoritative-only | recursion off, hosts lab.test | Authoritative-only |
| t12, t13 | NSD | authoritative-only | hosts lab.test | Authoritative-only |
| t14 | dnsmasq | forwarder | forwards to t01 | Recursive |
| t15 | Unbound | forwarder | forwards to t03 | Recursive |
| t16 | BIND | forwarder | forwards to t05 | Recursive |
| t17 | Unbound | slow | tc netem delay 3000 ms (longer than our 2 s timeout) | Inconclusive |
| t18 | BIND | rate-limited | iptables: 1 DNS packet per minute accepted | Inconclusive |
| t19 | dnsmasq | silent | iptables drops DNS from 10.10.2.10 only | Inconclusive |
| t20 | BIND | broken upstream | forwards to 10.10.0.250, which does not exist | Inconclusive |

Recursive targets reach the canary server through a stub or forward rule for canary.lab, so the canary
log records which source asked for each unique name.

## Running it

    make lab-gen && make lab-build && make lab-up
    make lab-check        # both vantage points, exit code 0 only if every checked target matches
    make lab-proof        # writes docs/phase-1.md
    make lab-down

`rl-canary-logs` (a Docker volume) holds the canary query log. The clients mount it read-only at /canary-logs.

## Notes for the classifier (Phase 3)

- A reply that arrives after the tool's timeout is a timeout. t17 still contacts the canary server, so a
  canary hit without a reply must never count as recursion.
- Unbound answers NXDOMAIN with the AA flag for names under .test. The baseline check therefore needs
  NOERROR, AA and a non-empty answer, not AA alone.
- An authoritative-only verdict needs a reply (REFUSED or empty) to the canary query. A timeout is Inconclusive.

## Verification status

Checked in a sandbox (Ubuntu 24.04, same BIND, Unbound, dnsmasq and NSD packages as the image) with the
generated configs: all 20 servers behave as listed from both vantage points, except t17 (needs tc netem).
Not yet checked: the Docker build, the Compose file, and tc netem. Phase 1 is only complete when
`make lab-check` passes in Docker and `docs/phase-1.md` has been committed.
