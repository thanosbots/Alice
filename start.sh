#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -f .updates/python ]]; then
  IFS= read -r updated_python < .updates/python
  if [[ -x "$updated_python" ]]; then
    exec "$updated_python" main.py
  fi
fi
if [[ ! -x .venv/bin/python ]]; then
  bash setup.sh
fi
exec .venv/bin/python main.py
