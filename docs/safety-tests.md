# Safety tests in the Docker lab
Date: 2026-10-30T20:21:56+05:30   Run by: Dinesh Babu R S

## 1. Dry run sends nothing
```
ResolverLens 0.2.0  run 20261030T145157Z  seed 1337
targets: 20  queries per target: 4 (1 baseline + 3 canary)  total: 80
limits: per target 1.0/s burst 2; global 5.0/s burst 5; timeout 2.0s
DRY RUN: nothing is sent. Minimum time at these limits: about 16 s (more if servers time out).
example canary names: rl-edf65aaaa1.canary.lab, rl-8953f25590.canary.lab, rl-027257082a.canary.lab
```

## 2. A stop file ends a run cleanly between servers
```
t07  10.10.0.17    bind     REFUSED=4  canary_hits=0/3
stop file found: 28 probes in 14.8 s -> results/stop-test/
make: *** [Makefile:59: probe] Error 130
status: stopped | reason: stop file found | probes: 28 of 80
```

## 3. The reply-size tripwire ends a run after the first oversized reply (limit lowered to ratio 1.0 for this test)
```
targets: 20  queries per target: 4 (1 baseline + 3 canary)  total: 80
limits: per target 1.0/s burst 2; global 5.0/s burst 5; timeout 2.0s
safety tripwire: t01: reply of 251 bytes to a 40-byte query (limits: 1232 bytes, ratio 1.0): 1 probes in 0.0 s -> results/tripwire-test/
exit code: 3
status: stopped | reason: safety tripwire: t01: reply of 251 bytes to a 40-byte query (limits: 1232 bytes, ratio 1.0 | probes: 1
```
