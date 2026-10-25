#!/bin/bash
# ResolverLens lab entrypoint: apply the traffic impairment (if any), then run one DNS server in the foreground.
set -euo pipefail
: "${RL_SOFTWARE:?RL_SOFTWARE is required}"
RL_IMPAIR="${RL_IMPAIR:-none}"
RL_IP="${RL_IP:-}"

iface() {
  local d=""
  if [ -n "$RL_IP" ]; then
    d=$(ip -o -4 addr show | awk -v ip="$RL_IP" 'index($4, ip "/") == 1 {print $2; exit}')
  fi
  echo "${d:-eth0}"
}

case "$RL_IMPAIR" in
  none) ;;
  delay)
    tc qdisc add dev "$(iface)" root netem delay "${RL_DELAY_MS:-3000}ms"
    echo "[rl] netem delay ${RL_DELAY_MS:-3000}ms applied on $(iface)" ;;
  ratelimit)
    for proto in udp tcp; do
      iptables -A INPUT -p "$proto" --dport 53 -m limit --limit 1/minute --limit-burst 1 -j ACCEPT
      iptables -A INPUT -p "$proto" --dport 53 -j DROP
    done
    echo "[rl] rate limit applied: 1 DNS packet per minute accepted" ;;
  silent)
    : "${RL_BLOCK_SRC:?RL_BLOCK_SRC is required for silent}"
    for proto in udp tcp; do
      iptables -A INPUT -s "$RL_BLOCK_SRC" -p "$proto" --dport 53 -j DROP
    done
    echo "[rl] DNS from $RL_BLOCK_SRC is silently dropped" ;;
  *) echo "[rl] unknown RL_IMPAIR=$RL_IMPAIR" >&2; exit 2 ;;
esac

mkdir -p /var/lib/rl /var/log/named
case "$RL_SOFTWARE" in
  bind)    chown -R bind:bind /var/lib/rl /var/log/named
           exec named -f -u bind -c /etc/rl/named.conf ;;
  unbound) exec unbound -d -c /etc/rl/unbound.conf ;;
  dnsmasq) exec dnsmasq --keep-in-foreground --conf-file=/etc/rl/dnsmasq.conf ;;
  nsd)     chown -R nsd:nsd /var/lib/rl
           exec nsd -d -c /etc/rl/nsd.conf ;;
  *) echo "[rl] unknown RL_SOFTWARE=$RL_SOFTWARE" >&2; exit 2 ;;
esac
