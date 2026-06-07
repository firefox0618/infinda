#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/dextrmed/Project/infinda"
STACK_SCRIPT="$ROOT_DIR/tests/web/start_e2e_stack.sh"
WEB_DIR="$ROOT_DIR/apps/web"

cleanup() {
  if [[ -n "${STACK_PID:-}" ]]; then
    kill "$STACK_PID" >/dev/null 2>&1 || true
    wait "$STACK_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

bash "$STACK_SCRIPT" &
STACK_PID=$!

for _ in $(seq 1 120); do
  if curl -sf http://127.0.0.1:8000/api/health/ >/dev/null && curl -sf http://127.0.0.1:3000/api/health >/dev/null; then
    cd "$WEB_DIR"
    PLAYWRIGHT_SKIP_WEBSERVER=1 NODE_PATH=./node_modules playwright test -c ../../tests/web/playwright.config.ts
    exit $?
  fi
  sleep 1
done

echo "E2E stack failed to start in time" >&2
exit 1
