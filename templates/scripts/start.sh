#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

FRONTEND_DIR="${FRONTEND_DIR:-src/web}"
BACKEND_DIR="${BACKEND_DIR:-src/api}"
FRONTEND_CMD="${FRONTEND_CMD:-npm run dev}"
BACKEND_CMD="${BACKEND_CMD:-npm run dev}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

FRONTEND_PATH="$ROOT_DIR/$FRONTEND_DIR"
BACKEND_PATH="$ROOT_DIR/$BACKEND_DIR"

if [[ ! -d "$FRONTEND_PATH" ]]; then
  echo "Frontend directory not found: $FRONTEND_PATH" >&2
  exit 1
fi

if [[ ! -d "$BACKEND_PATH" ]]; then
  echo "Backend directory not found: $BACKEND_PATH" >&2
  exit 1
fi

if [[ ! -f "$FRONTEND_PATH/package.json" ]]; then
  echo "Missing package.json in frontend directory: $FRONTEND_PATH" >&2
  exit 1
fi

if [[ ! -f "$BACKEND_PATH/package.json" ]]; then
  echo "Missing package.json in backend directory: $BACKEND_PATH" >&2
  exit 1
fi

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting backend: $BACKEND_CMD ($BACKEND_DIR)"
bash -lc "cd \"$BACKEND_PATH\" && $BACKEND_CMD" &
BACKEND_PID=$!

echo "Starting frontend: $FRONTEND_CMD ($FRONTEND_DIR)"
bash -lc "cd \"$FRONTEND_PATH\" && $FRONTEND_CMD" &
FRONTEND_PID=$!

sleep 2

if command -v open >/dev/null 2>&1; then
  open "$FRONTEND_URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$FRONTEND_URL" >/dev/null 2>&1 || true
fi

echo "Frontend URL: $FRONTEND_URL"
echo "Press Ctrl+C to stop frontend and backend."

wait "$BACKEND_PID" "$FRONTEND_PID"
