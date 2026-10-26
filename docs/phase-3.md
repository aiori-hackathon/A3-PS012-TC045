# Phase 3: classifier evidence
Date: 2026-10-26T07:14:40+05:30   Run by: Aditya V J

## Unit tests
```
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 0.45s
```

## Classification of the Phase 2 run (phase2-first)
```
t01  bind     recursive           -         R1  hits=3/3  expected=recursive           OK
t02  bind     recursive           -         R1  hits=3/3  expected=recursive           OK
t03  unbound  recursive           -         R1  hits=3/3  expected=recursive           OK
t04  unbound  recursive           -         R1  hits=3/3  expected=recursive           OK
t05  dnsmasq  recursive           -         R1  hits=3/3  expected=recursive           OK
t06  bind     refused             -         R2  hits=0/3  expected=refused             OK
t07  bind     refused             -         R2  hits=0/3  expected=refused             OK
t08  unbound  refused             -         R2  hits=0/3  expected=refused             OK
t09  unbound  refused             -         R2  hits=0/3  expected=refused             OK
t10  bind     authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t11  bind     authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t12  nsd      authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t13  nsd      authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t14  dnsmasq  recursive           -         R1  hits=3/3  expected=recursive           OK
t15  unbound  recursive           -         R1  hits=3/3  expected=recursive           OK
t16  bind     recursive           -         R1  hits=3/3  expected=recursive           OK
t17  unbound  inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
t18  bind     inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
t19  dnsmasq  inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
t20  bind     inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
wrote results/phase2-first/verdicts.csv and verdicts.jsonl
20/20 verdicts match the expected labels
```

## Classification of a fresh run (phase3-a)
```
t01  bind     recursive           -         R1  hits=3/3  expected=recursive           OK
t02  bind     recursive           -         R1  hits=3/3  expected=recursive           OK
t03  unbound  recursive           -         R1  hits=3/3  expected=recursive           OK
t04  unbound  recursive           -         R1  hits=3/3  expected=recursive           OK
t05  dnsmasq  recursive           -         R1  hits=3/3  expected=recursive           OK
t06  bind     refused             -         R2  hits=0/3  expected=refused             OK
t07  bind     refused             -         R2  hits=0/3  expected=refused             OK
t08  unbound  refused             -         R2  hits=0/3  expected=refused             OK
t09  unbound  refused             -         R2  hits=0/3  expected=refused             OK
t10  bind     authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t11  bind     authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t12  nsd      authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t13  nsd      authoritative_only  -         R3  hits=0/3  expected=authoritative_only  OK
t14  dnsmasq  recursive           -         R1  hits=3/3  expected=recursive           OK
t15  unbound  recursive           -         R1  hits=3/3  expected=recursive           OK
t16  bind     recursive           -         R1  hits=3/3  expected=recursive           OK
t17  unbound  inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
t18  bind     inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
t19  dnsmasq  inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
t20  bind     inconclusive        TIMEOUT   R4  hits=0/3  expected=inconclusive        OK
wrote results/phase3-a/verdicts.csv and verdicts.jsonl
20/20 verdicts match the expected labels
```

## Comparison of the two runs
```
IDENTICAL labels and reasons
```
