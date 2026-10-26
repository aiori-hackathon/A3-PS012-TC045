# Assessment summary: run fault-t18

- Servers assessed: **20**; providing recursion to the external client: **9** (t01, t02, t03, t04, t05, t14, t15, t16, t18)
- Accuracy 95.0% (19/20); accuracy on decided cases 94.1%; coverage 85.0%
- Wrong decisions: 1; correct abstentions: 3

## Confusion matrix (rows expected, columns reported)

| Expected \ Reported | Recursive | Authoritative-only | Refused | Inconclusive |
|---|---|---|---|---|
| Recursive | 8 | 0 | 0 | 0 |
| Authoritative-only | 0 | 4 | 0 | 0 |
| Refused | 0 | 0 | 4 | 0 |
| Inconclusive | 1 | 0 | 0 | 3 |

## Verdicts

| Server | Software | Verdict | Reason | Expected | Match |
|---|---|---|---|---|---|
| t01 | bind | Recursive | - | Recursive | yes |
| t02 | bind | Recursive | - | Recursive | yes |
| t03 | unbound | Recursive | - | Recursive | yes |
| t04 | unbound | Recursive | - | Recursive | yes |
| t05 | dnsmasq | Recursive | - | Recursive | yes |
| t06 | bind | Refused | - | Refused | yes |
| t07 | bind | Refused | - | Refused | yes |
| t08 | unbound | Refused | - | Refused | yes |
| t09 | unbound | Refused | - | Refused | yes |
| t10 | bind | Authoritative-only | - | Authoritative-only | yes |
| t11 | bind | Authoritative-only | - | Authoritative-only | yes |
| t12 | nsd | Authoritative-only | - | Authoritative-only | yes |
| t13 | nsd | Authoritative-only | - | Authoritative-only | yes |
| t14 | dnsmasq | Recursive | - | Recursive | yes |
| t15 | unbound | Recursive | - | Recursive | yes |
| t16 | bind | Recursive | - | Recursive | yes |
| t17 | unbound | Inconclusive | TIMEOUT | Inconclusive | yes |
| t18 | bind | Recursive | - | Inconclusive | NO |
| t19 | dnsmasq | Inconclusive | TIMEOUT | Inconclusive | yes |
| t20 | bind | Inconclusive | TIMEOUT | Inconclusive | yes |
