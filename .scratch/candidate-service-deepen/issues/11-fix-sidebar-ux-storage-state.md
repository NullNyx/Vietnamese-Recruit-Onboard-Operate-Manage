# 11 — Fix sidebar-ux T1-T8: storage state from admin-sidebar.json not working

**What to build:** Debug why sidebar-ux tests T1-T8 fail even after `admin.json` is copied to `admin-sidebar.json`. Tests use `test.use({ storageState })` but still fail with ENOENT or auth redirect.

**Blocked by:** None (runner already copies the file)

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] Investigate: sidebar T1 page.goto('/') → redirected to /login or heading not visible
- [ ] Check: admin-sidebar.json cookies domain/port match E2E_BASE_URL (localhost:3099)
- [ ] Check: cookies expiry not expired
- [ ] Fix: ensure cookies are valid and test loads dashboard
- [ ] T1-T8 all pass when run via `bash frontend/e2e/run-e2e-docker.sh --skip-setup`

## Instructions
1. Commit trực tiếp lên main
2. Skills: implement
3. Báo cáo kết quả
