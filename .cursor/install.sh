#!/usr/bin/env bash
# Idempotent repository bootstrap for Cloud Agents.
# Node dependencies come from the lockfile. Python tools live in .venv.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

npm ci

python3.12 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install -e ".[dev,coach]"
