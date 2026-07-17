# E2E Smoke Final Report — Full 9 Smoke

> Final re-run worker. Sau BUG-11 (T6 leave form selector) + BUG-12 (T7 payslip text leak)
> fix. Actor: re-run smoke full 9 để confirm 8+ PASS và chốt delta toàn bộ lộ trình
> worker (BUG-1 → BUG-7/8 → BUG-9 → BUG-10 → BUG-11/12). CHỈ đo + report, KHÔNG sửa
> code, KHÔNG commit.

Ngày final run: 2026-07-17. Repo HEAD chưa commit (toàn bộ fix track trong `vroom-hr/code/*FIX-REPORT.md`).

---

## 1. 🔧 Env / status

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Docker compose (postgres+redis+minio+backend+workers) | ✅ UP, healthy | `docker compose up -d postgres redis minio backend gmail-worker onboarding-worker` |
| `setup_complete` | **true** | DB còn state từ các run trước (giữ volume). T1 skip wizard (kỳ vọng). |
| Build FE (`next build`) | ✅ PASS (sanity) | 32 routes, exit 0 |
| `runtime/health` | ✅ **healthy 5/5** | redis / postgresql / minio / gmail-worker / onboarding-worker |
| vroom-hr `next dev :3001` + proxy :3000 | ✅ | Playwright `webServer` (e2e/start-servers.sh) quản lý |

### Thao tác dọn test artifact (idempotent, y hệt các run trước)
```sql
DELETE FROM refresh_tokens WHERE user_id IN
  (SELECT id FROM users WHERE email='hoangxuannguyen2005@gmail.com');
DELETE FROM users WHERE email='hoangxuannguyen2005@gmail.com';
```
+ `rm -f vroom-hr/e2e/.auth/employee-creds.json` + `echo '{}' > employee.json`
→ `GET /api/employees/{id}/account` → `{"exists":false}` (account đã dọn, employee record giữ).

---

## 2. 📊 Final Result — Full 9 Smoke

```
Running 9 tests using 1 worker

  -  1 First-Run Setup › wizard…                                    (SKIP: DB setup_complete → fallback login + hr.json)
  ✓  2 HR Dashboard › metrics+runtime+audit                         (1.2s)
  ✓  3 HR Employee provisioning → mật khẩu tạm                       (2.7s)
  ✓  4 ESS onboarding login + change password                        (5.5s)
  ✓  5 ESS check-in                                                    (1.7s)
  ✓  6 ESS request nghỉ phép + LEAVE_OVERLAP                         (4.1s)
  ✓  7 ESS payslip đã publish (draft không lộ)                        (1.7s)
  ✓  8 Recruitment backbone render & precondition                    (5.7s)
  ✓  9 HR AI Assistant human-in-the-loop                              (3.0s)

1 skipped, 8 passed (34.9s)
```

### Per-test detail

