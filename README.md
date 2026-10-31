<!-- resolverlens-readme -->
# ResolverLens: Authorised DNS Resolver Exposure Assessment

**Team A3-PS012-TC045 · AIORI Hackathon 3 · PS-012 (Cybersecurity)**

[![tests](https://github.com/aiori-hackathon/A3-PS012-TC045/actions/workflows/ci.yml/badge.svg)](https://github.com/aiori-hackathon/A3-PS012-TC045/actions/workflows/ci.yml)
[![live demo](https://github.com/aiori-hackathon/A3-PS012-TC045/actions/workflows/demo.yml/badge.svg)](https://github.com/aiori-hackathon/A3-PS012-TC045/actions/workflows/demo.yml)

ResolverLens tests whether authorised lab DNS servers provide recursion to an external client, and labels each one **Recursive**, **Authoritative-only**, **Refused** or **Inconclusive**. Its proof of recursion is not a flag a server sets: the tool asks for a unique made-up name that only our own *canary server* can answer, and the server counts as recursive only if the canary server's log shows that it looked the name up. Every verdict is scored against seeded ground truth, rate-limited, reproducible, and explained in a report.

## Results (measured in the Docker lab)

| Test | Result |
|---|---|
| Main lab, 20 seeded servers | 20/20 verdicts match the expected labels; coverage 80% (4 servers are unusable by design and are reported Inconclusive) |
| Three repeat runs | The same label for all 20 servers every time; replay re-derives the verdicts byte for byte |
| Challenge set, 6 servers built to fool a single-flag check | ResolverLens 6/6; RA + AA check 5/6; RA-flag check 3/6 |
| Main lab, single-flag checks | RA-flag check 20/20; RA + AA check 19/20 (it missed t05: dnsmasq passes through the AA flag of the server it asked) |
| Safety | A stop file ends a run cleanly; a reply-size tripwire ends a run after the first oversized reply (`docs/safety-tests.md`) |

Read these honestly: we built both the servers and the answer key, so the main-lab score shows the pipeline is consistent, not that the method is general. The challenge set widens the test, and the limits are written down in `docs/challenge.md`.

## Quick start

Needs Linux with Docker Engine and Compose v2, Python 3.10+ and `make`, about 1.5 GB of free RAM, and the `sch_netem` kernel module for the two servers that are slowed on purpose.

    git clone https://github.com/aiori-hackathon/A3-PS012-TC045.git && cd A3-PS012-TC045
    sudo modprobe sch_netem        # once per boot
    make bootstrap                 # first time only: Python environment and Docker images (several minutes)
    make demo                      # start the lab, check it, assess both server sets, write reports, replay the evidence
    make demo-down                 # stop everything

Reports are written to `results/demo-main-<time>/` and `results/demo-chal-<time>/` (`report.html`, `summary.md`, `scores.json`, and `report.pdf` if you run `.venv/bin/pip install weasyprint` first).

| Command | What it does |
|---|---|
| `make lab-up` / `make challenge-up` | Start the 20-server lab / the 6 deceptive servers |
| `make lab-check` / `make challenge-check` | Confirm every server behaves as designed |
| `make preflight` | Self-test before a run, including one canary round trip |
| `make probe-dry` | Show the plan; send nothing |
| `make assess RUN=name PDF=1` | Probe, classify, score and write the report |
| `make challenge RUN=name PDF=1` | The same for the deceptive set, with the single-flag comparison |
| `make replay RUN=name` | Check a stored run is intact and its verdicts reproduce |
| `make repeat PREFIX=stab N=3` | Run three times and compare the labels |
| `make fault-demo` | Break one server on purpose and show the false-result analysis |
| `make test` | Unit tests |

## How it works

    external probe client --(baseline query, RD off)------------> target server
    external probe client --(canary query "rl-<hash>.canary.lab", RD on)--> target server --(asks)--> CANARY SERVER (logs the name)
    ResolverLens reads: reply flags, answer, and the canary server's log  -->  rules  -->  verdict  -->  report

A control client inside the allowed address range shows that servers which refuse the outsider can still serve their own users. The pseudocode is in [`docs/pseudocode.md`](docs/pseudocode.md) and the architecture in `docs/tool.md` and `docs/lab.md`.

## How this answers PS-012

| Key requirement | Where |
|---|---|
| Assess up to 20 authorised servers | Scope guard and hard cap: `src/resolverlens/scope.py`, `config.py` |
| Focus only on recursion exposure | One question per server; out-of-scope list in `docs/classifier.md` |
| Controlled test zone and separate client vantage | `canary.lab` zone, outsider client `rl-ext`, control client `rl-ctl` (`lab/`) |
| Recursive, Authoritative-only, Refused, Inconclusive | `src/resolverlens/classify.py`, `docs/classifier.md` |
| Compare with seeded ground truth | `lab/targets.yaml`, `src/resolverlens/compare.py` |
| Rate controls, bounded and reproducible | Token buckets: `ratelimit.py`, `config/config.yaml`; seeded names and jitter; replay and stability |
| No Internet-wide scanning, spoofing or amplification testing | Isolated lab network, allowlist, type A only, no spoofing option, reply-size tripwire |

| Expected outcome | Where |
|---|---|
| DNS resolver probe tool | `rlens probe` (`src/resolverlens/`) |
| Controlled labelled test cases | `lab/targets.yaml` (20 servers), `lab/challenge.yaml` (6 servers) |
| Configurable rate-control mechanism | `rate:` in `config/config.yaml` |
| Response classification and ground-truth comparison | `rlens classify --check`, report section 3 |
| DNS exposure assessment report | `rlens report`; examples in `docs/examples/*/report.pdf` |
| False and inconclusive result analysis | Report section 4; `make fault-demo` |
| Final technical demonstration and report | Live demo below; `docs/mentor-demo.md`; `docs/pseudocode.md` |

## Safety and ethics

The lab runs on a Docker network with no Internet access and publishes no ports. The tool sends only type A queries to at most 20 allowlisted private addresses from its own address (it has no spoofing option), under token-bucket limits (default 1 query/s per server and 5/s overall, with hard caps), and stops on a stop file or when a reply is unusually large. Our lab contains open resolvers on purpose, so it must never be exposed to the Internet. That is why the live demo runs on a disposable GitHub runner.

## Live demo

The **Live demo** workflow builds the lab from a clean checkout on a GitHub runner, assesses both server sets, replays the evidence and shows the results on the run page:
[Actions, Live demo](https://github.com/aiori-hackathon/A3-PS012-TC045/actions/workflows/demo.yml). Open a finished run for the summary tables, or use "Run workflow". Reports and evidence are downloadable as the artifact `demo-results`.

Recorded run evidence: [`docs/phase-7.md`](docs/phase-7.md) · Walkthrough script: [`docs/mentor-demo.md`](docs/mentor-demo.md)
<!-- Demo video: https://www.youtube.com/watch?v=YOUR_DEMO_VIDEO_ID -->

## Repository map

| Path | Content |
|---|---|
| `src/resolverlens/` | The tool: probe, rate control, scope guard, canary log reader, classifier, scoring, report, replay, stability, preflight |
| `lab/` | Lab definition (`targets.yaml`, `challenge.yaml`), generator, generated Docker Compose files and server configs, images, checks |
| `config/` | Tool settings |
| `tests/` | 139 unit tests |
| `docs/` | Design notes, evidence per phase, real example runs; start at [`docs/index.md`](docs/index.md) |
| `.github/workflows/` | Unit tests on every push; the live demo |
| `results/` | Output of runs (not committed) |

## Team

| Name | Role |
|---|---|
| Aditya V J | Team lead; probe tool, classifier, preflight, replay |
| Dinesh Babu R S | Lab, challenge servers, scoring and report, CI |
| Dr. Gokulapriya R (faculty) | Guidance and review |

The work was done in phases, on branches, and each phase was reviewed and merged by the other student (see the git history and tags `v0.0-phase0` to `v0.7-phase7`).

## Limits

- The lab and the answer key are ours; the challenge set is wider but not independent.
- A very lossy open resolver is reported Inconclusive, not Recursive: the three canary attempts must agree.
- The canary zone must be reachable from the target's resolution path.
- A server that serves recursion but refuses our external vantage is reported Refused, which is correct for that client.
- IPv4 only, and only BIND, Unbound, dnsmasq and NSD were tested.

## References

RFC 5358 (BCP 140), RFC 1035, RFC 6891, RFC 7766, RFC 8906 (BCP 231); Kührer et al., "Going Wild: Large-Scale Classification of Open DNS Resolvers", IMC 2015; Nmap `dns-recursion`. Full list in `docs/tool.md` and the presentation.

---

# Level 1 submission notes (kept as submitted)

# AIORI-3-HACKATHON-PROJECTS
This repository will contain the code and resources for the AIORI-3 hackathon that will be developed during the AIORI-3

# A3-PS012-TC045: ResolverLens

**Authorised DNS Resolver Exposure Assessment** | AIORI Hackathon 3 | Problem Statement PS-12 (Cybersecurity)

ResolverLens is a probe tool, being built for the AIORI Hackathon 3, that checks whether authorised lab DNS servers offer recursion to an external client. It labels each server **Recursive**, **Authoritative-only**, **Refused** or **Inconclusive**, and scores every label against known expected results.

## Team Introduction Video

[Watch the team introduction video on YouTube](https://youtu.be/QG4MiJL1zHA)

youtube: https://youtu.be/QG4MiJL1zHA

## The Problem

Open recursive DNS resolvers answer queries from anyone on the Internet. Attackers abuse them as reflectors in DDoS amplification attacks: a small spoofed query triggers a much larger reply aimed at a victim. [RFC 5358 (BCP 140)](https://www.rfc-editor.org/rfc/rfc5358.html) tells operators to offer recursion only to their intended clients.

Operators need a precise, repeatable way to test this. Checking one flag, such as the RA bit, is weak evidence, and a timeout is ambiguous. The testing itself must also be ethical: an authorised lab only, up to 20 servers, no spoofed traffic, no Internet-wide scanning, no amplification stress testing, and a bounded query rate.

## Our Approach

A flag only says what a server claims. Our own **canary server** shows what a server actually did.

1. The **external probe client** sends a **canary query**: a unique, made-up name in our own test zone.
2. If the **target server** recurses, it asks our canary server for that name, and the canary server logs it. That log entry is the **canary evidence**.
3. A **control client**, inside the allowed address range, shows that a server can recurse at all, so REFUSED means a real access rule and not a broken server.
4. Rules combine flags, result codes, the answer and the canary evidence into one class. Anything unclear is **Inconclusive**, with a reason code.
5. Each verdict is compared with the server's **expected label** in a confusion matrix.

### Key terms

| Term | Meaning |
| --- | --- |
| Target server | A lab DNS server we assess |
| Canary server | Our own DNS server for a test zone; logs every query |
| Canary query | Our probe for a unique made-up name in that zone |
| Canary evidence | That name appears in the canary log, so the target looked it up |
| External probe client | The outsider machine where our tool runs |
| Control client | A client inside the allowed range, used to prove a server can recurse |
| Expected label | The known correct answer (seeded ground truth) for each lab server |

### Response classes

| Class | What we expect to see |
| --- | --- |
| Recursive | RA set, no error, the marker answer, and canary evidence in the log |
| Authoritative-only | Own-zone answer with AA set, no answer for outside names, no canary evidence |
| Refused | REFUSED for both the in-zone and the out-of-zone query |
| Inconclusive | Anything else, with a reason: `TIMEOUT`, `SERVFAIL`, `TC_FAIL`, `CONFLICT` or `RATE_LIMITED` |

## Planned Features

- Seeded lab of 20 DNS servers (open recursive, policy-refusing, authoritative-only, forwarders, lossy or rate-limited, broken or silent) with known expected labels, built with Docker
- Canary server and unique canary names, so caching cannot hide the lookup
- Three attempts per target with a TCP retry; the attempts must agree
- Token-bucket rate control, per target and global, with a fixed seed so runs can be repeated
- Exposure assessment report with a confusion matrix, precision and recall per class, accuracy on decided cases, coverage, and analysis of false and inconclusive results

## Ethical Safeguards

- Hard allowlist of up to 20 authorised lab servers, checked before any packet is sent
- Real source address only: no spoofing
- Small queries only, no ANY queries
- Isolated lab with no Internet access; never aimed at public resolvers
- Stops if replies look unusually large; kill switch and an audit log of every query

## Project Status

In development for AIORI Hackathon 3. Planned timeline:

| Phase | Dates |
| --- | --- |
| Lab build | 14 to 18 Oct |
| Probe engine | 18 to 22 Oct |
| Classifier | 22 to 25 Oct |
| Report | 25 to 29 Oct |
| Go live: full run on all 20 targets, demo and final report | By 31 Oct |

## Documents

- Presentation: `A3-PS012-TC045_Presentation.pdf` (add the file to this repository)
- Problem statement: PS-12, Authorised DNS Resolver Exposure Assessment

## Team

| Name | Role | Contact |
| --- | --- | --- |
| Aditya V J | Team lead | aditya.vj@btech.christuniversity.in |
| Dinesh Babu R S | Lab and testing | dinesh.babu@btech.christuniversity.in |
| Dr. Gokulapriya R | Faculty mentor: guidance and review | r.gokulapriya@christuniversity.in |

Christ University | Team code: **A3-PS012-TC045**

## References

1. J. Damas, F. Neves. Preventing Use of Recursive Nameservers in Reflector Attacks. RFC 5358 (BCP 140), 2008.
2. P. Mockapetris. Domain Names: Implementation and Specification. RFC 1035, 1987.
3. J. Damas, M. Graff, P. Vixie. Extension Mechanisms for DNS (EDNS(0)). RFC 6891, 2013.
4. J. Dickinson et al. DNS Transport over TCP: Implementation Requirements. RFC 7766, 2016.
5. M. Andrews, R. Bellis. A Common Operational Problem in DNS Servers: Failure to Communicate. RFC 8906 (BCP 231), 2020.
6. M. Kührer, T. Hupperich, J. Bushart, C. Rossow, T. Holz. Going Wild: Large-Scale Classification of Open DNS Resolvers. ACM IMC, 2015.
7. Nmap Project. NSE script dns-recursion. https://nmap.org/nsedoc/scripts/dns-recursion.html
