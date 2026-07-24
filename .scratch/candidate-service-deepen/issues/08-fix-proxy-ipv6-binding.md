# 08 — Fix proxy IPv4/IPv6 binding: proxy.mjs listen on both addresses

**What to build:** Fix proxy.mjs so Playwright's IPv6 localhost resolution (`::1:3099`) doesn't get ECONNREFUSED when the proxy only binds to `127.0.0.1` (IPv4). Currently `server.listen(PORT, "127.0.0.1", ...)` binds to IPv4 only.

**Blocked by:** None

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] Change proxy.mjs server.listen from `"127.0.0.1"` to `"0.0.0.0"` (both IPv4 + IPv6)
- [ ] Verify: `curl -6 http://localhost:3099/api/auth/setup-status` succeeds
- [ ] Verify: `E2E_BASE_URL=http://localhost:3099 npx playwright test e2e/login-setup.spec.ts` passes consistently (run 3 times)
- [ ] `bash frontend/e2e/run-e2e-docker.sh --skip-setup` — login-setup step passes (no ECONNREFUSED)
- [ ] `ruff check --fix` và `ruff format` chạy clean (proxy.mjs không cần ruff)

## Instructions
1. Commit trực tiếp lên main
2. Dùng skill implement
3. Báo cáo kết quả
