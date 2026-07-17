# BUG-9 Fix Report — T4 click race trong `vroom-hr/e2e/vroom-hr-smoke.spec.ts`

> Worker test-infra cho BUG-9 (KHÔNG phải feature bug — chỉ sửa file spec Playwright).
> T4 trong ESS onboarding: sau khi fill form `/change-password` và click
> `#change-password-submit-button`, nút bị detach khỏi DOM khi `setSuccess(true)`
> unmount form (`{!success && <form>}`), làm `.click()` actionability retry vô tận
> hang 90s → `waitForURL`/`storageState` không chạy → `employee.json` = `{}` →
> cascade T5/T6/T7 fail. CHỈ sửa spec, KHÔNG đụng `app/change-password` hay BE. KHÔNG commit.

Ngày fix: 2026-07-17. Scope: `vroom-hr/e2e/vroom-hr.smoke.spec.ts` (T4, ~line 199).

---

## 1. Chẩn đoán (tóm tắt từ E2E-RERUN3-REPORT §4 BUG-9)

- Trang `/change-password` (`app/change-password/page.tsx:121`) render `{!success && <form>…}`
  trong đó nút `#change-password-submit-button` (line 184). `handleSubmit` gọi BE
  `POST /api/auth/change-password` → thành công → `setSuccess(true)` → React re-render
  → `{!success && …}` false → `<form>` subtree unmount → nút detach khỏi DOM.
- Vào thời điểm `.click()` của Playwright thực hiện actionability check (visible/enabled/
  stable), BE request async ~hàng trăm ms; nếu form unmount xảy ra giữa các vòng
  actionability → "element was detached from the DOM, retrying" → không bao giờ điểm
 停下 → "Test timeout 90s exceeded" dù `router.replace('/dashboard')` (setTimeout 2s)
  đã diễn ra → `waitForURL('**/employee')` và `context.storageState({path:EMP_STATE})`
  không bao giờ chạy → `employee.json` giữ placeholder `{}` → T5/T6/T7 load `storageState
  {cookies:[],origins:[]}` → trang protected redirect `/login`.
- Feature chạy đúng thủ công (đã verify trong E2E-RERUN3-REPORT §2).

## 2. Đánh giá 3 đề xuất fix → chọn way 3

Kiểm tra API Playwright đã cài (`@playwright/test@1.61.1`,
`node_modules/.pnpm/playwright-core@1.61.1/…/types.d.ts`):

| Way | Đề xuất | Khả thi? |
|---|---|---|
| 1 | `Promise.all([page.waitForURL('**/employee'), btn.click()])` | ❌ Risk: nếu `.click()` reject ("detached") thì `Promise.all` reject → test fail dù navigation OK. Vẫn race giữa actionability check và BE 200 unmount. |
| 2 | `btn.click({ noWaitAfter: true })` | ❌ Trong Playwright 1.61 `ClickOptions.noWaitAfter` đã `@deprecated This option has no effect` (`types.d.ts:2126-2129`) → vô dụng. |
| 3 | `form.requestSubmit()` qua `page.evaluate()` | ✅ An toàn nhất: dispatch submit event synchronous, **bypass actionability hoàn toàn**, không chờ gì post-submit → return ngay → `waitForURL` chờ navigation đó xảy ra. Deterministic, không race với unmount. |

**Chọn way 3**: an toàn nhất, không phụ thuộc timing/Playwright click semantics, không
dùng API deprecated. Giữ nguyên fill 3 trường (current/new/confirm) bằng locator rồi thay
mỗi nút `.click()` bằng dispatch submit.

## 3. Diff T4

### Trước (line ~199 cũ)
```ts
        await page.locator("#change-password-confirm-input").fill(EMP_NEW_PASSWORD);
        await page.locator("#change-password-submit-button").click();   // ← hang 90s

        // After change, redirect to ESS dashboard (/employee).
        await page.waitForURL("**/employee", { timeout: 30000 });
        await context.storageState({ path: EMP_STATE });
```

### Sau (line 199-213)
```ts
        await page.locator("#change-password-confirm-input").fill(EMP_NEW_PASSWORD);
        // Race fix (BUG-9): /change-password renders `{!success && <form>}`; the
        // moment the API returns 200 it does setSuccess(true) -> form unmounts ->
        // #change-password-submit-button detaches. `.click()` actionability checks
        // then retry forever on the detaching button (hang 90s) even though the
        // /employee navigation already happened, so `waitForURL` + `storageState`
        // below never run and `employee.json` stays `{}` (cascade T5/T6/T7 -> /login).
        // Dispatch the submit event directly: no actionability, no hang, then wait
        // for the navigation and persist the ESS session.
        await page.evaluate(() => {
          const button = document.getElementById("change-password-submit-button");
          const form = button ? (button.closest("form") as HTMLFormElement | null) : null;
          if (!form) throw new Error("change-password form not found");
          form.requestSubmit();
        });

        // After change, redirect to ESS dashboard (/employee).
        await page.waitForURL("**/employee", { timeout: 30000 });
        await context.storageState({ path: EMP_STATE });
```

