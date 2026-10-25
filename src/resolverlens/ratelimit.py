"""Token-bucket rate control: one bucket per target plus one global bucket."""
from __future__ import annotations

import random
import time

from resolverlens.config import BucketCfg


class TokenBucket:
    """A counter that refills at `rate` tokens per second up to `burst`. One query uses one token."""

    def __init__(self, rate: float, burst: int, clock=time.monotonic):
        self.rate, self.burst, self._clock = rate, burst, clock
        self._tokens = float(burst)
        self._last = clock()

    def _refill(self) -> None:
        now = self._clock()
        self._tokens = min(float(self.burst), self._tokens + (now - self._last) * self.rate)
        self._last = now

    def wait_time(self) -> float:
        self._refill()
        return 0.0 if self._tokens >= 1.0 else (1.0 - self._tokens) / self.rate

    def take(self) -> None:
        self._refill()
        if self._tokens < 1.0:
            raise RuntimeError("take() called with no token available")
        self._tokens -= 1.0


class RateController:
    """A query may be sent only when both the target's bucket and the global bucket have a token."""

    def __init__(self, per_target: BucketCfg, global_cfg: BucketCfg, jitter_ms: int, seed: int,
                 clock=time.monotonic, sleep=time.sleep):
        self._pt_cfg, self._clock, self._sleep = per_target, clock, sleep
        self._global = TokenBucket(global_cfg.rate, global_cfg.burst, clock)
        self._buckets: dict[str, TokenBucket] = {}
        self._jitter = jitter_ms / 1000.0
        self._rng = random.Random(seed)

    def acquire(self, target_id: str) -> float:
        """Block until a query to `target_id` is allowed. Returns the seconds spent waiting."""
        b = self._buckets.setdefault(target_id, TokenBucket(self._pt_cfg.rate, self._pt_cfg.burst, self._clock))
        start = self._clock()
        while True:
            wait = max(b.wait_time(), self._global.wait_time())
            if wait <= 0.0:
                b.take()
                self._global.take()
                break
            self._sleep(wait)
        if self._jitter:
            self._sleep(self._rng.uniform(0.0, self._jitter))
        return self._clock() - start
