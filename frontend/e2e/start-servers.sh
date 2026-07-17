#!/usr/bin/env bash
# Single Playwright `webServer.command`:
#   1) starts `next dev` (vroom-hr) on :3001 in the background
#   2) waits for it to answer
#   3) execs the reverse proxy on :3000 in the foreground (this process
#      becomes the webServer process Playwright supervises/kills)
# The browser only ever talks to http://localhost:3000 (same-origin), so the
# backend's Secure; SameSite=Lax HttpOnly cookie is carried and no CORS
# preflight is required (the FastAPI backend has no CORSMiddleware).
set -euo pipefail

cd "$(dirname "$0")/.."

# Cleanup any stale Next dev server bound to :3001.
if command -v fuser >/dev/null 2>&1; then fuser -k 3001/tcp 2>/dev/null || true; fi

# Start Next dev for vroom-hr on :3001.
pnpm dev --port 3001 &
NEXT_PID=$!

cleanup() {
  kill "$NEXT_PID" 2>/dev/null || true
  wait "$NEXT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait for Next dev to accept connections (it compiles on first request).
for i in $(seq 1 90); do
  if curl -sf -o /dev/null http://localhost:3001/; then
    echo "[start-servers] Next dev ready on :3001"
    break
  fi
  sleep 1
done

# Run the proxy in the foreground — Playwright supervises this process.
exec node e2e/proxy.mjs