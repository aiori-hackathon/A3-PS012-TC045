#!/usr/bin/env bash
# Fault injection: remove the rate limit on rl-t18, assess, show how the report explains the false result, then restore rl-t18.
set -uo pipefail
cd "$(dirname "$0")/.."
RUN="${1:-fault-t18}"
echo "== removing the rate limit on rl-t18 (it is meant to be unusable, so the tool should now report a false exposure) =="
docker exec rl-t18 iptables -F INPUT
make probe RUN="$RUN"
.venv/bin/python -m resolverlens.cli report "results/$RUN" || true
echo "== restoring rl-t18 =="
docker restart rl-t18 >/dev/null
sleep 8
echo "rl-t18 health: $(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}-{{end}}' rl-t18)"
