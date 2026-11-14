# Pilot sandbox image (decision 0002-A2). Build from the QCA/ root:
#   docker build -f 03_framework/sandbox/Dockerfile -t cec-pilot:0.1 .
# Fixture 2:  docker build -f 03_framework/sandbox/Dockerfile --build-arg REPO=pilot_repo2 -t cec-pilot2:0.1 .
# Pin the base image by digest at the pilot freeze.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pytest==8.3.5 ruff==0.11.8
# semgrep is deliberately NOT installed: SEC-INPUT-002 must evaluate to unknown(checker_unavailable) in the pilot.

# /repo is owned by root and read-only for the agent user; the edit tool (docker exec -u root) is the only write path.
ARG REPO=pilot_repo
COPY 04_benchmark/repositories/${REPO} /repo
RUN useradd --create-home --shell /bin/bash agent \
    && cd /repo && git init -q && git -c user.email=pilot@local -c user.name=pilot add -A \
    && git -c user.email=pilot@local -c user.name=pilot commit -qm "pilot base" \
    && chown -R root:root /repo && chmod -R a+rX,go-w /repo \
    && git config --system --add safe.directory /repo
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /repo
