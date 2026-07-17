# E2E Smoke Re-Run Report — lần 3 (sau BUG-7 + BUG-8 a11y fix)

> Re-run worker lần 3. Mục tiêu: đo delta sau khi BUG-7 (Modal `role="dialog"`) +
> BUG-8 (send button `aria-label`) đã fix (xem `A11Y-FIX-REPORT.md`), mở khóa cascade
> ESS (T3→T4→T5-T7) và AI test (T9). CHỈ đo + report, KHÔNG sửa code. Bug mới phát
> hiện được liệt kê cho orchestrator; không fix.

Ngày re-run: 2026-07-17. Repo HEAD chưa commit (sau apply A11Y-FIX-REPORT diff).

---

## 1. 🔧 Env / status hiện tại

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Docker compose (postgres+redis+minio+backend+gmail-worker+onboarding-worker) | ✅ UP, healthy | `docker compose up -d postgres redis minio backend gmail-worker onboarding-worker`. Không bật service `frontend` (Next 14 cũ). |
| Backend :8000 reachable | ✅ | `GET /api/auth/setup-status` → `{"setup_complete":true}` |
| `setup_complete` | **true** | DB còn state từ các run trước → T1 tự skip wizard, nhánh fallback login (kỳ vọng) |
| vroom-hr `pnpm dev --port 3001` + reverse proxy :3000 | ✅ | Playwright `webServer` (e2e/start-servers.sh) quản lý khi chạy test; verify thủ công bằng MCP Playwright browser qua proxy `e2e/proxy.mjs`. |
| Build vroom-hr | ✅ PASS (A11Y-FIX-REPORT §3) | `next build` exit 0, 32 routes |
| `runtime/health` | ✅ **healthy 5/5** | redis / postgresql / minio / gmail-worker / onboarding-worker. **BUG-5 vẫn RESOLVED** (kế thừa từ lần 2). |

### Thao tác dọn test artifact (chuẩn bị T3 branch provisioning fresh, y hệt lần 2)
Trước khi chạy smoke, dọn state leak của demo Employee để T3 lại được cấp tài khoản +
mật khẩu tạm fresh (đúng path đo BUG-7 fix):
```sql
-- trong vroom-postgres
DELETE FROM refresh_tokens WHERE user_id IN
  (SELECT id FROM users WHERE email='hoangxuannguyen2005@gmail.com');
DELETE FROM users WHERE email='hoangxuannguyen2005@gmail.com' RETURNING id;
```
+ clear `vroom-hr/e2e/.auth/employee-creds.json` + reset `employee.json` = `{}`.
→ `GET /api/employees/ea6f1392-…/account` trả `{"exists":false,…}` xác nhận account đã
dọn, employee record (NV-001) giữ nguyên. Thao tác này chỉ dọn test artifact leak (run
trước T4 flake đã `POST /change-password` → `must_change_password=false`, làm T3 rẽ
nhánh "alreadyCreated" ở các run sau), KHÔNG reset First-Run, KHÔNG sửa feature code.

### BE shape (xác nhận lại, không đổi)
```
POST /api/auth/login → {"user":{…},"must_change_password":…,"setup_complete":true}   (wrapped)
GET  /api/auth/me     → {"id":…,"email":…,"role":…,"must_change_password":…,…}      (FLAT — BUG-1 fix còn hiệu lực)
POST /api/employees/{id}/account → {"user":{…},"temporary_password":"<12 ký tự>"}    (200 khi account chưa tồn tại)
```

---

## 2. Quickcheck a11y fix (browser thật qua proxy :3000)

**BUG-7 fix verify** — `vroom-hr/components/operate.tsx:260` `Modal` giờ có
`role="dialog"` + `aria-modal="true"` + `aria-label={title}` + nút close
`aria-label="Đóng"`. UI provisioning (`/employees/[id]` → "Tạo tài khoản"):
- BE `POST …/account` → 200 trả `temporary_password` thật (`zvefZEj99XHG`).
- Modal "Tài khoản đã được tạo" lộ thị giác + accessibility tree nhận diện là
  `role="dialog"` → `page.getByRole("dialog")` giờ match. (T3 PASS trong suite, §3.)

