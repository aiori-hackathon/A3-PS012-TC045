# Phase 1: the lab
Date: 2026-10-25T19:50:16+05:30   Run by: Dinesh Babu R S <217003480+Dineshbaburs@users.noreply.github.com>

## Images
```
REPOSITORY   TAG       SIZE
rl-client    1         255MB
rl-dns       1         249MB
```

## Containers (name, state, health, address)
```
rl-canary  running   healthy    10.10.0.5
rl-ctl     running   -          10.10.1.10
rl-ext     running   -          10.10.2.10
rl-t01     running   healthy    10.10.0.11
rl-t02     running   healthy    10.10.0.12
rl-t03     running   healthy    10.10.0.13
rl-t04     running   healthy    10.10.0.14
rl-t05     running   healthy    10.10.0.15
rl-t06     running   healthy    10.10.0.16
rl-t07     running   healthy    10.10.0.17
rl-t08     running   healthy    10.10.0.18
rl-t09     running   healthy    10.10.0.19
rl-t10     running   healthy    10.10.0.20
rl-t11     running   healthy    10.10.0.21
rl-t12     running   healthy    10.10.0.22
rl-t13     running   healthy    10.10.0.23
rl-t14     running   healthy    10.10.0.24
rl-t15     running   healthy    10.10.0.25
rl-t16     running   healthy    10.10.0.26
rl-t17     running   healthy    10.10.0.27
rl-t18     running   healthy    10.10.0.28
rl-t19     running   healthy    10.10.0.29
rl-t20     running   healthy    10.10.0.30
```

## No published ports (Ports column must be empty)
```
rl-t13 []
rl-t06 []
rl-t16 []
rl-t19 []
rl-t14 []
rl-t18 []
rl-t10 []
rl-t15 []
rl-t03 []
rl-t04 []
rl-t12 []
rl-t20 []
rl-t09 []
rl-t02 []
rl-t11 []
rl-t08 []
rl-t17 []
rl-t01 []
rl-t07 []
rl-t05 []
rl-canary []
rl-ctl []
rl-ext []
```

## Memory and CPU
```
NAME                   MEM USAGE / LIMIT     CPU %
rl-t13                 37.83MiB / 192MiB     0.00%
rl-t06                 23.33MiB / 192MiB     0.00%
rl-t16                 22.89MiB / 192MiB     0.00%
rl-t19                 1000KiB / 192MiB      0.00%
rl-t14                 980KiB / 192MiB       0.00%
rl-t18                 23.17MiB / 192MiB     0.00%
rl-t10                 22.75MiB / 192MiB     0.00%
rl-t15                 8.047MiB / 192MiB     0.00%
rl-t03                 8.043MiB / 192MiB     0.00%
rl-t04                 8.035MiB / 192MiB     3.42%
rl-t12                 37.82MiB / 192MiB     0.00%
rl-t20                 22.86MiB / 192MiB     0.00%
rl-t09                 8.043MiB / 192MiB     0.00%
rl-t02                 23.38MiB / 192MiB     0.00%
rl-t11                 22.76MiB / 192MiB     3.18%
rl-t08                 8.035MiB / 192MiB     0.00%
rl-t17                 8.07MiB / 192MiB      0.00%
rl-t01                 23.51MiB / 192MiB     0.00%
rl-t07                 23.36MiB / 192MiB     0.00%
rl-t05                 988KiB / 192MiB       0.00%
rl-canary              22.88MiB / 192MiB     0.00%
rl-ctl                 788KiB / 256MiB       0.00%
rl-ext                 804KiB / 256MiB       0.00%
saas-billing-mongodb   20.36MiB / 9.578GiB   0.48%
Portainer              24.67MiB / 9.578GiB   0.00%
```

## Isolation: connect from the external client to a public address (must fail)
```
OSError: [Errno 101] Network is unreachable
```