Lý do chọn từng phần:
- Tìm form qua `button.closest("form")` từ chính nút `#change-password-submit-button`
  (đã có sẵn, không cần thêm selector form) → nếu không có nút/form thì `throw` rõ ràng
  (reason failure, không phải hang).
- `form.requestSubmit()` dispatch submit event → React `onSubmit={handleSubmit}` chạy
  → `e.preventDefault()` (line 32 change-password/page.tsx) → BE call → success →
  redirect. **Không chờ actionability**, không retry.
- `await page.evaluate(...)` return ngay sau khi dispatch (không chờ vài sửa đổi DOM) →
  `waitForURL('**/employee')` chạy song song với việc BE xử lý + redirect.
- `waitForURL` timeout giữ 30000ms (chain /change-password → setTimeout 2s →
  /dashboard → useAuthGuard(requireAdmin) → /employee). KHÔNG tăng (suy đoán
  cold-compile đã sai — root cause thật là feature bug khác, xem §5).

## 4. Verify (re-run partial + typecheck)

### Typecheck
```bash
cd vroom-hr && pnpm exec tsc --noEmit -p tsconfig.json
```
- File `e2e/vroom-hr.smoke.spec.ts`: **0 error spec**.
- 3 error TS2307 `Cannot find module 'vitest'` ở `lib/api/__tests__/*.test.ts` và
  `lib/api/assistant.test.ts` — **pre-existing**, không liên quan tới sửa (test unit khác,
  không import vitest devDep chưa cài). Spec của T4 không touch vitest.

### Re-run canonical full 9 smoke (sau reset test artifact)
Sửa ready → heavy infrastructure docker full lên + dọn `users` row demo employee +
clear `e2e/.auth/{employee,employee-creds}.json` (giống E2E-RERUN3-REPORT §1):

```
Running 9 tests using 1 worker
  -  1 First-Run Setup › wizard…                   (skipped: DB setup_complete → fallback)
  ✓  2 HR Dashboard                                 (1.5s)
  ✓  3 HR Employee provisioning → mật khẩu tạm        (3.4s)
  ✘  4 ESS onboarding login + change password         (1.3m)   ← click hang GONE; advances
  ✘  5 ESS check-in                                  (22.5s)  ← cascade (T4 không ghi employee.json)
  ✘  6 ESS leave+LEAVE_OVERLAP                       (22.4s)  ← cascade
  ✘  7 ESS payslip published                         (22.4s)  ← cascade
  ✓  8 Recruitment backbone render                   (5.8s)
  ✓  9 HR AI Assistant human-in-the-loop             (3.3s)
4 failed, 1 skipped, 4 passed (2.8m)
```

**BUG-9 (click hang) đã GONE**: T4 không còn hang 90s ở `.click()`; `requestSubmit()`
fire submit event ngay. BE log xác nhận `POST /api/auth/change-password HTTP/1.1 200 OK`
(account `must_change_password=false` sau run). Test tiến qua click → tới
`waitForURL("**/employee", { timeout: 30000 })` → 30s timeout (mới fail ở bước khác, xem §5).

### Quickcheck thủ công BUG-9 fix (browser qua proxy :3000)
Login temp (`gQAJepFuNsQ2`) → `/change-password` → fill → chạy
`page.evaluate(() => form.requestSubmit())` → sau ~6s URL = **`/employee`** (đúng kỳ vọng).
→ requestSubmit fix hoạt động đúng navigation chain, KHÔNG hang.

## 5. Phát hiện bug KHÁC trong lúc verify (KHÔNG sửa — feature/BE, ngoài scope)

Trong canonical run, dù `requestSubmit()` dispatch đúng + BE `POST /change-password` 200,
T4 vẫn fail ở `waitForURL("**/employee")` (30s timeout). BE log mà worker re-run thu được:

```
POST /api/auth/change-password HTTP/1.1 200 OK
GET  /api/auth/me                HTTP/1.1 401 Unauthorized   ← sau change-password
GET  /api/admin/runtime/health   HTTP/1.1 403 Forbidden
GET  /api/admin/audit-logs       HTTP/1.1 403 Forbidden
```