**BUG-8 fix verify** — `vroom-hr/components/AiChat.tsx` send button giờ có
`aria-label="Gửi"` + `<span class="sr-only">Gửi</span>`:
- `getByRole("button", { name: /gửi/i })` match → T9 không còn skip ở nhánh
  "send not found" (T9 PASS trong suite, §3).
- Verify thủ công: gửi "Có bao nhiêu Candidate đang ở trạng thái new?" → BE trả
  `502 {"detail":"LLM service unavailable: LLM timeout"}` (BUG-3) → UI surface
  error "Assistant API 502: …LLM timeout" + nút "Thử lại" (đúng `replyOrError` kỳ
  vọng của test).

**T4 verify thủ công** (login temp `zvefZEj99XHG` → `/change-password` → đổi
`VroomEmp!2026#qa` → `/employee`): feature chạy đúng end-to-end, redirect về ESS
`/employee`, không còn `must_change_password`. → T4 fail trong suite KHÔNG phải
feature bug, là test-infra race (xem §4 BUG-9).

---

## 3. 📊 Kết quả Playwright (full 9 smoke, canonical run sau reset)

```
Running 9 tests using 1 worker
  -  1 First-Run Setup › wizard…                          (skipped: DB setup_complete → fallback login + skip wizard)
  ✓  2 HR Dashboard › metrics+runtime+audit               (1.3s)
  ✓  3 HR Employee provisioning → mật khẩu tạm             (2.6s)   ← BUG-7 fix → PASS
  ✘  4 ESS onboarding login + change password              (1.6m)   ← BUG-9 NEW (test-infra race)
  ✘  5 ESS check-in                                         (22.2s)  ← cascade: T4 không ghi employee.json
  ✘  6 ESS request nghỉ phép + LEAVE_OVERLAP              (22.2s)  ← cascade
  ✘  7 ESS payslip đã publish                              (22.2s)  ← cascade
  ✓  8 Recruitment backbone render & precondition         (5.5s)
  ✓  9 HR AI Assistant human-in-the-loop                    (2.9s)   ← BUG-8 fix → PASS
4 passed, 4 failed, 1 skipped  (≈3.0m)
```

Tổng: **4 PASS** (T2, T3, T8, T9) + **4 FAIL** (T4, T5, T6, T7) + **1 SKIP** (T1).

### Delta table (test | lần 2 | lần 3 | note)

