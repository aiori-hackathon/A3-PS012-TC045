# ResolverLens: pseudocode

This is the logic of the tool as implemented in `src/resolverlens/`. Names in brackets are the files.

## 1. One assessment run  [runner.py, probe.py]

    PROBE(config, targets_file):
        cfg           <- load_config(config)           # a rate above the hard caps is rejected (20/s overall, 5/s per server)
        lab, targets  <- load_lab(targets_file)        # expected labels are NOT loaded here
        scope         <- ScopeGuard(lab, targets)      # at most 20 targets, private subnet only
        PREFLIGHT()                                    # settings, allowlist, disk, one canary round trip; stop if anything fails
        run_dir       <- results/<run_id>/             # never overwritten

        for target in targets, one at a time:
            if file results/STOP exists: end the run cleanly
            SEND(target, "ns." + baseline_zone, RD = off, phase = baseline)
            for k in 1 .. attempts:                    # normally 3
                name <- "rl-" + sha256(seed, run_id, target, k)[:10] + "." + canary_zone    # fresh, repeatable from the seed
                rec  <- SEND(target, name, RD = on, phase = canary)
                wait <- canary_wait   if rec has an answer
                        0.3 s         if replied without an answer
                        0.6 s         if no reply
                rec.canary_sources <- canary_log.wait_for(name, wait)    # who asked OUR server for this name?
                rec.canary_hit     <- canary_sources is not empty
                append rec to evidence.jsonl
                if reply bytes > limit or reply/query ratio > limit: abort the run (safety tripwire)

        write manifest.json: seed, config digest, counts, how the run ended, sha256 of evidence.jsonl and audit.log

    SEND(target, name, RD, phase):
        scope.check(target.ip)                         # raises if the address is not on the allowlist; nothing is sent
        RATE.acquire(target.id)                        # see section 2
        append a line to audit.log                     # written before the packet leaves
        q     <- type A query, EDNS buffer 1232, RD as given        # never ANY
        reply <- UDP(q, timeout = 2 s)
        if reply is truncated and tcp_retry: reply <- TCP(q)
        return {status, flags (AA, TC, RD, RA), answers, rtt, query bytes, reply bytes, transport}

## 2. Rate control: token buckets  [ratelimit.py]

    bucket(rate r, burst b):    tokens <- b;  every second tokens <- min(b, tokens + r)
    RATE.acquire(target):
        loop:
            wait <- max(bucket[target].time_to_next_token(), bucket[global].time_to_next_token())
            if wait <= 0: take one token from BOTH buckets; break
            sleep(wait)
        sleep(random(0, jitter_ms))                    # seeded, so a run is repeatable
    # defaults: per server 1 query/s, burst 2; all servers together 5 queries/s, burst 5

## 3. Classification: the four rules  [classify.py]

    DECIDE(baseline, canaries):                        # first matching rule wins
        if baseline or any canary attempt is missing:  return INCONCLUSIVE(NO_DATA)
        R1  if every canary attempt is NOERROR, RA set, marker address in the answer, AND canary_hit:
                return RECURSIVE
        R2  if baseline is REFUSED and every canary attempt is REFUSED with no canary_hit:
                return REFUSED
        R3  if baseline is NOERROR with AA and an answer, and every canary attempt got a reply with
               no answer, no RA and no canary_hit:
                return AUTHORITATIVE_ONLY
        R4  return INCONCLUSIVE with a reason:
                TC_FAIL   if a truncated reply could not be completed over TCP
                TIMEOUT   if no canary attempt got a reply   (ERROR if the probe host failed to send)
                SERVFAIL  if the attempts were only SERVFAIL or timeouts
                CONFLICT  otherwise: the attempts disagree, or flags, answer and canary log contradict each other

    # A canary hit without a reply is not recursion (a slow server). An answer without a canary hit is not recursion either
    # (a sinkhole or a local-data liar): that is why the canary server's log, not the flags, decides.

## 4. Scoring and report  [compare.py, score.py, baseline.py, report.py]

    for each server: match <- (verdict == expected label)         # expected labels are read only here
    confusion matrix (rows expected, columns reported); precision, recall, F1 per class
    accuracy; accuracy on decided cases (verdict is not INCONCLUSIVE); coverage; wrong decisions; false and missed exposure
    for each false result: cause <- lookup(expected, reported, reason)    # ACL, recursion enabled, packet loss, upstream failure, ...
    also judge the same evidence with two single-flag rules (RA set; RA set and AA clear) and compare them with ResolverLens
    write report.html, report.pdf, summary.md, scores.json

## 5. Replay and stability  [replay.py, stability.py]

    REPLAY(run_dir):    check evidence sequence, counts, allowlist, query types and file hashes;
                        re-derive verdicts from evidence.jsonl alone and require them to be byte-identical to the stored ones
    STABILITY(runs):    a server is unstable if its LABEL differs between runs (a changing reason with the same label is a note)
