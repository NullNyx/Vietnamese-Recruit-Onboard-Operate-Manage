#!/usr/bin/env bash
# Start the E2E reverse proxy on port 3099 (avoids conflict with Docker
# frontend on :3000) and wait for it to answer health checks.
#
# The browser talks to http://localhost:3099 (same-origin) so the backend's
# Secure; SameSite=Lax HttpOnly auth cookie is carried and no CORS preflight
# is required (the FastAPI backend has no CORSMiddleware).
#
#   http://localhost:3099/api/*  -> http://localhost:8000  (FastAPI backend)
#   http://localhost:3099/*      -> http://localhost:3000  (Docker frontend)
#
# Usage (from frontend/):
#   bash e2e/start-proxy-docker.sh
set -euo pipefail

cd "$(dirname "$0")/.."

PROXY_PORT="${PROXY_PORT:-3099}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "[start-proxy-docker] Starting proxy on :${PROXY_PORT} ..."
PROXY_PORT="${PROXY_PORT}" \
  BACKEND_URL="${BACKEND_URL}" \
  FRONTEND_URL="${FRONTEND_URL}" \
  node e2e/proxy.mjs &
PROXY_PID=$!

# Cleanup on exit
cleanup() {
  echo "[start-proxy-docker] Cleaning up (pid ${PROXY_PID}) ..."
  kill "${PROXY_PID}" 2>/dev/null || true
  wait "${PROXY_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait for proxy to accept connections
echo "[start-proxy-docker] Waiting for proxy health on :${PROXY_PORT} ..."
for i in $(seq 1 30); do
  if curl -sf "http://localhost:${PROXY_PORT}/api/auth/setup-status" >/dev/null 2>&1; then
    echo "[start-proxy-docker] Proxy ready on :${PROXY_PORT}"
    # Keep running in foreground -- caller waits on this PID
    wait "${PROXY_PID}"
    exit $?
  fi
  sleep 1
done

echo "[start-proxy-docker] Timed out waiting for proxy on :${PROXY_PORT}" >&2
exit 1
