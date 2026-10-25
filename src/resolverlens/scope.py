"""Scope guard: the tool may only send packets to the allowlisted lab servers."""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path

import yaml


class ScopeError(RuntimeError):
    """An address outside the authorised lab was refused."""


@dataclass(frozen=True)
class Target:
    id: str
    ip: str
    software: str


def load_lab(path: str | Path):
    """Return (lab settings, list of Target). The expected labels in the file are deliberately not loaded."""
    data = yaml.safe_load(Path(path).read_text())
    lab = data["lab"]
    targets = [Target(t["id"], t["ip"], t["software"]) for t in data["targets"]]
    return lab, targets


class ScopeGuard:
    def __init__(self, lab: dict, targets: list[Target], max_targets: int = 20):
        if len(targets) > max_targets:
            raise ScopeError(f"{len(targets)} targets exceeds the limit of {max_targets}")
        net = ipaddress.ip_network(lab["subnet"])
        if not net.is_private:
            raise ScopeError(f"lab subnet {net} is not a private range; refusing to run")
        self._net = net
        self._allowed = {}
        for t in targets:
            ip = ipaddress.ip_address(t.ip)
            if ip not in net:
                raise ScopeError(f"{t.id} address {t.ip} is outside the lab subnet {net}")
            self._allowed[str(ip)] = t.id
        self.canary_ip = lab["canary"]["ip"]

    @property
    def allowed(self) -> dict:
        return dict(self._allowed)

    def check(self, ip: str) -> str:
        """Return the target id for an allowlisted address, otherwise raise ScopeError."""
        try:
            key = str(ipaddress.ip_address(ip))
        except ValueError:
            raise ScopeError(f"not an IP address: {ip!r}") from None
        if key not in self._allowed:
            raise ScopeError(f"{ip} is not on the allowlist; nothing was sent")
        return self._allowed[key]
