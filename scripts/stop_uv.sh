#!/usr/bin/env bash

set -euo pipefail

stop_target() {
  local pattern="$1"
  local label="$2"

  mapfile -t pids < <(pgrep -f -- "$pattern" || true)
  if [ "${#pids[@]}" -eq 0 ]; then
    echo "$label: no running process found."
    return
  fi

  echo "Stopping $label (PIDs: ${pids[*]})..."
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done

  local deadline=$((SECONDS + 10))
  for pid in "${pids[@]}"; do
    while kill -0 "$pid" 2>/dev/null; do
      if (( SECONDS >= deadline )); then
        echo "$label: PID $pid did not terminate, sending SIGKILL."
        kill -9 "$pid" 2>/dev/null || true
        break
      fi
      sleep 0.5
    done
  done
  echo "$label stopped."
}

MODE="backend"
if [ $# -gt 0 ]; then
  MODE="$1"
fi

case "$MODE" in
  backend)
    stop_target "web/backend/app.py" "backend service"
    ;;
  *)
    echo "Usage: $0 [backend]" >&2
    exit 1
    ;;
esac
