#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_BIN="${UV_BIN:-uv}"
export UV_PYTHON="${UV_PYTHON:-3.11}"

if ! command -v "$UV_BIN" >/dev/null 2>&1; then
  echo "Error: uv is required but was not found in PATH." >&2
  exit 1
fi

REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "Error: requirements.txt not found at $REQUIREMENTS_FILE." >&2
  exit 1
fi

ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

VENV_DIR="${UV_VENV_DIR:-$PROJECT_ROOT/.venv}"
PYTHON_BIN="$VENV_DIR/bin/python"
REQUIREMENTS_HASH_FILE="$VENV_DIR/.requirements.sha256"

if [ ! -d "$VENV_DIR" ]; then
  "$UV_BIN" venv "$VENV_DIR"
fi

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Error: Python interpreter not found in $VENV_DIR." >&2
  exit 1
fi

CURRENT_HASH="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"
INSTALLED_HASH=""
if [ -f "$REQUIREMENTS_HASH_FILE" ]; then
  INSTALLED_HASH="$(<"$REQUIREMENTS_HASH_FILE")"
fi

if [ "$CURRENT_HASH" != "$INSTALLED_HASH" ]; then
  echo "Dependencies changed, installing with uv..."
  echo "This may take a few minutes on first run..."
  "$UV_BIN" pip install --python "$PYTHON_BIN" --requirement "$REQUIREMENTS_FILE" --verbose
  if [ $? -eq 0 ]; then
    echo "$CURRENT_HASH" > "$REQUIREMENTS_HASH_FILE"
    echo "Dependencies installed successfully!"
  else
    echo "Error: Failed to install dependencies" >&2
    exit 1
  fi
else
  echo "Dependencies are up to date, skipping installation."
fi

cd "$PROJECT_ROOT"

MODE="backend"
if [ ${#} -gt 0 ]; then
  MODE="$1"
  shift
fi

run_backend() {
  exec env \
    http_proxy= \
    https_proxy= \
    HTTP_PROXY= \
    HTTPS_PROXY= \
    ALL_PROXY= \
    all_proxy= \
    NO_PROXY= \
    no_proxy= \
    "$PYTHON_BIN" web/backend/app.py "$@"
}

case "$MODE" in
  backend)
    run_backend "$@"
    ;;
  *)
    echo "Usage: $0 [backend] [-- additional-args]" >&2
    exit 1
    ;;
esac
