from resolverlens.config import BucketCfg
from resolverlens.ratelimit import RateController, TokenBucket


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_burst_then_steady_rate():
    c = Clock()
    b = TokenBucket(rate=1.0, burst=2, clock=c)
    assert b.wait_time() == 0
    b.take(); b.take()
    assert abs(b.wait_time() - 1.0) < 1e-9
    c.t += 1.0
    assert b.wait_time() == 0


def test_bucket_never_exceeds_burst():
    c = Clock()
    b = TokenBucket(rate=1.0, burst=2, clock=c)
    c.t += 100
    b.take(); b.take()
    assert b.wait_time() > 0


def test_per_target_limit_spaces_queries():
    c = Clock()
    rc = RateController(BucketCfg(1.0, 1), BucketCfg(100.0, 100), 0, 1, clock=c, sleep=c.sleep)
    rc.acquire("t01"); rc.acquire("t01"); rc.acquire("t01")
    assert abs(c.t - 2.0) < 1e-6          # 1 free, then 1 s apart


def test_global_limit_applies_across_targets():
    c = Clock()
    rc = RateController(BucketCfg(100.0, 100), BucketCfg(2.0, 1), 0, 1, clock=c, sleep=c.sleep)
    for tid in ("t01", "t02", "t03", "t04"):
        rc.acquire(tid)
    assert abs(c.t - 1.5) < 1e-6          # 1 free, then 0.5 s apart


def test_targets_have_separate_buckets():
    c = Clock()
    rc = RateController(BucketCfg(1.0, 1), BucketCfg(100.0, 100), 0, 1, clock=c, sleep=c.sleep)
    rc.acquire("t01"); rc.acquire("t02"); rc.acquire("t03")
    assert c.t == 0


def test_jitter_is_seeded():
    def total(seed):
        c = Clock()
        rc = RateController(BucketCfg(100.0, 100), BucketCfg(100.0, 100), 50, seed, clock=c, sleep=c.sleep)
        for _ in range(5):
            rc.acquire("t01")
        return c.t
    assert total(3) == total(3)
    assert total(3) != total(4)
    assert 0 < total(3) <= 0.25
