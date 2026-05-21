#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from https://www.python.org/downloads/ or Homebrew."
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  else
    echo "ffmpeg is required. Install Homebrew first, then run: brew install ffmpeg"
    exit 1
  fi
fi

if [ ! -d ".local-ai" ]; then
  python3 -m venv .local-ai
fi

. .local-ai/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

if [ ! -f certs/localhost.crt ] || [ ! -f certs/localhost.key ]; then
  mkdir -p certs
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout certs/localhost.key \
    -out certs/localhost.crt \
    -days 365 \
    -subj "/CN=localhost"
fi

APP_ROOT="$PWD" \
WEB_DIR="$PWD/web" \
DATA_DIR="$PWD/data" \
MAX_UPLOAD_MB=0 \
DEFAULT_SOURCE_LANG=auto \
DEFAULT_TARGET_LANG=en \
SUPERTONIC_VOICE=M1 \
SUBTITLE_STYLE=bold \
SUBTITLE_POSITION=bottom \
SUBTITLE_SIZE=100 \
SUBTITLE_FONT="Noto Sans" \
MIN_DUB_SPEED=0.85 \
MAX_DUB_SPEED=1.75 \
uvicorn backend.app.main:app \
  --host 127.0.0.1 \
  --port 8801 \
  --ssl-certfile certs/localhost.crt \
  --ssl-keyfile certs/localhost.key
