# Mentor demonstration (about 7 minutes)

The lab must be running (`make lab-up`, `make challenge-up`). Everything below runs from the repository root.

| Min | Say | Run | Show |
|---|---|---|---|
| 0:00 | "Open resolvers are abused for DDoS amplification. We test whether lab servers give recursion to an outsider, safely and repeatably." | `make lab-ps` | 23 containers, no published ports |
| 0:45 | "Before every run the tool checks itself, including one real round trip through our own canary server." | `make preflight` | Seven PASS lines |
| 1:30 | "Nothing is sent in a dry run. This is the plan and the rate limits." | `make probe-dry` | 80 queries, 1/s per server, 5/s overall |
| 2:00 | "Now the real assessment of 20 servers: one baseline and three canary queries each, with fresh names." | `make assess RUN=demo PDF=1` | One line per server, about 70 s |
| 3:15 | "Our proof of recursion is not a flag. The server must ask OUR server for a name only we can answer, and our server logs it." | open `results/demo/report.pdf` | Findings table, confusion matrix, evidence card for t01 and a forwarder (t14: the canary sees its upstream) |
| 4:15 | "A single flag can be fooled. These six servers are built to do it." | `make challenge RUN=demo-chal PDF=1` | Section 10: ResolverLens 6/6, RA + AA check 5/6, RA-flag check 3/6 |
| 5:15 | "Every result can be checked afterwards." | `make replay RUN=demo` | REPLAY OK; then change one line of `results/demo/evidence.jsonl` and run it again: REPLAY FAILED |
| 6:00 | "And if something is wrong, the report explains it." | `make fault-demo` | t18 reported as a false exposure with the cause "impairment not effective" |
| 6:45 | Limits (below) | | |

## Say these limits yourself

- The lab and the answer key are ours. The challenge set widens the test but is not independent.
- A very lossy open resolver is reported Inconclusive, not Recursive (the attempts must agree).
- The canary zone must be reachable from the target's resolution path.
- IPv4 and four DNS server programs (BIND, Unbound, dnsmasq, NSD) only.

## If asked

- Why not just read the RA flag? Because a server can set it and answer without recursing (c01, c02, c06). The measured comparison is in section 10 of the report.
- Is it safe? Allowlist of at most 20 private lab addresses, no spoofing option, type A only, token buckets, a reply-size tripwire, a stop file, and no Internet access from the lab (`docs/safety-tests.md`).
- Can I run it myself? `make bootstrap` once, then `make demo`.
