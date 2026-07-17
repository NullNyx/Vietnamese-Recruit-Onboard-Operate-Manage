# BUG-10 Fix Report — Cookie session sau change-password (cascade ESS T4→T5-T7)

> Worker BUG-10, được orchestrator cấp quyền sửa cả FE + BE. Mục tiêu: fix bug session
> cookie sau `POST /api/auth/change-password` chặn cascade ESS (T4 timeout → T5/T6/T7
> fail). KHÔNG reset First-Run, KHÔNG commit.

Ngày fix: 2026-07-17. Repo HEAD chưa commit (vroom-hr/ untracked).

---

## 1. Chẩn đoán root cause (xác định bằng curl + browser)

### Hypothesis ban đầu (không đúng)
- `_set_session_cookies` set `secure=True, samesite="lax"` trên localhost → browser bỏ qua
  secure cookie? Hoặc `auth_service.change_password` revoke/rotate token sai?

### Điều tra runtime (curl sequence qua proxy :3000 → BE :8000)
Repro với cả HR QA (admin) **và** Employee temp (must_change_password=true → đổi):

```bash
# 1) login temp employee
POST /api/auth/login            → 200, Set-Cookie access_token+refresh_token+must_change_password
GET  /api/auth/me  (jar login)  → 200  ✅

# 2) change-password
POST /api/auth/change-password  → 200, body {user, must_change_password:false, setup_complete:true}
                                   Set-Cookie: access_token=<NEW>; HttpOnly; Secure; SameSite=lax
                                                refresh_token=<NEW>; HttpOnly; Secure; SameSite=lax
                                                must_change_password=""; Max-Age=0  (delete)
GET  /api/auth/me  (jar mới)    → 200  ✅
```

**Kết luận BE**: `auth_service.change_password` (`backend/src/modules/identity/application/auth_service.py`)
rotate token đúng — `revoke_user_tokens(updated.id)` + `_issue_session(updated)` (issue
new access_token + refresh_token, cả 2 đều mới). `_set_session_cookies` gọi hệt `login`
(set 2 cookie mới + delete `must_change_password`). **BE không phải bug.** `/api/auth/me`
vẫn `get_current_user` decode JWT (signature+exp) + lookup user — stateless, không check
session-revoke, nên token mới → 200.

### Root cause THẬT (FE — React Query cache stale)
FE dùng `useSession()` (TanStack Query `["session"]`, `staleTime: 30s`) để biết user qua
`GET /api/auth/me`. Cookie HttpOnly nên JS **không đọc được** — session state chỉ đến từ
`/me` hoặc từ response body của `/login`+`/change-password`.

Vấn đề: **`lib/api/auth.ts` `login()` / `changePassword()` trả `AuthSessionResponse` chứa
`user` đầy đủ, nhưng FE KHÔNG bao giờ cập nhật cache `["session"]` với user đó.** Cookie
HttpOnly được BE set trên response (browser tự lưu), nhưng React Query cache `["session"]`
vẫn giữ giá trị **STALE**:

1. `page.goto('/login')` (fresh context, chưa cookie) → `/api/auth/me` → **401** →
   `fetchCurrentUser` trả `null` → cache `["session"] = null` (fresh, staleTime 30s).
2. User submit `/login` → BE 200, set cookie (browser lưu), navigate `/change-password`
   (must_change_password=true). **Cache vẫn = null (stale, chưa refetch vì staleTime<30s).**
3. `/change-password` mount → `useSession()` trả `null` từ cache → `isAuthenticated=false`
   → `useEffect(() => { if (!isLoading && !isAuthenticated) router.replace('/login') })`
   (line 25) **bounce về `/login`** ngay khi render form → **race** với việc fill+submit.
4. Tưởng change-password 200 (cookie mới), nhưng `["session"]` cache vẫn stale. Navigation
   chain lộn xộn: `/change-password` ⇄ `/login` ⇄ `/dashboard`(hardcoded) → `useSession`
   trả stale null → `useAuthGuard` cho `/dashboard` thấy `isAuthenticated=false` →
   redirect `/login` (KHÔNG phải `/employee`) → `waitForURL('**/employee')` timeout → cascade.

Add vào đó: `app/change-password/page.tsx` **hard-code `router.replace('/dashboard')`** cho
mọi user (line 59 cũ). Employee (role=user) → `/dashboard` (admin-only) →
`useAuthGuard({requireAdmin})` redirect `/employee` (detour), kèm `/api/admin/*` 403 noise,
và race thêm với cache stale.

