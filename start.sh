#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -f .updates/python ]]; then
  IFS= read -r updated_python < .updates/python
  if [[ -x "$updated_python" ]]; then
    if ! "$updated_python" -c "from Crypto.Cipher import DES" >/dev/null 2>&1; then
      bash setup.sh
      UV_CACHE_DIR="$PWD/.uv-cache" .bootstrap/bin/uv pip install --python "$updated_python" -r requirements.txt
    fi
    exec "$updated_python" main.py
  fi
fi
if [[ ! -x .venv/bin/python ]] || ! .venv/bin/python -c "from Crypto.Cipher import DES" >/dev/null 2>&1; then
  bash setup.sh
fi
exec .venv/bin/python main.py