**Root cause mới (KHÔ phải BUG-9, KHÔ phải spec) — tentatively "BUG-10":**
- Sau khi change-password thành công 200, BE **không set / không thay access_token
  cookie** hợp lệ trong response, hoặc cookie mới die → cookie mang tới trang tiếp theo
  (`/dashboard`), `useSession()` gọi `GET /api/auth/me` → **401**.
- 401 → `useAuthGuard({requireAuth:true, requireAdmin:true})` trên `/dashboard`:
  `isAuthenticated=false` → `router.replace('/login')` (KHÔ phải `/employee`).
- → `waitForURL('**/employee')` không bao giờ match → T4 timeout → cascade T5/T6/T7.
- Khác biệt so với verify thủ công trước đây: trong session MCP Playwright (live và
  remaining `employee.json = {}`), conditional `useSession` staleTime + cookie load order
  khác; canonical suite prune cookie mới → /me 401 → redirect /login khác với nhìn manual.

Đây là **bug feature/BE** (cookie session sau change-password), KHÔ phải trong scope
worker test-infra BUG-9. List cho orchestrator dispatch worker backend/feature:
- Back-end: kiểm tra `POST /api/auth/change-password` có issue `Set-Cookie` (access_token
  mới + refresh_token) khi mật khẩu đổi không? Có dạng HTTP-only, Secure=False, SameSite?
- Hoặc đổi password có làm mất refresh_token → access token cũ fails hết?
- Verify bằng curl: login temp → bắt cookie → POST /change-password với cookie → check
  response `Set-Cookie` + thử lại access_token cho GET /api/auth/me ngay sau đó.

**Tôi ghi note nhưng KHÔ fix BUG-10** (vi phạm ràng buộc "chỉ sửa spec"). Fix BUG-9 ✅;
việc mở khóa cascade đầy đủ tới T5-T7 cần thêm works phụ thuộc BUG-10.

## 6. Ràng buộc tuân thủ

- ✅ Tiếng Việt.
- ✅ CHỈ sửa `vroom-hr/e2e/vroom-hr-smoke.spec.ts` (test-infra). KHÔNG đụng
  `app/change-password`, `lib/auth/session.ts` (sửa BUG-1 vẫn hiệu lực), backend, hay bất
  kỳ feature code nào.
- ✅ KHÔNG commit. KHÔNG build feature (chỉ typecheck spec).
- ✅ Build/typecheck spec PASS (0 lỗi spec; 3 lỗi pre-existing ở vitest import không liên
  quan).

## 7. Việc tiếp theo cho orchestrator

1. Dispatch worker backend/feature cho **BUG-10** (session cookie sau change-password):
   - Sau khi fix, re-run smoke → kỳ vọng T4 PASS → ghi `EMP_STATE` → cascade T5/T6/T7 PASS
     (feature đã verify thủ công) → 8 PASS / 1 SKIP (T1 skip OK). Phase 0-3 product + tất
     cả code/test-infra bug sẽ green.
2. (Tùy chọn) tác vụ BE: nếu fix BUG-2 CORSMiddleware cho prod thì có thể bỏ proxy
   workaround; BUG-3 LLM + BUG-4 Google Workspace vẫn cần config thật cho 6c/6e đầy đủ.

## 8. Lệnh reproduce (cho human)

```bash
cd /home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage
docker compose up -d postgres redis minio backend gmail-worker onboarding-worker
# chờ setup-status; xác nhận:
curl -s http://localhost:8000/api/auth/setup-status   # {"setup_complete":true}

# dọn test artifact leak để T3 branch provisioning fresh (giống re-run report §1)
curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"hr.qa@vroom.example.com","password":"VroomQA!148#2026"}' -c /tmp/jar.txt -o /dev/null
docker exec vroom-postgres psql -U postgres -d vroom_hr -c \
  "DELETE FROM refresh_tokens WHERE user_id IN \
   (SELECT id FROM users WHERE email='hoangxuannguyen2005@gmail.com'); \
   DELETE FROM users WHERE email='hoangxuannguyen2005@gmail.com';"
rm -f vroom-hr/e2e/.auth/employee-creds.json && echo '{}' > vroom-hr/e2e/.auth/employee.json

cd vroom-hr
export E2E_HR_EMAIL=hr.qa@vroom.example.com \
       E2E_HR_PASSWORD='VroomQA!148#2026' \
       E2E_HR_NAME='HR QA' \
       E2E_ORGANIZATION_NAME='Vroom QA Organization' \
       NEXT_PUBLIC_API_URL=http://localhost:3000 \
       DISABLE_HMR=true
pnpm exec playwright test --reporter=list
# Sau: T4 giờ không còn hang 90s ở click; tiến đến waitForURL (fail vì BUG-10 nếu chưa fix).
# trace T4:
pnpm exec playwright show-trace test-results/<slug>/trace.zip

# dọn
docker compose down
```