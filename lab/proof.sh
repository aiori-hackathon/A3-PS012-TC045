#!/usr/bin/env bash
# Writes docs/phase-1.md: evidence that the lab is up and every server behaves as designed.
set -uo pipefail
cd "$(dirname "$0")/.."
OUT=docs/phase-1.md
run() { echo '```'; "$@" 2>&1; echo '```'; echo; }
{
echo "# Phase 1: the lab"
echo "Date: $(date -Iseconds)   Run by: $(git config user.name) <$(git config user.email)>"
echo
echo "## Images"; run docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' --filter reference='rl-*'
echo "## Containers (name, state, health, address)"
echo '```'
for c in $(docker ps -a --filter name='^rl-' --format '{{.Names}}' | sort -V); do
  printf '%-10s %-9s %-10s %s\n' "$c" "$(docker inspect -f '{{.State.Status}}' "$c")" \
    "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}-{{end}}' "$c")" \
    "$(docker inspect -f '{{(index .NetworkSettings.Networks "rl-lab").IPAddress}}' "$c")"
done
echo '```'; echo
echo "## No published ports (Ports column must be empty)"; run docker ps --filter name='^rl-' --format '{{.Names}} [{{.Ports}}]'
echo "## Memory and CPU"; run docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'
echo "## Isolation: connect from the external client to a public address (must fail)"
echo '```'
docker exec rl-ext python3 -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('1.1.1.1', 53)); print('UNEXPECTED: connected')" 2>&1 | tail -1
echo '```'; echo
echo "## Check from the external probe client (rl-ext)"; run docker exec rl-ext python3 /work/lab/verify.py --vantage external
echo "## Check from the control client (rl-ctl)"; run docker exec rl-ctl python3 /work/lab/verify.py --vantage control
echo "## Last canary log lines"; run docker exec rl-canary tail -n 5 /var/log/named/queries.log
} > "$OUT"
echo "wrote $OUT"; grep -E "^vantage=" "$OUT"
