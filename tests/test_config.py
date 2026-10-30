import pytest
import yaml

from resolverlens.config import ConfigError, config_digest, load_config


def _edit(path, fn):
    d = yaml.safe_load(path.read_text())
    fn(d)
    path.write_text(yaml.safe_dump(d))


def test_default_config_loads():
    cfg = load_config("config/config.yaml")
    assert cfg.attempts == 3 and cfg.global_bucket.rate == 5.0 and cfg.max_targets == 20


def test_rate_above_hard_cap_is_rejected(lab_files):
    _edit(lab_files["config"], lambda d: d["rate"]["per_target"].update(rate=50))
    with pytest.raises(ConfigError):
        load_config(lab_files["config"])


def test_global_rate_above_hard_cap_is_rejected(lab_files):
    _edit(lab_files["config"], lambda d: d["rate"]["global"].update(rate=100))
    with pytest.raises(ConfigError):
        load_config(lab_files["config"])


def test_too_many_targets_is_rejected(lab_files):
    _edit(lab_files["config"], lambda d: d["safety"].update(max_targets=21))
    with pytest.raises(ConfigError):
        load_config(lab_files["config"])


def test_bad_source_address_is_rejected(lab_files):
    _edit(lab_files["config"], lambda d: d["probe"].update(source_address="not-an-ip"))
    with pytest.raises(ConfigError):
        load_config(lab_files["config"])


def test_missing_setting_is_rejected(lab_files):
    _edit(lab_files["config"], lambda d: d["probe"].pop("timeout_s"))
    with pytest.raises(ConfigError):
        load_config(lab_files["config"])


def test_digest_changes_with_config_and_targets(lab_files):
    cfg = load_config(lab_files["config"])
    a = config_digest(cfg, "x")
    assert a == config_digest(cfg, "x")
    assert a != config_digest(cfg, "y")


def test_reference_target_defaults_to_t01_and_can_be_set(lab_files):
    assert load_config(lab_files["config"]).reference_target == "t01"
    _edit(lab_files["config"], lambda d: d.update(preflight={"reference_target": "t06"}))
    assert load_config(lab_files["config"]).reference_target == "t06"
