"""Reads the canary server's query log to find out which sources asked for a canary name."""
from __future__ import annotations

import re
import time
from pathlib import Path

LOG_RE = re.compile(r"^(\S+ \S+) client @0x[0-9a-f]+ ([0-9a-fA-F.:]+)#\d+ \(([^)]+)\)")


class CanaryLog:
    def __init__(self, path: str | Path, clock=time.monotonic, sleep=time.sleep, poll_s: float = 0.1):
        self.path, self._clock, self._sleep, self._poll_s = Path(path), clock, sleep, poll_s
        self._pos = 0
        self._seen: dict[str, list[str]] = {}

    def _poll(self) -> None:
        try:
            size = self.path.stat().st_size
        except OSError:
            return
        if size < self._pos:          # the log was rotated
            self._pos = 0
        with open(self.path, "rb") as f:
            f.seek(self._pos)
            chunk = f.read()
        end = chunk.rfind(b"\n")
        if end < 0:
            return
        self._pos += end + 1
        for line in chunk[:end].decode(errors="ignore").splitlines():
            m = LOG_RE.match(line)
            if m:
                srcs = self._seen.setdefault(m.group(3).lower(), [])
                if m.group(2) not in srcs:
                    srcs.append(m.group(2))

    def sources(self, name: str) -> list[str]:
        self._poll()
        return list(self._seen.get(name.lower().rstrip("."), []))

    def wait_for(self, name: str, timeout_s: float) -> list[str]:
        """Return the sources that asked for `name`, waiting up to `timeout_s` for the first one."""
        end = self._clock() + timeout_s
        while True:
            found = self.sources(name)
            if found or self._clock() >= end:
                return found
            self._sleep(self._poll_s)
