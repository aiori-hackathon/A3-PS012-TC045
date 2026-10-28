# The challenge set: an evaluation that can fail (Phase 5)

The main lab (`lab/targets.yaml`, 20 servers) is built and labelled by us, so a perfect score there shows that the
pipeline is consistent, not that the method is good. The challenge set (`lab/challenge.yaml`, 6 servers) contains servers
built to **fool a single-flag check**, and the report scores ResolverLens against two simpler methods on the same evidence.

Each assessment run covers at most 20 servers: the main lab is one run (20), the challenge set is a separate run (6).

## The servers

| Server | Software | What it does | Truth | Why it is hard |
|---|---|---|---|---|
| c01 | dnsmasq | Sets RA, answers names under canary.lab from local data (AA set), never contacts the canary server | not recursive | Looks like a resolver in the flags |
| c02 | dnsmasq | Answers every name, including the baseline, with the marker address | not recursive | Same, for every name |
| c03 | BIND | Recursion configured on but denied to everyone: REFUSED | Refused | Configured for recursion yet refuses |
| c04 | dnsmasq | Two-hop forwarder: c04 to t14 to t01 | Recursive | The canary only ever sees t01, never c04 |
| c05 | Unbound | Slow but within our timeout (200 ms each way; the first lookup takes about 1 s) | Recursive | Must not be mistaken for a timeout |
| c06 | BIND | Response-policy (DNS firewall) resolver: NOERROR, RA set, AA clear, marker answer, no canary contact | not recursive | By flags alone it is identical to a real open resolver |

## The methods compared (question: does the server provide recursion to the external client?)

| Method | Rule |
|---|---|
| ResolverLens | The four rules over 3 attempts; recursion needs RA, the marker answer **and** a canary log hit |
| RA-flag check | First RD=1 reply is NOERROR with RA set (what Nmap's `dns-recursion` script reads) |
| RA + AA check | The same, plus AA clear and an answer |

Result in the sandbox (same server software, no `tc netem`): ResolverLens 6/6, RA + AA check 5/6 (fooled by c06),
RA-flag check 3/6 (fooled by c01, c02 and c06). On the 20-server main lab all three methods are expected to agree.
The Docker numbers are recorded in `docs/phase-5.md`.

The liars c01 and c02 also give themselves away through the AA flag. The c06 sinkhole does not: only the canary log
shows that it never looked anything up.

## Commands

    make challenge-up                      # start c01 to c06 on the existing lab network (run make lab-up first)
    make challenge-check                   # confirm each server behaves as designed
    make challenge RUN=chal-a PDF=1       # probe, classify and report the challenge set
    make challenge-down

## Limits (what the tool cannot do)

- **A lossy open resolver becomes Inconclusive.** The three canary attempts must agree. One lost attempt gives CONFLICT, so a truly open resolver on a bad link is reported as Inconclusive, not Recursive. This costs coverage, not correctness. More attempts (up to 5 in `config.yaml`) reduce it.
- **The canary zone must be reachable from the target's resolution path.** In our lab the recursive servers are configured to find the canary server. In a network where we cannot arrange that, recursion cannot be proven this way.
- **A slow link makes the first lookup of a zone several times slower than the next ones.** On c05 the first query took about 977 ms against about 400 ms afterwards. At 500 ms of delay the first query exceeded our 2 s timeout, one attempt disagreed with the other two, and the verdict was Inconclusive. On a slow network, raise `timeout_s` in `config.yaml`.
- **A resolver that serves recursion but refuses our external vantage looks Refused.** That is the right answer for the external client; the control client exists to show the server can recurse for others.
- **We built both the servers and the answer key.** The challenge set widens the test but does not make it independent. A fully independent test needs servers configured by someone else.
- **IPv4 and the four named DNS server programs only.** IPv6, other server software and DNSSEC-validating resolvers were not tested.
