from resolverlens.names import canary_name


def test_same_inputs_give_same_name():
    assert canary_name(1, "r1", "t01", 1, "canary.lab") == canary_name(1, "r1", "t01", 1, "canary.lab")


def test_every_input_changes_the_name():
    base = canary_name(1, "r1", "t01", 1, "canary.lab")
    assert len({base, canary_name(2, "r1", "t01", 1, "canary.lab"), canary_name(1, "r2", "t01", 1, "canary.lab"),
                canary_name(1, "r1", "t02", 1, "canary.lab"), canary_name(1, "r1", "t01", 2, "canary.lab")}) == 5


def test_name_is_inside_the_canary_zone():
    n = canary_name(1, "r1", "t01", 1, "canary.lab")
    assert n.startswith("rl-") and n.endswith(".canary.lab")