## Check from the external probe client (rl-ext)
```
t01  bind     open_recursive     PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t02  bind     open_recursive     PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t03  unbound  open_recursive     PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t04  unbound  open_recursive     PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t05  dnsmasq  open_recursive     PASS  base=REFUSED canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t06  bind     policy_refusing    PASS  base=REFUSED canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t07  bind     policy_refusing    PASS  base=REFUSED canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t08  unbound  policy_refusing    PASS  base=REFUSED canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t09  unbound  policy_refusing    PASS  base=REFUSED canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t10  bind     authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t11  bind     authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t12  nsd      authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t13  nsd      authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t14  dnsmasq  forwarder          PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t15  unbound  forwarder          PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t16  bind     forwarder          PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t17  unbound  slow               PASS  base=TIMEOUT canary=['TIMEOUT', 'TIMEOUT', 'TIMEOUT'] hit=['n', 'n', 'n']
t18  bind     rate_limited       PASS  base=NOERROR canary=['TIMEOUT', 'TIMEOUT', 'TIMEOUT'] hit=['n', 'n', 'n']
t19  dnsmasq  silent             PASS  base=TIMEOUT canary=['TIMEOUT', 'TIMEOUT', 'TIMEOUT'] hit=['n', 'n', 'n']
t20  bind     broken_upstream    PASS  base=NOERROR canary=['TIMEOUT', 'TIMEOUT', 'TIMEOUT'] hit=['n', 'n', 'n']

vantage=external: 20/20 checked targets match their expected profile, 0 failed
```

## Check from the control client (rl-ctl)
```
t01  bind     open_recursive     PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t02  bind     open_recursive     PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t03  unbound  open_recursive     PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t04  unbound  open_recursive     PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t05  dnsmasq  open_recursive     PASS  base=REFUSED canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t06  bind     policy_refusing    PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t07  bind     policy_refusing    PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t08  unbound  policy_refusing    PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t09  unbound  policy_refusing    PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t10  bind     authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t11  bind     authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t12  nsd      authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t13  nsd      authoritative_only PASS  base=NOERROR/AA canary=['REFUSED', 'REFUSED', 'REFUSED'] hit=['n', 'n', 'n']
t14  dnsmasq  forwarder          PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t15  unbound  forwarder          PASS  base=NXDOMAIN/AA canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t16  bind     forwarder          PASS  base=NOERROR canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t17  unbound  slow               SKIP  base=TIMEOUT canary=['TIMEOUT', 'TIMEOUT', 'TIMEOUT'] hit=['n', 'n', 'n'] (not checked from control)
t18  bind     rate_limited       SKIP  base=NOERROR canary=['TIMEOUT', 'TIMEOUT', 'TIMEOUT'] hit=['n', 'n', 'n'] (not checked from control)
t19  dnsmasq  silent             PASS  base=REFUSED canary=['NOERROR', 'NOERROR', 'NOERROR'] hit=['y', 'y', 'y']
t20  bind     broken_upstream    SKIP  base=NOERROR canary=['TIMEOUT', 'TIMEOUT', 'TIMEOUT'] hit=['n', 'n', 'n'] (not checked from control)

vantage=control: 17/17 checked targets match their expected profile, 0 failed
```

## Last canary log lines
```
25-Oct-2026 14:22:38.977 client @0x7f2ce000f2f8 10.10.0.27#58827 (rl-v-t17-dec826a3.canary.lab): query: rl-v-t17-dec826a3.canary.lab IN A -E(0)DC (10.10.0.5)
25-Oct-2026 14:22:41.787 client @0x7f2ce4001ee8 10.10.0.27#42339 (rl-v-t17-75be25bb.canary.lab): query: rl-v-t17-75be25bb.canary.lab IN A -E(0)DC (10.10.0.5)
25-Oct-2026 14:22:50.020 client @0x7f2ce808e738 10.10.0.29#54492 (rl-v-t19-b1d2e765.canary.lab): query: rl-v-t19-b1d2e765.canary.lab IN A +E(0) (10.10.0.5)
25-Oct-2026 14:22:50.223 client @0x7f2cd8002f48 10.10.0.29#39190 (rl-v-t19-57b62637.canary.lab): query: rl-v-t19-57b62637.canary.lab IN A +E(0) (10.10.0.5)
25-Oct-2026 14:22:50.425 client @0x7f2cd8002f48 10.10.0.29#56041 (rl-v-t19-602b9d83.canary.lab): query: rl-v-t19-602b9d83.canary.lab IN A +E(0) (10.10.0.5)
```

