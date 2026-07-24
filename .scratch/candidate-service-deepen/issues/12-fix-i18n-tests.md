# 12 — Fix i18n locale redirect tests (T1, T5)

**What to build:** Debug why i18n.spec.ts tests T1 (en-US locale redirect) and T5 (cookie persistence) fail in Docker environment. These tests don't need API — they should work with just the frontend.

**Blocked by:** None

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] Investigate: T1 — `en-US → / → /en/` redirect timeout
- [ ] Investigate: T5 — cookie persistence not working
- [ ] Fix or update test expectations for Docker environment
- [ ] T1, T5 pass when run via `bash frontend/e2e/run-e2e-docker.sh --skip-setup --grep "i18n"`

## Instructions
1. Commit trực tiếp lên main
2. Skills: implement
3. Báo cáo kết quả
