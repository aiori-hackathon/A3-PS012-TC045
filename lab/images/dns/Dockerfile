# One image for every lab DNS server. RL_SOFTWARE selects bind, unbound, dnsmasq or nsd at run time.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends bind9 bind9-dnsutils unbound dnsmasq nsd iproute2 iptables ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /usr/local/bin/rl-entrypoint
RUN chmod 0755 /usr/local/bin/rl-entrypoint
ENTRYPOINT ["/usr/local/bin/rl-entrypoint"]
