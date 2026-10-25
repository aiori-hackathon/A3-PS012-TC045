# Phase 2: tool core evidence
Date: 2026-10-26T00:30:20+05:30   Run by: Aditya V J

## Unit tests
```
...................................................                      [100%]
51 passed in 0.41s
```

## Manifest
```
{'status': 'completed', 'stop_reason': 'completed', 'probes': 80, 'canary_hits': 24, 'duration_s': 70.7, 'seed': 1337, 'tool_version': '0.2.0'}
digest a79e23245d905be4
{'NOERROR': 34, 'NXDOMAIN': 3, 'REFUSED': 29, 'TIMEOUT': 14}
```

## Per-target summary and rate check
```
t01  {'NOERROR': 4}  canary_hits=3/3  sources=['10.10.0.11']
t02  {'NOERROR': 4}  canary_hits=3/3  sources=['10.10.0.12']
t03  {'NXDOMAIN': 1, 'NOERROR': 3}  canary_hits=3/3  sources=['10.10.0.13']
t04  {'NXDOMAIN': 1, 'NOERROR': 3}  canary_hits=3/3  sources=['10.10.0.14']
t05  {'REFUSED': 1, 'NOERROR': 3}  canary_hits=3/3  sources=['10.10.0.15']
t06  {'REFUSED': 4}  canary_hits=0/3  sources=[]
t07  {'REFUSED': 4}  canary_hits=0/3  sources=[]
t08  {'REFUSED': 4}  canary_hits=0/3  sources=[]
t09  {'REFUSED': 4}  canary_hits=0/3  sources=[]
t10  {'NOERROR': 1, 'REFUSED': 3}  canary_hits=0/3  sources=[]
t11  {'NOERROR': 1, 'REFUSED': 3}  canary_hits=0/3  sources=[]
t12  {'NOERROR': 1, 'REFUSED': 3}  canary_hits=0/3  sources=[]
t13  {'NOERROR': 1, 'REFUSED': 3}  canary_hits=0/3  sources=[]
t14  {'NOERROR': 4}  canary_hits=3/3  sources=['10.10.0.11']
t15  {'NXDOMAIN': 1, 'NOERROR': 3}  canary_hits=3/3  sources=['10.10.0.13']
t16  {'NOERROR': 4}  canary_hits=3/3  sources=['10.10.0.15']
t17  {'TIMEOUT': 4}  canary_hits=0/3  sources=[]
t18  {'NOERROR': 1, 'TIMEOUT': 3}  canary_hits=0/3  sources=[]
t19  {'TIMEOUT': 4}  canary_hits=0/3  sources=[]
t20  {'NOERROR': 1, 'TIMEOUT': 3}  canary_hits=0/3  sources=[]
max queries in any 1 s window (all targets): 3 (limit: 5 per second plus burst)
```
