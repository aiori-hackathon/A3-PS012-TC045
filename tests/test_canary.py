from resolverlens.canary import CanaryLog

LINE = "25-Oct-2026 14:22:38.977 client @0x7f2ce000f2f8 {src}#58827 ({name}): query: {name} IN A -E(0)DC (10.10.0.5)\n"


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_reads_sources_and_ignores_other_lines(tmp_path):
    p = tmp_path / "q.log"
    p.write_text("startup noise\n" + LINE.format(src="10.10.0.27", name="rl-aaa.canary.lab"))
    assert CanaryLog(p).sources("rl-aaa.canary.lab") == ["10.10.0.27"]
    assert CanaryLog(p).sources("rl-bbb.canary.lab") == []


def test_case_insensitive_and_multiple_sources(tmp_path):
    p = tmp_path / "q.log"
    p.write_text(LINE.format(src="10.10.0.11", name="RL-AaA.canary.lab") + LINE.format(src="10.10.0.12", name="rl-aaa.canary.lab"))
    assert CanaryLog(p).sources("rl-aaa.canary.lab") == ["10.10.0.11", "10.10.0.12"]


def test_incomplete_last_line_is_not_read_until_finished(tmp_path):
    p = tmp_path / "q.log"
    full = LINE.format(src="10.10.0.11", name="rl-aaa.canary.lab")
    p.write_text(full[:40])
    log = CanaryLog(p)
    assert log.sources("rl-aaa.canary.lab") == []
    p.write_text(full)
    assert log.sources("rl-aaa.canary.lab") == ["10.10.0.11"]


def test_new_lines_are_picked_up_and_rotation_is_handled(tmp_path):
    p = tmp_path / "q.log"
    p.write_text(LINE.format(src="10.10.0.11", name="rl-aaa.canary.lab") * 3)
    log = CanaryLog(p)
    assert log.sources("rl-aaa.canary.lab")
    p.write_text(LINE.format(src="10.10.0.13", name="rl-bbb.canary.lab"))     # shorter file = rotated
    assert log.sources("rl-bbb.canary.lab") == ["10.10.0.13"]


def test_wait_for_times_out_and_returns_empty(tmp_path):
    c = Clock()
    p = tmp_path / "q.log"
    p.write_text("")
    log = CanaryLog(p, clock=c, sleep=c.sleep)
    assert log.wait_for("rl-zzz.canary.lab", 1.0) == []
    assert c.t >= 1.0


def test_missing_file_is_empty(tmp_path):
    assert CanaryLog(tmp_path / "nope.log").sources("rl-aaa.canary.lab") == []
