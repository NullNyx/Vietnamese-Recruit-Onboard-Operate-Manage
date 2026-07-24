# 09 — Fix ci-health spec: use E2E_BASE_URL instead of hardcoded localhost:3000

**What to build:** Update `ci-health.spec.ts` to use `E2E_BASE_URL` env var (hoặc baseURL from config) instead of hardcoded `http://localhost:3000`. Test hiện tại gọi API trực tiếp vào port 3000 của Next.js thay vì qua proxy.

**Blocked by:** None (independent)

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] `ci-health.spec.ts` line 9: replace `"http://localhost:3000"` with dynamic base URL
- [ ] Cách fix: dùng `page.request.baseURL` hoặc đọc từ env var `E2E_BASE_URL`
- [ ] Chạy với proxy: `E2E_BASE_URL=http://localhost:3099 npx playwright test e2e/ci-health.spec.ts` → 2 tests pass
- [ ] Chạy không proxy (fallback): `npx playwright test e2e/ci-health.spec.ts` → 2 tests pass (dùng localhost:3000)
- [ ] `bash frontend/e2e/run-e2e-docker.sh --skip-setup` — ci-health tests pass

## Instructions
1. Commit trực tiếp lên main
2. Dùng skill implement
3. Báo cáo kết quả
