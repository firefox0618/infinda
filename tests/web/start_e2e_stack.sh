#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${WEB_PID:-}" ]]; then
    kill "$WEB_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

cd "$API_DIR"
{
  echo "[e2e] applying backend migrations"
  "$API_DIR/.venv/bin/python" manage.py migrate --noinput
} >/tmp/infinda-e2e-api.log 2>&1

"$API_DIR/.venv/bin/python" manage.py runserver 127.0.0.1:8000 >/tmp/infinda-e2e-api.log 2>&1 &
API_PID=$!

cd "$WEB_DIR"
{
  echo "[e2e] building frontend"
  npm run build
} >/tmp/infinda-e2e-web-build.log 2>&1

npm run start -- --hostname 127.0.0.1 --port 3000 >/tmp/infinda-e2e-web.log 2>&1 &
WEB_PID=$!

for _ in $(seq 1 120); do
  if curl -sf http://127.0.0.1:8000/api/health/ >/dev/null && curl -sf http://127.0.0.1:3000/api/health >/dev/null; then
    wait
    exit 0
  fi
  sleep 1
done

echo "E2E stack failed to start in time" >&2
exit 1
