#!/usr/bin/env bash
# E2E runner for Docker Compose environment.
#
# One-script orchestration that:
#   1. Seeds/resets the DB (setup_complete=true or false)
#   2. Starts the reverse proxy on :3099, waits for health
#   3. Creates auth state files (if DB is already set up)
#   4. Runs Playwright tests
#   5. Cleans up
#
# Usage:
#   bash frontend/e2e/run-e2e-docker.sh              # First-Run flow  (setup_complete=false)
#   bash frontend/e2e/run-e2e-docker.sh --skip-setup  # Already seeded (setup_complete=true)
#   bash frontend/e2e/run-e2e-docker.sh --grep "T10"  # Run specific tests
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"  # frontend/e2e/
FRONTEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"                    # frontend/
REPO_DIR="$(cd "${FRONTEND_DIR}/.." && pwd)"                      # repo root

cd "${FRONTEND_DIR}"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROXY_PORT=3099
E2E_BASE_URL="http://localhost:${PROXY_PORT}"
BACKEND_DIR="${REPO_DIR}/backend"
SEED_SCRIPT="python scripts/seed_e2e.py"
PW_CLI="node node_modules/@playwright/test/cli.js"

SETUP_COMPLETE="false"
EXTRA_ARGS=()

# Parse flags
for arg in "$@"; do
  case "$arg" in
    --skip-setup) SETUP_COMPLETE="true" ;;
    *) EXTRA_ARGS+=("${arg}") ;;
  esac
done

# ---------------------------------------------------------------------------
# Cleanup handler
# ---------------------------------------------------------------------------
PROXY_PID=""
cleanup() {
  local exit_code=$?
  echo ""
  echo "[run-e2e] Cleaning up ..."
  if [ -n "${PROXY_PID}" ]; then
    kill "${PROXY_PID}" 2>/dev/null || true
    wait "${PROXY_PID}" 2>/dev/null || true
    echo "[run-e2e] Proxy stopped."
  fi
  echo "[run-e2e] Done (exit=${exit_code})."
  exit ${exit_code}
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# Step 1 -- Seed DB
# ---------------------------------------------------------------------------
echo "============================================"
echo "[run-e2e] Step 1 -- Seed DB"
echo "  setup_complete=${SETUP_COMPLETE}"
echo "============================================"

if [ "${SETUP_COMPLETE}" = "true" ]; then
  # Truncate, then seed_all.py creates comprehensive demo data, then override admin
  cd "${BACKEND_DIR}"
  echo "[run-e2e] Truncating DB..."
  ${SEED_SCRIPT}
  echo "[run-e2e] Running seed_all.py (comprehensive demo data)..."
  uv run python scripts/seed_all.py 2>&1 | tail -5
  echo "[run-e2e] seed_all.py done."
  echo "[run-e2e] Updating admin credentials for E2E tests..."
  python scripts/override_admin_for_e2e.py
  echo "[run-e2e] Admin override done."
  cd "${FRONTEND_DIR}"

  else
    cd "${BACKEND_DIR}"
    ${SEED_SCRIPT}
    cd "${FRONTEND_DIR}"
  fi
echo ""

# ---------------------------------------------------------------------------
# Step 2 -- Start proxy
# ---------------------------------------------------------------------------
echo "============================================"
echo "[run-e2e] Step 2 -- Start proxy on :${PROXY_PORT}"
echo "============================================"

if command -v fuser >/dev/null 2>&1; then
  fuser -k "${PROXY_PORT}/tcp" 2>/dev/null || true
fi

PROXY_PORT="${PROXY_PORT}" \
  BACKEND_URL="http://localhost:8000" \
  FRONTEND_URL="http://localhost:3000" \
  node e2e/proxy.mjs &
PROXY_PID=$!

echo "[run-e2e] Waiting for proxy health on :${PROXY_PORT} ..."
for i in $(seq 1 30); do
  if curl -sf "http://localhost:${PROXY_PORT}/api/auth/setup-status" >/dev/null 2>&1; then
    echo "[run-e2e] Proxy ready on :${PROXY_PORT}"
    break
  fi
  if [ "${i}" -eq 30 ]; then
    echo "[run-e2e] Timed out waiting for proxy on :${PROXY_PORT}" >&2
    exit 1
  fi
  sleep 1
done

echo ""

# ---------------------------------------------------------------------------
# Step 3 -- Auth state generation (skip-setup mode only)
# ---------------------------------------------------------------------------
if [ "${SETUP_COMPLETE}" = "true" ]; then
  echo "============================================"
  echo "[run-e2e] Step 3 -- Generate auth state"
  echo "============================================"

  E2E_BASE_URL="${E2E_BASE_URL}" \
    E2E_HR_EMAIL="${E2E_HR_EMAIL:-hr.qa@vroom.example.com}" \
    E2E_HR_PASSWORD="${E2E_HR_PASSWORD:-VroomQA!148#2026}" \
    ${PW_CLI} test e2e/login-setup.spec.ts \
    --grep="login and save storage state" \
    --config=playwright.config.ts \
    --reporter=list \
    --project=vroom-hr-smoke \
    --workers=1 || {
    echo "[run-e2e] WARNING: Auth state generation failed -- tests may fail" >&2
  }

  echo ""
fi

# ---------------------------------------------------------------------------
# Step 4 -- Run Playwright tests
# ---------------------------------------------------------------------------
echo "============================================"
echo "[run-e2e] Step 4 -- Run Playwright tests"
echo "============================================"

E2E_BASE_URL="${E2E_BASE_URL}" \
  ${PW_CLI} test \
  --config=playwright.config.ts \
  --reporter=list \
  "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"

EXIT_CODE=$?

echo ""
echo "============================================"
echo "[run-e2e] Tests finished (exit=${EXIT_CODE})"
echo "============================================"

exit ${EXIT_CODE}