**Tallies với bằng chứng BUG9-FIX-REPORT §5** (`POST change-password 200` → `GET /me 401`
→ `GET /api/admin/* 403`): `/me 401` = request `/me` mang cookie hợp lệ NHƯNG cache stale
null khiến FE tự redirect `/login` rồi `useSession` refetch `/me` khi chưa kịp cookie mới
(timing race); `/api/admin/* 403` = `/dashboard` mount (detour hardcode) với cookie employee
hợp lệ → `get_current_user` OK, `require_admin` 403. → Khớp root cause FE cache stale +
hardcode redirect.

---

## 2. Fix (FE — `vroom-hr/app/login/page.tsx` + `vroom-hr/app/change-password/page.tsx`)

Nguyên tắc: sau auth action BE trả user trong body → **cập nhật cache `["session"]` ngay**
bằng `queryClient.setQueryData(['session'], result.user)` (cookie HttpOnly BE tự set, browser
tự lưu; cache FE phải sync với user thật để `useSession()` không dùng stale null). API
`login()`/`changePassword()` giữ nguyên (chỉ caller đổi). KHÔNG đụng BE, KHÔNG đụng feature
logic, KHÔNG đổi `useSession`/`useAuthGuard` contract.

### `app/login/page.tsx`
```diff
   import { useRouter } from 'next/navigation';
+  import { useQueryClient } from '@tanstack/react-query';
   ...
-  import { login } from '@/lib/api/auth';
+  import { login, type CurrentUser } from '@/lib/api/auth';
   ...
   export default function LoginPage() {
     const router = useRouter();
+    const qc = useQueryClient();
     ...
       const result = await login(email.trim(), password);
+      // BUG-10 fix: BE set HttpOnly cookie qua login response, nhưng cookie KHÔNG đọc
+      // được từ JS (HttpOnly). useSession() chỉ biết user qua GET /api/auth/me — mà
+      // React Query cache ['session'] vẫn giữ giá trị STALE null từ lần /me 401 khi
+      // /login mới mount (chưa cookie). Sync cache ngay bằng user trong response body
+      // để các trang protected (/change-password) không thấy isAuthenticated=false (stale)
+      // và redirect /login nhầm → race chặn cascade ESS.
+      qc.setQueryData<CurrentUser | null>(['session'], result.user);
       if (result.must_change_password) {
         router.replace('/change-password');
       } else {
         router.replace(result.user.role === 'admin' ? '/dashboard' : '/employee');
       }
```

### `app/change-password/page.tsx`
```diff
   import { useRouter } from 'next/navigation';
+  import { useQueryClient } from '@tanstack/react-query';
   ...
-  import { changePassword } from '@/lib/api/auth';
+  import { changePassword, type CurrentUser } from '@/lib/api/auth';
   ...
   export default function ChangePasswordPage() {
     const router = useRouter();
+    const qc = useQueryClient();
     ...
       setIsSubmitting(true);
       try {
-        await changePassword(currentPassword, newPassword);
+        const result = await changePassword(currentPassword, newPassword);
+        // BUG-10 fix: BE set cookie mới + đổi mật khẩu, nhưng ['session'] cache vẫn
+        // giữ user CŨ (must_change_password=true) hoặc null (stale từ /login mount).
+        // Sync cache với user mới trong response body để trang protected tiếp theo
+        // thấy đúng isAuthenticated + mustChangePassword=false; tránh redirect /login
+        // nhầm + tránh /me 401 race → T4 → /employee và cascade T5-T7 unlock.
+        qc.setQueryData<CurrentUser | null>(['session'], result.user);
         setSuccess(true);
-        // Redirect to dashboard after a brief delay
+        // Redirect theo role: admin → /dashboard, employee (ESS) → /employee.
+        // Trước đây hardcode '/dashboard' → employee bị /dashboard (admin-only) bounce
+        // /employee, gây detour + /api/admin/* 403 noise + race với cache stale.
         setTimeout(() => {
-          router.replace('/dashboard');
+          const target = result.user.role === 'admin' ? '/dashboard' : '/employee';
+          router.replace(target);
         }, 2000);
```

### Tác động downstream
- `useSession()` giờ trả user đúng (isAuthenticated=true, mustChangePassword=false) trên
  mọi navigation sau auth action → `useAuthGuard` không còn redirect `/login` nhầm.
