#!/usr/bin/env bash
# Idempotent repository bootstrap for Cloud Agents.
# Node dependencies come from the lockfile. Python tools live in .venv.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# The default image has Python 3.12 but not the venv module.
if ! python3.12 -c "import ensurepip" >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12-venv
fi

npm ci

if [[ ! -x "$ROOT/.venv/bin/pip" ]]; then
  rm -rf "$ROOT/.venv"
fi
python3.12 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install -e ".[dev,coach]"
