# Phase 5: an evaluation that can fail
Date: 2026-10-28T14:23:51+05:30   Run by: Aditya V J

## Unit tests
```
........................................................................ [ 62%]
............................................                             [100%]
116 passed in 4.48s
```

## Main lab (20 servers): all methods

## Comparison with single-flag checks (does the server provide recursion?)

| Method | Correct | False exposure | Missed exposure | Called wrongly |
|---|---|---|---|---|
| ResolverLens | 20/20 | 0 | 0 | none |
| RA-flag check | 20/20 | 0 | 0 | none |
| RA + AA check | 19/20 | 0 | 1 | t05 |

## Verdicts

## Challenge set (6 deceptive servers)

# Assessment summary: run chal-a

- Servers assessed: **6**; providing recursion to the external client: **2** (c04, c05)
- Accuracy 100.0% (6/6); accuracy on decided cases 100.0%; coverage 50.0%
- Wrong decisions: 0; correct abstentions: 3

## Confusion matrix (rows expected, columns reported)

| Expected \ Reported | Recursive | Authoritative-only | Refused | Inconclusive |
|---|---|---|---|---|
| Recursive | 2 | 0 | 0 | 0 |
| Authoritative-only | 0 | 0 | 0 | 0 |
| Refused | 0 | 0 | 1 | 0 |
| Inconclusive | 0 | 0 | 0 | 3 |

## Comparison with single-flag checks (does the server provide recursion?)

| Method | Correct | False exposure | Missed exposure | Called wrongly |
|---|---|---|---|---|
| ResolverLens | 6/6 | 0 | 0 | none |
| RA-flag check | 3/6 | 3 | 0 | c01, c02, c06 |
| RA + AA check | 5/6 | 1 | 0 | c06 |

## Verdicts

| Server | Software | Verdict | Reason | Expected | Match |
|---|---|---|---|---|---|
| c01 | dnsmasq | Inconclusive | CONFLICT | Inconclusive | yes |
| c02 | dnsmasq | Inconclusive | CONFLICT | Inconclusive | yes |
| c03 | bind | Refused | - | Refused | yes |
| c04 | dnsmasq | Recursive | - | Recursive | yes |
| c05 | unbound | Recursive | - | Recursive | yes |
| c06 | bind | Inconclusive | CONFLICT | Inconclusive | yes |