- Cookie HttpOnly vẫn do BE quản lý (KHÔNG đụng). Khi cookie expire (15 min) React Query
  refetch `/me` → BE 401 (do cookie hết hạn) → `fetchCurrentUser` trả null → redirect
  `/login` bình thường (chính xác).
- API `login()` / `changePassword()` contract KHÔNG đổi.

---

## 3. Build verify

### BE (không sửa, sanity)
```bash
cd backend
.venv/bin/ruff check src/modules/identity   # All checks passed!  (exit 0)
.venv/bin/pytest tests/modules/identity/ -q  # 339 passed in 3.43s  (exit 0)
```

### FE
```bash
cd vroom-hr && node_modules/.bin/next build
# ✓ Compiled successfully in 3.4s  (exit 0, 32 routes)
```

---

## 4. Curl verify (BE+proxy, cả admin lẫn employee) — root cause đã loại trừ BE

```bash
# HR QA: login → /me 200 → change-password → /me 200 (revert pwd gốc)
POST /api/auth/login            HTTP 200  (Set-Cookie access_token+refresh_token)
GET  /api/auth/me               HTTP 200
POST /api/auth/change-password  HTTP 200  (Set-Cookie access_token<NEW>+refresh_token<NEW>)
GET  /api/auth/me               HTTP 200  ✅ (không 401)

# Employee temp: login temp → /me 200 (must_change_password=true) → change-password → /me 200
POST /api/auth/login            HTTP 200  (Set-Cookie with must_change_password=true)
GET  /api/auth/me               HTTP 200
POST /api/auth/change-password  HTTP 200  (Set-Cookie access_token<NEW must_change_password=false>)
GET  /api/auth/me               HTTP 200  ✅ (role=user, must_change_password=false)
```

→ BE + proxy dispatch cookie đúng; `/me` sau change-password 200. Bug 100% FE cache.

---

## 5. Browser verify (Playwright MCP qua proxy :3000, flow T4 thật)

Code fix chạy với `next dev :3001` + `e2e/proxy.mjs :3000`. Repro provision Employee temp:
| Bước | Trước fix | Sau fix |
|---|---|---|
| `/login` (temp) → submit | navigate `/change-password` | navigate `/change-password` (**không bounce `/login`**) — cache sync |
| `/change-password` fill + submit | `POST /change-password` 200 nhưng redirect hardcode `/dashboard` → bounce `/employee`, kèm `/api/admin/* 403`; cache `["session"]` stale null → `useAuthGuard` redirect `/login` (KHÔNG `/employee`) | `POST /change-password` 200 → `router.replace('/employee')` (role-based), cache sync user mới |
| Sau navigation | `GET /api/auth/me` **401** (race/prune cookie) → redirect `/login` → T4 timeout | URL = **`/employee`** ✅; `GET /api/auth/me` **200** (role=user, must_change_password=false) |
| `/employee/attendance` (ESS) | redirect `/login` (no session) | render heading "Chấm công" + Check-in + history ✅ |

→ **T4 flow PASS** với fix.

---

## 6. Playwright smoke (canonical, clean slate) — cascade ESS unlock xác nhận

Setup: `DELETE FROM users WHERE email='hoangxuannguyen2005@gmail.com'` + clear
`e2e/.auth/employee-creds.json` + `employee.json={}` (buộc T3 provisioning fresh — gap
test-infra idempotency đã note trong các report trước), rồi `pnpm exec playwright test`:

```
      -  1 First-Run Setup › wizard                       (SKIP: DB setup_complete → fallback login + skip)
      ✓  2 HR Dashboard › metrics+runtime+audit           (1.3s)
      ✓  3 HR Employee provisioning → mật khẩu tạm         (2.8s)   ← provision fresh temp
      ✓  4 ESS onboarding login + change password          (5.0s)   ← BUG-10 FIX: /change-password → /employee ✅
      ✓  5 ESS check-in                                     (1.7s)   ← cascade UNLOCKED: employee.json có session hợp lệ
      ✘  6 ESS request nghỉ phép + LEAVE_OVERLAP           (1.5m)   ← BUG KHÁC (selector click timeout — xem §7)
      ✘  7 ESS payslip đã publish (draft không lộ)         (1.9s)   ← BUG KHÁC (payslip lộ draft — xem §7)
      ✓  8 Recruitment backbone render & precondition      (5.3s)
      ✓  9 HR AI Assistant human-in-the-loop               (3.5s)
  6 passed, 2 failed, 1 skipped (2.1m)
```