| # | Test | Status | Time | Note |
|---|---|---|---|---|
| T1 | First-Run Setup wizard | SKIP | — | DB `setup_complete=true` → fallback login ghi `hr.json` + skip wizard. KHÔ phải regression. |
| T2 | HR Dashboard metrics+runtime+audit | ✅ PASS | 1.2s | Heading "Tổng quan & Metrics", runtime "KHỎE" 5/5, audit log render. |
| T3 | HR Employee provisioning | ✅ PASS | 2.7s | Provision fresh account → modal `role=dialog` match → capture `temporary_password` → write `EMP_CREDS`. |
| T4 | ESS onboarding login + change-pw | ✅ PASS | 5.5s | Login temp → `/change-password` → `requestSubmit()` (BUG-9 fix) → cache sync (BUG-10 fix) → `/employee` → `storageState(EMP_STATE)`. |
| T5 | ESS check-in | ✅ PASS | 1.7s | ESS session từ `employee.json` → `/employee/attendance` heading "Chấm công" + Check-in button + history render. |
| T6 | ESS request nghỉ phép + LEAVE_OVERLAP | ✅ PASS | 4.1s | `getByRole("textbox",{name:/Lý do/i})` fill (BUG-11 fix) → "Gửi yêu cầu" click → first leave OK → second overlap → `LEAVE_OVERLAP` error surfaced. |
| T7 | ESS payslip đã publish (draft không lộ) | ✅ PASS | 1.7s | "Danh sách phiếu lương" + 2 "Đã phát hành" badge, `draftCount=0` (BUG-12: subtitle cấm text đã xóa + defense-in-depth filter). |
| T8 | Recruitment backbone render | ✅ PASS | 5.7s | Auth thật, inbox/candidates/interviews render + precondition calendar (GH #214). |
| T9 | HR AI Assistant human-in-the-loop | ✅ PASS | 3.0s | Send button `aria-label="Gửi"` match (BUG-8 fix) → chat → BE `502 LLM timeout` (BUG-3) → `replyOrError` assertion PASS. |

---

## 3. 📈 Delta so tất cả các run trước

| # | E2E (1st) | RERUN (2nd) | RERUN3 (3rd) | BUG-10 | FINAL | Journey |
|---|---|---|---|---|---|---|
| T1 | PASS+/SKIP | SKIP | SKIP | SKIP | SKIP | = DB setup |
| T2 | ❌ BUG-1 | ✅ | ✅ | ✅ | ✅ | **FAIL→PASS** (BUG-1) |
| T3 | ❌ BUG-1 | ❌ BUG-7 | ✅ | ✅ | ✅ | **FAIL→FAIL→PASS** (BUG-1→BUG-7) |
| T4 | ❌ SKIP | ❌ SKIP→FAIL BUG-9 | ❌ FAIL BUG-9 | ✅ | ✅ | **SKIP→FAIL→PASS** (BUG-10) |
| T5 | ❌ BUG-1 | ❌ cascade | ❌ cascade | ✅ | ✅ | **FAIL→PASS** (BUG-10) |
| T6 | ❌ BUG-1 | ❌ cascade | ❌ cascade | ❌ BUG-11 | ✅ | **FAIL→PASS** (BUG-11) |
| T7 | ❌ BUG-1 | ❌ cascade | ❌ cascade | ❌ BUG-12 | ✅ | **FAIL→PASS** (BUG-12) |
| T8 | ✅ | ✅ | ✅ | ✅ | ✅ | = stable |
| T9 | ❌ SKIP | ❌ SKIP BUG-8 | ✅ | ✅ | ✅ | **SKIP→PASS** (BUG-8) |

**Tổng quát:**
- **E2E (1st):** 1 PASS + 5 FAIL + 3 SKIP → tất cả fail do BUG-1 (session shape `/api/auth/me`).
- **RERUN (2nd):** 2 PASS + 4 FAIL + 3 SKIP → T2 PASS (BUG-1 fix); T3 lộ BUG-7 (Modal a11y) chặn cascade.
- **RERUN3 (3rd):** 4 PASS + 4 FAIL + 1 SKIP → T3 PASS (BUG-7 fix), T9 PASS (BUG-8 fix); T4 lộ BUG-9 (click race) chặn T5-T7.
- **BUG-10:** 6 PASS + 2 FAIL + 1 SKIP → T4/T5 PASS (BUG-10 fix cookie/cache + role redirect); T6/T7 lộ BUG-11/12.
- **FINAL:** **8 PASS + 1 SKIP** 🎉 — T6/T7 PASS (BUG-11/12 fix). Full green smoke.

| Run | PASS | FAIL | SKIP | Root cause blocked |
|---|---|---|---|---|
| E2E (1st) | 1 | 5 | 3 | BUG-1 session shape |
| RERUN (2nd) | 2 | 4 | 3 | BUG-7 Modal a11y |
| RERUN3 (3rd) | 4 | 4 | 1 | BUG-9 click race |
| BUG-10 | 6 | 2 | 1 | BUG-11/12 |
| **FINAL** | **8** | **0** | **1** | (chỉ env BUG-2/3/4 còn lại) |

---

## 4. 🐞 Bug còn lại (chỉ env/config, KHÔ phải code bug — xác nhận không chặn smoke)

| Bug | Description | Impact smoke? | Category |
|---|---|---|---|
| **BUG-2** | Backend thiếu CORSMiddleware | ❌ Không (workaround = reverse proxy) | Config production |
| **BUG-3** | HR AI Assistant LLM provider chưa cấu hình | ❌ Không (T9 PASS trên nhánh LLM-error surfacing) | Env dev |
| **BUG-4** | Recruitment happy-path cần Google Workspace thật | ❌ Không (T8 PASS ở mức render+precondition) | Env integration |
| **BUG-5** | gmail-worker heartbeat | ✅ RESOLVED (healthy 5/5 ở run này) | — |
| **BUG-6** | setup_complete không có cột DB | ✅ Note-only (không chặn smoke) | — |

→ **KHÔ còn code bug nào chặn smoke.** Toàn bộ 9 test xanh (8 PASS + 1 SKIP expected). Phase 0-3 product foundation + recruitment + onboarding + ESS + AI Assistant tất cả xác nhận auth + render + core data flow đúng.

---

## 5. ✅ Summary

### Kết quả
- **8/9 PASS, 1/9 SKIP** (T1 skip = DB `setup_complete=true`, kỳ vọng, không phải regression).
- Tổng thời gian: **34.9s** (giảm từ ~3.0m trước BUG-9/10 fix).
- Tất cả code bug (BUG-1, BUG-7, BUG-8, BUG-9, BUG-10, BUG-11, BUG-12) đã fix và xác nhận qua smoke.
- BE runtime healthy 5/5, `setup_complete=true`, đủ data seed (payslip published, attendance history).

### Recommandation cho human
1. **Commit toàn bộ fix:** Các file đã sửa (theo từng `*FIX-REPORT.md`):
   - `vroom-hr/lib/auth/session.ts` (BUG-1)
   - `vroom-hr/lib/api/auth.ts` (BUG-1 doc comment)
   - `vroom-hr/components/operate.tsx` Modal (BUG-7)
   - `vroom-hr/components/AiChat.tsx` send button (BUG-8)
   - `vroom-hr/e2e/vroom-hr.smoke.spec.ts` T4 requestSubmit + T6 selector (BUG-9, BUG-11)
   - `vroom-hr/app/login/page.tsx` (BUG-10 cache sync)
   - `vroom-hr/app/change-password/page.tsx` (BUG-10 cache sync + role redirect)
   - `vroom-hr/app/(employee)/employee/payslips/page.tsx` (BUG-12 subtitle + filter)
2. **Config env cho 6c/6e đầy đủ (ngoài smoke):** Cấu hình Google Workspace (BUG-4) + LLM provider (BUG-3) để test Backbone flow + AI Draft Action đầy đủ. Thêm CORSMiddleware (BUG-2) cho production.
3. **Test-infra improvement:** Làm T3 provisioning idempotent (BE expose reset/delete account endpoint hoặc spec tự dọn `users` row) để re-run không cần SQL manual. Đã note từ RERUN3 report.

---

## 6. 🔁 Commands human reproduce

```bash
cd /home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage

# 1) Lên hạ tầng
docker compose up -d postgres redis minio backend gmail-worker onboarding-worker
# chờ ~20-30s
curl -s http://localhost:8000/api/auth/setup-status   # {"setup_complete":true}

# 2) Dọn test artifact (nếu cần T3 branch provisioning)
curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"hr.qa@vroom.example.com","password":"VroomQA!148#2026"}' -c /tmp/jar.txt -o /dev/null
docker exec vroom-postgres psql -U postgres -d vroom_hr -c \
  "DELETE FROM refresh_tokens WHERE user_id IN \
   (SELECT id FROM users WHERE email='hoangxuannguyen2005@gmail.com'); \
   DELETE FROM users WHERE email='hoangxuannguyen2005@gmail.com';"
rm -f vroom-hr/e2e/.auth/employee-creds.json && echo '{}' > vroom-hr/e2e/.auth/employee.json

# 3) Chạy smoke
cd vroom-hr
export E2E_HR_EMAIL=hr.qa@vroom.example.com \
       E2E_HR_PASSWORD='VroomQA!148#2026' \
       E2E_HR_NAME='HR QA' \
       E2E_ORGANIZATION_NAME='Vroom QA Organization' \
       NEXT_PUBLIC_API_URL=http://localhost:3000 \
       DISABLE_HMR=true
pnpm exec playwright test --reporter=list
# Kỳ vọng: 8 passed, 1 skipped

# Trace FAIL (nếu có):
pnpm exec playwright show-trace test-results/<slug>/trace.zip
# Report HTML:
pnpm exec playwright show-report

# 4) Dọn
docker compose down   # giữ volume cho retry
```

---

## 7. Changelog worker (theo lộ trình)

| Worker | Bug | Fix file(s) | Report |
|---|---|---|---|
| BUG-1 | session shape `/api/auth/me` | `lib/auth/session.ts`, `lib/api/auth.ts` | BUG1-FIX-REPORT.md |
| BUG-7 | Modal thiếu `role=dialog` | `components/operate.tsx` | A11Y-FIX-REPORT.md |
| BUG-8 | send button thiếu `aria-label` | `components/AiChat.tsx` | A11Y-FIX-REPORT.md |
| BUG-9 | T4 click race (detach) | `e2e/vroom-hr.smoke.spec.ts` (T4) | BUG9-FIX-REPORT.md |
| BUG-10 | cookie cache stale + role redirect | `app/login/page.tsx`, `app/change-password/page.tsx` | BUG10-FIX-REPORT.md |
| BUG-11 | T6 reason field selector | `e2e/vroom-hr.smoke.spec.ts` (T6) | BUG11-FIX-REPORT.md |
| BUG-12 | T7 payslip text leak | `app/(employee)/employee/payslips/page.tsx` | BUG12-FIX-REPORT.md |

Không sửa feature code ngoài scope từng worker. Không git commit. Tài liệu này là output duy nhất.
