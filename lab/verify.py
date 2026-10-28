#!/usr/bin/env python3
"""Phase 1 lab check: does every lab server behave the way targets.yaml says it should?

Run from inside the external probe client (rl-ext) and the control client (rl-ctl):
    python3 /work/lab/verify.py --vantage external
    python3 /work/lab/verify.py --vantage control
Exit code 0 only if every checked target matches its expected profile.
"""
import argparse
import re
import secrets
import sys
import time
from pathlib import Path

import dns.exception
import dns.flags
import dns.message
import dns.query
import dns.rcode
import yaml

LOG_RE = re.compile(r"client @0x[0-9a-f]+ ([0-9a-fA-F.:]+)#\d+ \(([^)]+)\)")


def remap(ip, sandbox):
    return ("127.10." + ip.split(".", 2)[2]) if sandbox and ip.startswith("10.10.") else ip


class Probe:
    def __init__(self, a, lab):
        self.a, self.lab = a, lab
        self.marker = lab["canary"]["marker_ip"]
        self.cz, self.bz = lab["canary"]["zone"], lab["baseline_zone"]

    def ask(self, ip, name, rd, timeout):
        q = dns.message.make_query(name, "A", flags=(dns.flags.RD if rd else 0))
        try:
            r = dns.query.udp(q, ip, timeout=timeout, source=self.a.source or None)
        except dns.exception.Timeout:
            return {"status": "TIMEOUT", "ra": False, "aa": False, "answers": [], "tc": False}
        except OSError as e:
            return {"status": f"ERROR:{e.__class__.__name__}", "ra": False, "aa": False, "answers": [], "tc": False}
        ans = [rr.address for rrset in r.answer for rr in rrset if rr.rdtype == 1]
        return {"status": dns.rcode.to_text(r.rcode()), "ra": bool(r.flags & dns.flags.RA),
                "aa": bool(r.flags & dns.flags.AA), "tc": bool(r.flags & dns.flags.TC), "answers": ans}

    def canary_hit(self, name, wait=2.0):
        """Return the set of source IPs that asked the canary server for `name`."""
        end = time.time() + wait
        path = Path(self.a.canary_log)
        while True:
            if path.exists():
                srcs = {m.group(1) for line in path.read_text(errors="ignore").splitlines()[-4000:]
                        if name in line for m in [LOG_RE.search(line)] if m}
                if srcs:
                    return srcs
            if time.time() >= end:
                return set()
            time.sleep(0.2)

    def canary_query(self, ip, tid, timeout):
        name = f"rl-v-{tid}-{secrets.token_hex(4)}.{self.cz}"
        r = self.ask(ip, name, True, timeout)
        r["name"] = name
        r["hit"] = self.canary_hit(name, 2.0 if r["status"] != "TIMEOUT" else 0.6)
        r["marker"] = self.marker in r["answers"]
        return r


def judge(p, t, vantage, ip, timeout):
    """Return (ok, summary) for one target from one vantage point. ok=None means not checked."""
    bh, tid = t["behavior"], t["id"]
    base = p.ask(ip, f"ns.{p.bz}", False, timeout)
    time.sleep(0.2)
    c = [p.canary_query(ip, tid, timeout)]
    for _ in range(2):
        time.sleep(0.2)
        c.append(p.canary_query(ip, tid, timeout))
    c1 = c[0]
    rec = lambda r: r["status"] == "NOERROR" and r["ra"] and r["marker"] and bool(r["hit"])
    nohit = lambda r: not r["hit"] and not r["marker"]
    summ = f"base={base['status']}{'/AA' if base['aa'] else ''} canary={[x['status'] for x in c]} hit={['y' if x['hit'] else 'n' for x in c]}"
    if bh in ("open_recursive", "forwarder"):
        return all(rec(x) for x in c), summ
    if bh == "policy_refusing":
        if vantage == "external":
            return base["status"] == "REFUSED" and all(x["status"] == "REFUSED" and nohit(x) for x in c), summ
        return all(rec(x) for x in c), summ
    if bh in ("liar_local_answer", "wildcard_hijacker", "sinkhole_rewriter"):
        # answers with RA set and the marker, yet the canary log never shows a lookup
        return all(x["status"] == "NOERROR" and x["ra"] and x["marker"] and not x["hit"] for x in c), summ
    if bh == "ra_refuser":
        return all(x["status"] == "REFUSED" and nohit(x) for x in c), summ
    if bh == "slow_ok":
        # slow but responsive: tolerate a single cold-start timeout, require the rest to succeed
        nok = sum(1 for x in c if rec(x))
        return nok >= 2, summ
    if bh == "authoritative_only":
        return (base["status"] == "NOERROR" and base["aa"] and base["answers"] == [ip] and
                all(x["status"] in ("REFUSED", "NOERROR") and nohit(x) and not x["ra"] for x in c)), summ
    if vantage == "control":
        if bh == "silent":
            return all(rec(x) for x in c), summ
        return None, summ + " (not checked from control)"
    timeouts = sum(1 for x in [base] + c if x["status"] == "TIMEOUT")
    if bh == "slow":
        # replies arrive after our timeout; the canary may still log the lookup, so only the timeouts are checked
        return timeouts == 4, summ
    if bh == "silent":
        return timeouts == 4 and all(nohit(x) for x in c), summ
    if bh == "rate_limited":
        return timeouts >= 2, summ
    if bh == "broken_upstream":
        return all(x["status"] in ("SERVFAIL", "TIMEOUT") and nohit(x) for x in c), summ
    return False, summ + " (unknown behavior)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--targets", default="/work/lab/targets.yaml")
    ap.add_argument("--canary-log", default="/canary-logs/queries.log")
    ap.add_argument("--vantage", choices=["external", "control"], default="external")
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--only", help="check a single target id, e.g. t06")
    ap.add_argument("--source", help="source address to bind (sandbox only)")
    ap.add_argument("--sandbox", action="store_true", help="remap 10.10.x.y to 127.10.x.y (sandbox only)")
    a = ap.parse_args()
    data = yaml.safe_load(Path(a.targets).read_text())
    p = Probe(a, data["lab"])
    rows, bad = [], 0
    for t in data["targets"]:
        if a.only and t["id"] != a.only:
            continue
        ok, summ = judge(p, t, a.vantage, remap(t["ip"], a.sandbox), a.timeout)
        tag = "SKIP" if ok is None else "PASS" if ok else "FAIL"
        bad += tag == "FAIL"
        rows.append((t["id"], t["software"], t["behavior"], tag, summ))
        print(f"{t['id']:<4} {t['software']:<8} {t['behavior']:<18} {tag:<5} {summ}", flush=True)
    checked = sum(1 for r in rows if r[3] != "SKIP")
    print(f"\nvantage={a.vantage}: {sum(1 for r in rows if r[3]=='PASS')}/{checked} checked targets match their expected profile, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
