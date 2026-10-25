# Client image used for the external probe client (rl-ext) and the control client (rl-ctl).
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-dnspython python3-yaml python3-jinja2 bind9-dnsutils iproute2 ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["sleep", "infinity"]