**Delta so trước fix BUG-10** (RERUN3: T4 FAIL/SKIP, T5/T6/T7 FAIL cascade no session):
- **T4 SKIP→PASS** ✅ — ESS onboarding login temp → change-password → `/employee`,
  `storageState(EMP_STATE)` ghi cookie ESS hợp lệ.
- **T5 FAIL→PASS** ✅ — ESS check-in dùng `employee.json` (session hợp lệ), render
  "Chấm công" + Check-in.
- **T6/T7 FAIL→FAIL** nhưng **root cause đổi** — KHÔ còn cascade no-session (page render
  OK), mà là 2 bug feature/test **MỚI, độc lập** (§7), ngoài scope BUG-10.

→ **BUG-10 đã khắc phục**: cascade ESS session (T4→T5) mở khóa; T6/T7 giờ là bug feature
riêng, không liên quan cookie/session.

---

## 7. Bug MỚI phát hiện (KHÁC BUG-10, list cho orchestrator)

### BUG-11 (P2, mới) — ESS Leave request submit button không match selector / form
`e2e/vroom-hr.smoke.spec.ts:247` T6:
```
await page.getByRole("button", { name: /Gửi.*nghỉ phép|Tạo.*nghỉ phép|Gửi yêu cầu/i }).first().click();
```
→ `locator.click: Test timeout 90000ms exceeded` (button không match hoặc actionability).
ESS session hợp lệ (heading `/Yêu cầu|nghỉ phép|làm thêm/` render OK ở dòng 248 trước đó),
nên KHÔ phải BUG-10. Cần worker E2E/feature: kiểm `/employee/requests` page — tên nút submit
thực tế là gì? Có thể nút là "Gửi" đơn thuần / icon-only (giống BUG-8 pattern) → thêm
`aria-label` hoặc chỉnh selector spec.

### BUG-12 (P2, mới) — ESS Payslip list lộ "draft/unpublished" cho employee
`e2e/vroom-hr.smoke.spec.ts:281` T7: page `/employee/payslips` render "Danh sách phiếu lương"
+ "Đã phát hành" (session ESS hợp lệ → KHÔ phải BUG-10) NHƯNG `getByText(/Bản nháp|draft|unpublished/i).count() > 0`
→ "ESS must not expose unpublished payslips". → BE `employee_payslip_router` hoặc seed đang
trả draft payslip cho employee, hoặc trang ESS render nhầm badge "Bản nháp". Cần worker
backend/feature kiểm `GET /api/employee/payslips` (employee_router) filter status=published
và HR `payroll/payslips` page có draft persist từ các smoke run trước (T3/T7 HR tạo draft).

> Cả 2 bug trên **đều xảy ra khi ESS session đã hợp lệ** (sau BUG-10 fix) → xác nhận
> BUG-10 không leak; chúng là bug feature/test độc lập.

---

## 8. Ràng buộc tuân thủ

- ✅ Tiếng Việt.
- ✅ Sửa cả FE (`vroom-hr/app/login/page.tsx`, `vroom-hr/app/change-password/page.tsx`);
  BE KHÔNG sửa (chẩn đoán + curl loại trừ BE; ruff+pytest BE pass).
- ✅ KHÔNG reset First-Run (DB `setup_complete=true` nguyên). Chỉ delete `users` row của
  demo Employee giữa các smoke run (gap test-infra idempotency đã note từ report trước —
  không phải reset First-Run, không sửa feature).
- ✅ KHÔNG refactor `useSession`/`useAuthGuard`/`lib/api/auth.ts` contract (chỉ caller pages
  thêm `setQueryData` + role-based redirect).
- ✅ Build PASS (BE ruff+pytest, FE next build) rồi dừng.
- ✅ KHÔNG commit.

---

## 9. Việc tiếp theo cho orchestrator

1. Dispatch worker:
   - **BUG-11**: spec T6 leave submit button selector / FE `aria-label`.
   - **BUG-12**: BE `employee_payslip_router` filter `status=published` + HR payroll draft
     persist cleanup, hoặc FE ESS payslip page badge logic.
2. Re-run smoke sau 2 fix trên → kỳ vọng **8 PASS / 1 SKIP** (T1 skip DB setup OK).
   BUG-2 (CORS), BUG-3 (LLM), BUG-4 (Google Workspace) vẫn là config/env, không chặn smoke.
3. (Tùy chọn) test-infra: làm T3 provisioning idempotent (BE expose reset/delete account
   hoặc spec tự dọn users row giữa run) để re-run không cần delete manual — gap đã note.