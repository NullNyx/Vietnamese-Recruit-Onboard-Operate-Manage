# 07 — E2E test infrastructure: Docker-compatible test runner

**What to build:** Create a Docker-compatible E2E test runner that starts the proxy (pointing to Docker backend + frontend), seeds the DB with test data, generates fresh auth state files, and runs Playwright tests. Currently E2E tests only work with `start-servers.sh` (Next.js dev on :3001 + proxy on :3000), not against Docker Compose (frontend on :3000 directly).

**Blocked by:** None (independent of recruitment refactor)

**Status:** ready-for-agent

**Acceptance criteria:**

### 1. Proxy integration
- [ ] `frontend/e2e/start-e2e-docker.sh` script created that:
  - Starts the proxy (`node e2e/proxy.mjs`) on a non-conflicting port (e.g. 3099)
  - `BACKEND_URL=http://localhost:8000` (Docker backend)
  - `FRONTEND_URL=http://localhost:3000` (Docker frontend)
  - Waits for proxy health (`/api/auth/setup-status` returns 200)
- [ ] `E2E_BASE_URL` env var properly forwarded to Playwright (maps to proxy port)

### 2. DB seed for E2E
- [ ] `backend/scripts/seed_e2e.py` (hoặc SQL script) created with:
  - Sets `setup_complete = false` trong Organization settings (cho First-Run Setup tests)
  - Hoặc seeds đầy đủ dữ liệu cho HR Dashboard tests (Candidates, Employees, etc.)
  - Configurable via `E2E_SEED_MODE=fresh|seeded` env var
- [ ] Script chạy trước Playwright: reset DB → seed → run tests

### 3. Auth state files
- [ ] `frontend/e2e/login-setup.ts` (hoặc script tương tự) tạo auth state files bằng API calls thật:
  - `hr.json` — login bằng admin credentials, lưu storage state
  - `employee.json` — login bằng employee credentials, lưu storage state
- [ ] Auth files được regenerate mỗi lần chạy test (không dùng file cũ)

### 4. Smoke runner
- [ ] `frontend/e2e/run-e2e-docker.sh` — one script to rule them all:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  
  # 1. Seed DB
  E2E_SEED_MODE=fresh python backend/scripts/seed_e2e.py
  
  # 2. Start proxy
  cd frontend && PROXY_PORT=3099 BACKEND_URL=http://localhost:8000 FRONTEND_URL=http://localhost:3000 node e2e/proxy.mjs &
  PROXY_PID=$!
  
  # 3. Generate auth state
  npx playwright test --grep "login as admin"
  
  # 4. Run full test suite
  E2E_BASE_URL=http://localhost:3099 npx playwright test
  
  # 5. Cleanup
  kill $PROXY_PID
  ```

### 5. Verify
- [ ] 15 non-API tests pass (i18n, negative tests)
- [ ] ci-health tests pass (proxy routes correctly)
- [ ] Login cascade tests pass (auth state generation works)
- [ ] Test count: 15+ passed (baseline from Docker-run)
- [ ] Existing CI tests không bị ảnh hưởng (`.github/workflows/e2e-ci.yml` uses start-servers.sh, unchanged)

## Instructions
1. Dùng skill implement
2. Test thủ công: chạy `bash frontend/e2e/run-e2e-docker.sh` và verify kết quả
3. Báo cáo code-review result + test summary
