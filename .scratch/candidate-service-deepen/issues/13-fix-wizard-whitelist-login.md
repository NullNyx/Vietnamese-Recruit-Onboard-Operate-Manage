# 13 — Fix First-Run Setup wizard test + Whitelist login timeout

**What to build:** Fix two remaining blocker issues:
1. First-Run Setup wizard test (smoke.ts:51) — Wizard container not visible after submitting the form
2. Whitelist tests (whitelist-gating.spec.ts) — Login timeout 30s

Both use UI-based login flows (not API login like login-setup.spec.ts).

**Blocked by:** None

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] Investigate First-Run Setup: smoke.ts:51 — wizard 3 bước → submit → dashboard không hiện
- [ ] Investigate Whitelist: gating.spec.ts — login button clicks but no redirect to dashboard
- [ ] Fix: ensure UI login flow works through proxy
- [ ] Tests pass when run via `bash frontend/e2e/run-e2e-docker.sh --skip-setup`

## Instructions
1. Commit trực tiếp lên main
2. Skills: implement
3. Báo cáo kết quả
