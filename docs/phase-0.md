# Phase 0: foundations
Date: 2026-10-24   Done by: Aditya V J

## Tool versions
```
Docker version 29.9.1, build dfc520d
Docker Compose version v5.6.0
git version 2.56.0
Python 3.12.13
GNU Make 4.4.1
```

## Isolated network test (ping must fail on rl-test; control ping on default bridge)
```
Unable to find image 'alpine:latest' locally
latest: Pulling from library/alpine
7b229517ed22: Pulling fs layer
7b229517ed22: Download complete
3ec36f3670df: Download complete
3da1513d2124: Download complete
Digest: sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
Status: Downloaded newer image for alpine:latest
PING 1.1.1.1 (1.1.1.1): 56 data bytes
ping: sendto: Network unreachable
RESULT: no route out of rl-test (expected)
PING 1.1.1.1 (1.1.1.1): 56 data bytes
64 bytes from 1.1.1.1: seq=0 ttl=57 time=77.627 ms

--- 1.1.1.1 ping statistics ---
1 packets transmitted, 1 packets received, 0% packet loss
round-trip min/avg/max = 77.627/77.627/77.627 ms
```
