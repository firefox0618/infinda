#!/usr/bin/env bash

set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000/api/health/}"
WEB_URL="${WEB_URL:-http://127.0.0.1:3000/api/health}"

check_endpoint() {
  local name="$1"
  local url="$2"

  echo "Checking ${name}: ${url}"
  local response
  response="$(curl -fsS "$url")"
  echo "${response}"
  echo "${response}" | grep -q '"status":"ok"'
}

check_endpoint "api" "$API_URL"
check_endpoint "web" "$WEB_URL"

echo "Smoke check passed."
