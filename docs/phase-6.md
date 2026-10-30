# Phase 6: hardening evidence
Date: 2026-10-30T20:39:05+05:30   Run by: Aditya V J

## Unit tests
```
........................................................................ [ 51%]
...................................................................      [100%]
139 passed in 5.75s
```

## Preflight
```
preflight checks
  PASS  settings are valid and inside the hard safety caps
  PASS  allowlist loads: private lab subnet, at most 20 targets  (20 targets)
  PASS  results folder is writable and has free space  (136879 MB free)
  PASS  no stop file is present
  PASS  canary query log is readable
  PASS  canary round trip through t01: marker answer and a canary log entry  (answer ['192.0.2.53'], canary saw it from ['10.10.0.11'])
preflight passed
```

## Stability across three real runs
```
t01  STABLE   recursive | recursive | recursive
t02  STABLE   recursive | recursive | recursive
t03  STABLE   recursive | recursive | recursive
t04  STABLE   recursive | recursive | recursive
t05  STABLE   recursive | recursive | recursive
t06  STABLE   refused | refused | refused
t07  STABLE   refused | refused | refused
t08  STABLE   refused | refused | refused
t09  STABLE   refused | refused | refused
t10  STABLE   authoritative_only | authoritative_only | authoritative_only
t11  STABLE   authoritative_only | authoritative_only | authoritative_only
t12  STABLE   authoritative_only | authoritative_only | authoritative_only
t13  STABLE   authoritative_only | authoritative_only | authoritative_only
t14  STABLE   recursive | recursive | recursive
t15  STABLE   recursive | recursive | recursive
t16  STABLE   recursive | recursive | recursive
t17  STABLE   inconclusive/TIMEOUT | inconclusive/TIMEOUT | inconclusive/TIMEOUT
t18  STABLE   inconclusive/TIMEOUT | inconclusive/TIMEOUT | inconclusive/TIMEOUT
t19  STABLE   inconclusive/TIMEOUT | inconclusive/TIMEOUT | inconclusive/TIMEOUT
t20  STABLE   inconclusive/TIMEOUT | inconclusive/TIMEOUT | inconclusive/TIMEOUT
20/20 servers keep the same label across 3 runs (stab-1, stab-2, stab-3)
```

## Replay of stored runs

### stab-1
```
  PASS  evidence.jsonl unchanged since the run (sha256)
  PASS  re-derived verdicts.jsonl is byte-identical to the stored one
  PASS  re-derived verdicts.csv is byte-identical to the stored one
REPLAY OK: the run is intact and its verdicts reproduce exactly
```

### phase5-main
```
  PASS  file hashes recorded in the manifest  (not recorded (run made before hashing was added))
  PASS  re-derived verdicts.jsonl is byte-identical to the stored one
  PASS  re-derived verdicts.csv is byte-identical to the stored one
REPLAY OK: the run is intact and its verdicts reproduce exactly
```

### chal-a
```
  PASS  file hashes recorded in the manifest  (not recorded (run made before hashing was added))
  PASS  re-derived verdicts.jsonl is byte-identical to the stored one
  PASS  re-derived verdicts.csv is byte-identical to the stored one
REPLAY OK: the run is intact and its verdicts reproduce exactly
```
