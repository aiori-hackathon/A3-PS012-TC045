.RECIPEPREFIX = >
SHELL := /bin/bash
RL_UID := $(shell id -u)
RL_GID := $(shell id -g)
export RL_UID RL_GID
COMPOSE := docker compose -f lab/generated/docker-compose.yml
.PHONY: help setup test clean lab-gen lab-build lab-up lab-down lab-ps lab-logs lab-check-ext lab-check-ctl lab-check lab-proof probe-dry probe
help:
> @echo "make setup        - create .venv and install dependencies"
> @echo "make test         - run unit tests"
> @echo "make lab-gen      - regenerate lab/generated from lab/targets.yaml"
> @echo "make lab-build    - build the rl-dns and rl-client images"
> @echo "make lab-up       - start the lab (23 containers)"
> @echo "make lab-ps       - show lab containers and health"
> @echo "make lab-logs T=t01 - follow logs of one container (t01..t20, canary, ext, ctl)"
> @echo "make lab-check    - verify every server from both vantage points"
> @echo "make lab-proof    - write docs/phase-1.md with the evidence"
> @echo "make lab-down     - stop and remove the lab"
> @echo "make probe-dry    - show the probe plan, send nothing"
> @echo "make probe [RUN=name] - run the probe from the external client against all 20 targets"
setup:
> python3 -m venv .venv
> .venv/bin/pip install -e ".[dev]"
test:
> .venv/bin/python -m pytest -q
clean:
> rm -rf .pytest_cache build *.egg-info src/*.egg-info
lab-gen:
> .venv/bin/python lab/generate.py
lab-build:
> docker build -t rl-dns:1 lab/images/dns
> docker build -t rl-client:1 lab/images/client
lab-up:
> mkdir -p results
> $(COMPOSE) up -d
> @echo "waiting 15 s for health checks..."; sleep 15
> @$(COMPOSE) ps --format 'table {{.Name}}\t{{.Status}}'
lab-down:
> $(COMPOSE) down
lab-ps:
> @$(COMPOSE) ps --format 'table {{.Name}}\t{{.Status}}\t{{.Image}}'
lab-logs:
> docker logs -f --tail 50 rl-$(T)
lab-check-ext:
> docker exec rl-ext python3 /work/lab/verify.py --vantage external
lab-check-ctl:
> docker exec rl-ctl python3 /work/lab/verify.py --vantage control
lab-check: lab-check-ext lab-check-ctl
lab-proof:
> bash lab/proof.sh
probe-dry:
> docker exec rl-ext python3 -m resolverlens.cli probe --config config/config.yaml --dry-run
probe:
> docker exec rl-ext python3 -m resolverlens.cli probe --config config/config.yaml $(if $(RUN),--run-id $(RUN),)
