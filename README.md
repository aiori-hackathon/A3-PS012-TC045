# AIORI-3-HACKATHON-PROJECTS
This repository will contain the code and resources for the AIORI-3 hackathon that will be developed during the AIORI-3

# A3-PS012-TC045: ResolverLens

**Authorised DNS Resolver Exposure Assessment** | AIORI Hackathon 3 | Problem Statement PS-12 (Cybersecurity)

ResolverLens is a probe tool, being built for the AIORI Hackathon 3, that checks whether authorised lab DNS servers offer recursion to an external client. It labels each server **Recursive**, **Authoritative-only**, **Refused** or **Inconclusive**, and scores every label against known expected results.

## Team Introduction Video

[Watch the team introduction video on YouTube](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)


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
