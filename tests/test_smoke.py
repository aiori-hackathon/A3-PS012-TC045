from resolverlens import __version__
from resolverlens.cli import main


def test_version_is_set():
    assert __version__


def test_cli_runs():
    assert main([]) == 0
