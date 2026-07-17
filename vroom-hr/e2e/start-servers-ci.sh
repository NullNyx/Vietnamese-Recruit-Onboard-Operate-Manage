#!/usr/bin/env bash
# CI variant of start-servers.sh — uses production build (pnpm start) instead
# of dev server for faster, more reliable CI startup.
#   1) starts `next start` (vroom-hr) on :3001 in the background
#   2) waits for it to answer
#   3) execs the reverse proxy on :3000 in the foreground
set -euo pipefail

cd "$(dirname "$0")/.."

# Cleanup any stale Next server bound to :3001.
if command -v fuser >/dev/null 2>&1; then fuser -k 3001/tcp 2>/dev/null || true; fi

# Start Next production server for vroom-hr on :3001.
pnpm start --port 3001 &
NEXT_PID=$!

cleanup() {
  kill "$NEXT_PID" 2>/dev/null || true
  wait "$NEXT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait for Next to accept connections (production server starts quickly).
for i in $(seq 1 30); do
  if curl -sf -o /dev/null http://localhost:3001/; then
    echo "[start-servers-ci] Next ready on :3001"
    break
  fi
  sleep 1
done

# Run the proxy in the foreground — Playwright supervises this process.
exec node e2e/proxy.mjs
