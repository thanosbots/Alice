#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Install only into this project. uv supplies a compatible Python if necessary.
if [[ ! -x .bootstrap/bin/uv ]]; then
  python3 -m venv .bootstrap
  .bootstrap/bin/python -m pip install --disable-pip-version-check uv
fi
export UV_PYTHON_INSTALL_DIR="$PWD/.python"
export UV_CACHE_DIR="$PWD/.uv-cache"
if [[ ! -x .venv/bin/python ]]; then
  .bootstrap/bin/uv venv --python 3.11 .venv
fi
.bootstrap/bin/uv pip install --python .venv/bin/python -r requirements.txt
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo 'FFmpeg is required: macOS: brew install ffmpeg | Ubuntu: sudo apt install ffmpeg'
  exit 1
fi
if [[ ! -f Config.env ]]; then
  cp Config.env.example Config.env
  echo 'Fill in your Telegram and MongoDB settings in Config.env.'
fi
echo 'Setup complete. Music needs no API key or extra service.'
echo 'Verify music: .venv/bin/python scripts/check_music.py'
echo 'Start bot: ./start.sh'