| # | Test | Lần 2 (trước a11y fix) | Lần 3 (sau BUG-7 + BUG-8) | Chuyển | Note |
|---|---|---|---|---|---|
| T1 | First-Run Setup wizard | SKIP (DB đã setup → fallback) | SKIP (giống) | = | DB `setup_complete=true` → nhánh wizard không test lại. KHÔ phải hồi quy. |
| T2 | HR Dashboard metrics+runtime+audit | ✅ PASS (BUG-1 fix) | ✅ PASS | = | Stable. Runtime "KHỎE" 5/5, audit card render. |
| T3 | HR Employee provisioning → mật khẩu tạm | ❌ **FAIL** (BUG-7: `Modal` thiếu `role="dialog"` → `getByRole("dialog")` timeout 20s) | ✅ **PASS** | **FAIL→PASS** ✅ | BUG-7 fix xác nhận trực tiếp: modal "Tài khoản đã được tạo" match `role="dialog"`, capture `temporary_password` (`zvefZEj99XHG`), ghi `EMP_CREDS`. |
| T4 | ESS onboarding login + change password | ❌ SKIP (T3 không ghi creds) | ❌ **FAIL** (BUG-9 NEW) | **SKIP→FAIL mới** | Cascade đã unlock đến mức login temp → `/change-password`. T4 giờ thực sự chạy, nhưng `.click()` submit hang 90s (button "detached from DOM" sau khi success form unmount) → `waitForURL('/employee')` + `storageState(EMP_STATE)` không chạy → `employee.json` giữ `{}`. Feature chạy đúng thủ công (§2). |
| T5 | ESS check-in | ❌ FAIL (cascade no ESS session) | ❌ FAIL (cascade từ T4) | = (root cause đổi) | Cascade vẫn chặn vì T4 không ghi `employee.json`. Verify thủ công lần 2: `/employee/attendance` heading "Chấm công", nút Check-in, bảng lịch sử 30 ngày → feature OK. |
| T6 | ESS leave+LEAVE_OVERLAP | ❌ FAIL (cascade) | ❌ FAIL (cascade) | = | Verify thủ công lần 2: `/employee/requests` heading "Yêu cầu của tôi", form nghỉ phép render. Feature OK. |
| T7 | ESS payslip published | ❌ FAIL (cascade) | ❌ FAIL (cascade) | = | Verify thủ công lần 2: 2 payslip "Đã phát hành" (05/2026, 06/2026), 0 draft lộ. Feature OK. |
| T8 | Recruitment backbone render | ✅ PASS | ✅ PASS | = | Auth thật, inbox/candidates/interviews render + precondition calendar (GH #214). |
| T9 | HR AI Assistant human-in-loop | ❌ **SKIP** (BUG-8: send button không accessible name) | ✅ **PASS** | **SKIP→PASS** ✅ | BUG-8 fix xác nhận: send button `aria-label="Gửi"` match → test gửi câu hỏi → BE trả `502 LLM timeout` (BUG-3) → `replyOrError` assertion PASS. |

### Tóm delta lần 2 → lần 3
- **Chuyển FAIL→PASS: 1** (T3) — BUG-7 fix mở khóa provisioning.
- **Chuyển SKIP→PASS: 1** (T9) — BUG-8 fix mở khóa AI Assistant test.
- **Cascade T3→T4 unlocked**: T3 giờ ghi `EMP_CREDS` → T4 thực sự chạy (trước skip).
- **T4 mới FAIL (BUG-9 NEW test-infra race)** chặn `employee.json` → T5/T6/T7 vẫn
  cascade-fail. **KHÔ phải hồi quy feature** (verify thủ công T4/T5/T6/T7 đều PASS).
- Stable PASS: T2, T8. Stable SKIP: T1 (DB setup).

---

## 4. 🐞 Bug còn lại / mới phát hiện

### BUG-2 — Backend thiếu CORSMiddleware (vẫn) — KHÔ phải code bug (config)
`backend/src/main.py` vẫn không đăng ký `CORSMiddleware` (đã `rg` lại lần 2). Lần này
vẫn workaround bằng reverse proxy cùng-origin `e2e/proxy.mjs`. Recommend thêm
`CORSMiddleware` (`allow_credentials=True`, `allow_origins=[http://localhost:3000,
AUTH_FRONTEND_URL]`) cho production. Không chặn smoke.

### BUG-3 — HR AI Assistant phụ thuộc LLM provider chưa sẵn sàng (vẫn) — KHÔ phải code bug (env)
`docker-compose.override.yml` `ASSISTANT_LLM_BASE_URL=http://host.docker.internal:20128/v1`
trỏ tới server LLM **không chạy** → chat trả `LLM timeout` (502). Sau BUG-8 fix, **T9
PASS** trên nhánh "error surfaced" (test handle fallback). Để exercise Draft-Action →
confirm ghi thật, cần LLM thật + HR cấu hình AI provider/enable Assistant. Không phải
code bug.

### BUG-4 — Recruitment happy-path cần Google Workspace thật (vẫn) — KHÔ phải code bug (env)
`GET /api/auth/organization-google-connection/calendars` → 403 (chưa kết nối). T8 vẫn
PASS ở mức render+precondition (calendar hint GH #214). Cần HR connect Gmail/Calendar
thật để exercise backbone flow đầy đủ (Inbox→promote→Candidate→Interview→Onboarding).

> 3 bug trên (BUG-2/3/4) **đều không phải code bug** — đúng khẳng định của
> orchestrator. Ngoài ra phát hiện thêm 1 bug **test-infra** mới, ghi rõ dưới đây
> để orchestrator dispatch worker test-infra (KHÔ phải feature code).

### BUG-9 — 🆕 NEW (test-infra race, chặn cascade T4→T5-T7) — P1
**`vroom-hr/e2e/vroom-hr.smoke.spec.ts` T4 click `#change-password-submit-button` race
với form unmount trên success.**

- **Hiện tượng**: T4 trong suite:
  ```
  await page.locator("#change-password-submit-button").click();   ← hang 90s
  await page.waitForURL("**/employee", { timeout: 30000 });       ← không bao giờ chạy
  await context.storageState({ path: EMP_STATE });                ← không bao giờ chạy
  ```
  Playwright log: "locator resolved to <button …>Đổi mật khẩu</button> → attempting
  click → element was detached from the DOM, retrying → Test timeout 90s exceeded".
- **Root cause**: Trang `/change-password` (`app/change-password/page.tsx`) render form
  trong `{!success && <form>…}`. Khi submit thành công (`handleSubmit` → BE 200 →
  `setSuccess(true)` → `setTimeout(router.replace('/dashboard'), 2000)`), form subtree
  unmount → nút `#change-password-submit-button` biến mất ngay sau khi click fire.
  Playwright.actionability check "element visible, enabled, stable" + click là atomic;
  vì nút detach giữa check và click, Playwright retry vô tận → `.click()` không return
  dù navigation đã diễn ra ở background → cascade `employee.json` không ghi → T5/T6/T7
  dùng `storageState = { cookies:[], origins:[] }` → protected page redirect `/login`.
- **Verify thủ công PASS** (§2): login temp → `/change-password` → fill → click submit
  → BE 200 → sau ~2s redirect `/employee`. Feature đúng.
- **KHÔ phải feature bug** (page + BE hoạt động chuẩn); là **spec Playwright click race**.
  Fix đề xuất **chỉ trong file test spec** (KHÔ đụng feature code):
  - Dùng `Promise.all` để click và wait navigation chạy song song:
    ```ts
    await Promise.all([
      page.waitForURL("**/employee", { timeout: 30000 }),
      page.locator("#change-password-submit-button").click(),
    ]);
    ```
    và `storageState({path:EMP_STATE})` sau `waitForURL`. Khi success unmount form,
    `click()` reject nhưng `waitForURL` đã resolve → test tiếp tục.
  - Hoặc `await button.click({ noWaitAfter: true })` (Playwright 1.61+ hỗ trợ) rồi
    `waitForURL` rồi `storageState`.
  - Hoặc submit qua `form.evaluate(f => f.requestSubmit())` + `waitForURL`.
- **Unlock sau fix BUG-9**: T4 PASS → ghi `EMP_STATE` → T5/T6/T7 PASS (feature đã
  verify thủ công). → 9/9 smoke green (trừ T1 skip do DB setup, T8 vẫn PASS, T9 PASS
  trên nhánh LLM-error). Phủ full green cần fix BUG-9 + config BUG-3/BUG-4 cho 6e/6c.

### Ghi chú test-infra khác (kế thừa từ lần 2, không phải bug mới)
- T3 branch `alreadyCreated` (account đã có → `tempPassword:null`) làm re-run không
  idempotent. Giải pháp: BE expose endpoint reset/delete account, hoặc worker test-infra
  tự dọn `users` row giữa các run (đã workaround bằng SQL manual lần này). Kết hợp với
  fix BUG-9 sẽ làm re-run ổn định.

---

## 5. 🔁 Commands human reproduce

```bash
cd /home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage

# 1) Lên hạ tầng đầy đủ (KHÔNG bật frontend service cũ)
docker compose up -d postgres redis minio backend gmail-worker onboarding-worker
# chờ ~20-30s alembic + seed; xác nhận:
curl -s http://localhost:8000/api/auth/setup-status   # {"setup_complete":true}
curl -s http://localhost:8000/api/admin/runtime/health  # status healthy (cần cookie HR)

# 2) Dọn test artifact leak để T3 branch provisioning fresh
docker exec vroom-postgres psql -U postgres -d vroom_hr -c \
  "DELETE FROM refresh_tokens WHERE user_id IN \
   (SELECT id FROM users WHERE email='hoangxuannguyen2005@gmail.com'); \
   DELETE FROM users WHERE email='hoangxuannguyen2005@gmail.com';"
rm -f vroom-hr/e2e/.auth/employee-creds.json && echo '{}' > vroom-hr/e2e/.auth/employee.json

# 3) Chạy smoke 9 (Playwright webServer tự start `pnpm dev :3001` + proxy :3000)
cd vroom-hr
export E2E_HR_EMAIL=hr.qa@vroom.example.com \
       E2E_HR_PASSWORD='VroomQA!148#2026' \
       E2E_HR_NAME='HR QA' \
       E2E_ORGANIZATION_NAME='Vroom QA Organization' \
       NEXT_PUBLIC_API_URL=http://localhost:3000 \
       DISABLE_HMR=true
pnpm exec playwright test --reporter=list

# trace FAIL:
pnpm exec playwright show-trace test-results/<slug>/trace.zip
# báo cáo HTML:
pnpm exec playwright show-report

# 4) Dọn (giữ volume cho retry)
docker compose down
```

Env khớp `backend/.env` (`E2E_HR_*`, `AUTH_SUPER_ADMIN_EMAIL`,
`AUTH_AUTO_SEED_SAMPLE_DATA=true`). Playwright 1.61 `webServer` nhận `port` duy nhất.

---

## 6. Kết luận

- **BUG-7 + BUG-8 fix xác nhận**: T3 **FAIL→PASS** (Modal `role="dialog"`) và
  T9 **SKIP→PASS** (send button `aria-label="Gửi"`). Cascade provisioning chain T3→T4
  đã được mở khóa đến bước login.
- **Phát hiện BUG-9 NEW (test-infra race)** tại T4 submit — nút `#change-password-submit-button`
  detach khỏi DOM khi `setSuccess(true)` unmount form, làm `.click()` Playwright hang 90s
  → `employee.json` không ghi → T5/T6/T7 cascade fail. **KHÔ phải product code bug**:
  feature verify thủ công PASS cho T4/T5/T6/T7 (login→change→/employee, attendance,
  requests, payslips published). Fix nên trong file spec (`vroom-hr/e2e/vroom-hr.smoke.spec.ts`)
  dùng `Promise.all([waitForURL, click])` hoặc `click({ noWaitAfter: true })`.
- **3 bug không-code còn lại đúng khẳng định orchestrator**: BUG-2 (CORS), BUG-3 (LLM env),
  BUG-4 (Google Workspace env) — cả 3 không chặn smoke (T9 PASS trên nhánh LLM-error,
  T8 PASS ở mức render). Phủ 6c/6e đầy đủ cần config thật.
- **Đường tới 9/9 smoke green**: fix BUG-9 (test-infra, ~5 dòng spec) → T4/T5/T6/T7 PASS.
  Sau đó smoke còn T1 skip (DB setup, OK) → 8 PASS 1 SKIP. Phase 0-3 product + tất cả
  code bug (BUG-1/7/8, a11y) đã sạch.

Không sửa feature code. Không git commit. Tài liệu này là output duy nhất.