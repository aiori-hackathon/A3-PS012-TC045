"""The probe engine: sends the baseline query and the canary queries, and records the evidence."""
from __future__ import annotations

import time
from datetime import datetime, timezone

import dns.exception
import dns.flags
import dns.message
import dns.query
import dns.rcode

from resolverlens.names import canary_name


class SafetyStop(RuntimeError):
    """A safety tripwire fired; the run must stop."""


def default_transport(query, ip, timeout, source, tcp):
    if tcp:
        return dns.query.tcp(query, ip, timeout=timeout, source=source)
    return dns.query.udp(query, ip, timeout=timeout, source=source)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Prober:
    def __init__(self, cfg, lab, scope, rate, canary, writer, run_id, transport=default_transport, clock=time.monotonic):
        self.cfg, self.lab, self.scope, self.rate = cfg, lab, scope, rate
        self.canary, self.writer, self.run_id = canary, writer, run_id
        self.transport, self.clock = transport, clock
        self.seq = 0

    # -- one query -------------------------------------------------------------------------
    def _send(self, target, qname: str, rd: bool, phase: str, attempt: int) -> dict:
        self.scope.check(target.ip)                      # refuse anything off the allowlist
        self.rate.acquire(target.id)                     # wait for a token from both buckets
        self.seq += 1
        rec = {"run_id": self.run_id, "seq": self.seq, "ts": _now(), "target_id": target.id, "target_ip": target.ip,
               "phase": phase, "attempt": attempt, "qname": qname, "qtype": "A", "rd": rd, "transport": "udp",
               "status": None, "rcode": None, "flags": {}, "answers": [], "rtt_ms": None, "query_bytes": None,
               "reply_bytes": None, "tcp_retry": False, "error": None, "canary_hit": None, "canary_sources": [],
               "canary_wait_ms": None}
        self.writer.audit(f"{rec['ts']} {target.id} {target.ip} {phase} attempt={attempt} rd={int(rd)} {qname}")
        q = dns.message.make_query(qname, "A", use_edns=0, payload=self.cfg.edns_payload,
                                   flags=dns.flags.RD if rd else 0)
        rec["query_bytes"] = len(q.to_wire(max_size=65535))
        t0 = self.clock()
        try:
            r = self.transport(q, target.ip, self.cfg.timeout_s, self.cfg.source_address, False)
            if (r.flags & dns.flags.TC) and self.cfg.tcp_retry:
                rec["tcp_retry"], rec["transport"] = True, "tcp"
                try:
                    r = self.transport(q, target.ip, self.cfg.timeout_s, self.cfg.source_address, True)
                except (OSError, dns.exception.DNSException) as e:
                    rec["status"], rec["error"] = "TC_FAIL", f"{type(e).__name__}: {e}"
                    r = None
            if r is not None:
                rec["rtt_ms"] = round((self.clock() - t0) * 1000, 1)
                rec["status"] = dns.rcode.to_text(r.rcode())
                rec["rcode"] = int(r.rcode())
                rec["flags"] = {k: bool(r.flags & v) for k, v in (("aa", dns.flags.AA), ("tc", dns.flags.TC),
                                                                   ("rd", dns.flags.RD), ("ra", dns.flags.RA))}
                rec["answers"] = [rr.address for rrset in r.answer for rr in rrset if rrset.rdtype == 1]
                rec["reply_bytes"] = len(r.to_wire(max_size=65535))
        except dns.exception.Timeout:
            rec["status"] = "TIMEOUT"
        except (OSError, dns.exception.DNSException) as e:
            rec["status"], rec["error"] = "ERROR", f"{type(e).__name__}: {e}"
        return rec

    def _finish(self, rec: dict) -> None:
        """Write the record, then enforce the reply-size tripwire."""
        self.writer.record(rec)
        rb, qb = rec["reply_bytes"], rec["query_bytes"]
        if rb is not None and (rb > self.cfg.max_reply_bytes or rb / qb > self.cfg.max_ratio):
            raise SafetyStop(f"{rec['target_id']}: reply of {rb} bytes to a {qb}-byte query "
                             f"(limits: {self.cfg.max_reply_bytes} bytes, ratio {self.cfg.max_ratio})")

    # -- one target ------------------------------------------------------------------------
    def probe_target(self, target) -> list[dict]:
        """Baseline query (RD off, own zone) then N canary queries (RD on, fresh unique names)."""
        out = []
        base = self._send(target, f"ns.{self.lab['baseline_zone']}", False, "baseline", 0)
        self._finish(base)
        out.append(base)
        zone = self.lab["canary"]["zone"]
        for k in range(1, self.cfg.attempts + 1):
            name = canary_name(self.cfg.seed, self.run_id, target.id, k, zone)
            rec = self._send(target, name, True, "canary", k)
            replied = rec["status"] not in ("TIMEOUT", "ERROR", "TC_FAIL")
            if rec["answers"]:                       # an answer came back: the lookup must appear in the canary log
                wait = self.cfg.canary_wait_s
            else:                                    # REFUSED, empty or no reply: nothing to wait for, only a short grace
                wait = min(0.3 if replied else 0.6, self.cfg.canary_wait_s)
            t0 = self.clock()
            rec["canary_sources"] = self.canary.wait_for(name, wait)
            rec["canary_hit"] = bool(rec["canary_sources"])
            rec["canary_wait_ms"] = round((self.clock() - t0) * 1000, 1)
            self._finish(rec)
            out.append(rec)
        return out
