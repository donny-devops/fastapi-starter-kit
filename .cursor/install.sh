#!/usr/bin/env bash
set -euo pipefail

# The default Cloud Agent image ships Python 3.12 but not the venv module.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y python3.12-venv
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

# Provide a local .env from the template on first setup (never overwrite an existing one).
if [ ! -f .env ]; then
  cp .env.example .env
fi
