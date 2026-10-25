import pytest
import yaml

from resolverlens.scope import ScopeError, ScopeGuard, load_lab


def test_allowlisted_address_passes(lab_files):
    lab, targets = load_lab(lab_files["targets"])
    guard = ScopeGuard(lab, targets)
    assert guard.check("10.10.0.11") == "t01"


@pytest.mark.parametrize("ip", ["8.8.8.8", "10.10.0.99", "10.10.0.5", "10.10.2.10", "127.0.0.1", "garbage"])
def test_other_addresses_are_refused(lab_files, ip):
    lab, targets = load_lab(lab_files["targets"])
    with pytest.raises(ScopeError):
        ScopeGuard(lab, targets).check(ip)


def test_public_subnet_is_refused(lab_files):
    lab, targets = load_lab(lab_files["targets"])
    lab["subnet"] = "8.8.0.0/16"
    with pytest.raises(ScopeError):
        ScopeGuard(lab, targets)


def test_target_outside_subnet_is_refused(lab_files):
    lab, targets = load_lab(lab_files["targets"])
    lab["subnet"] = "10.20.0.0/16"
    with pytest.raises(ScopeError):
        ScopeGuard(lab, targets)


def test_more_than_the_limit_is_refused(lab_files):
    lab, targets = load_lab(lab_files["targets"])
    with pytest.raises(ScopeError):
        ScopeGuard(lab, targets, max_targets=2)


def test_expected_labels_are_not_loaded(lab_files):
    _, targets = load_lab(lab_files["targets"])
    assert not hasattr(targets[0], "expected")
