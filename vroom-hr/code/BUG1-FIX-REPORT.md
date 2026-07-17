# BUG-1 FIX REPORT — session shape `/api/auth/me` (CRITICAL, chặn toàn UI authed)

> Fix worker BUG-1. Sửa `useSession()` parse sai shape `GET /api/auth/me`.
> Build PASS. KHÔNG commit.

Ngày fix: 2026-07-17. Scope: chỉ `lib/auth/session.ts` + `lib/api/auth.ts`
(comment) + một sửa nhỏ test-infra `playwright.config.ts` (gỡ lỗi type chặn
build, xem §4). KHÔNG đụng backend, KHÔNG sửa feature code khác.

---

## 1. Shape BE đã xác nhận

`backend/src/modules/identity/api/router.py`:

| Endpoint | Response shape | Source |
|---|---|---|
| `GET /api/auth/me` | **flat `UserResponse`** (`{id, email, name, avatar_url, employee_id, role, must_change_password, gmail_grant_valid, calendar_grant_valid, created_at, last_login}`) | `router.py:478–502` — `async def me(...) -> UserResponse: return UserResponse(...)` |
| `POST /api/auth/login` | wrapped `AuthSessionResponse = { user, must_change_password, setup_complete }` | `router.py:375–400` (JSONResponse content dict có key `"user"`) |
| `POST /api/auth/setup` | wrapped `AuthSessionResponse` | `router.py:180–198` |
| `POST /api/auth/change-password` | wrapped `AuthSessionResponse` | `router.py:413–430` |

`backend/src/modules/identity/api/schemas.py:38–52` định nghĩa `UserResponse`
flat đúng như trên; `:90–93` định nghĩa `AuthSessionResponse` wrap `UserResponse`.

BE runtime không chạy trong môi trường fix worker (`curl :8000` → connection
refused), nhưng shape được xác nhận từ source code (authoritative). E2E-REPORT
§5 BUG-1 đã có curl sample 200: `{"id":…,"email":"hr.qa@vroom.example.com",
"role":"admin","must_change_password":false,…}` (KHÔNG có key `"user"`).

Tham chiếu đúng (Next 14 cũ) `frontend/src/hooks/use-current-user.ts:27–34`:
`fetchCurrentUser` gọi `/api/auth/me` rồi `return res.json()` → `data` chính là
`CurrentUser` flat, không unwrap `data.user`.

---

## 2. Chẩn đoán bug (tóm tắt)

`vroom-hr/lib/auth/session.ts` (bản cũ) khai báo `AuthSessionResponse` =
`{user, must_change_password, setup_complete}` và `fetchSession` gọi
`/api/auth/me` rồi `useSession` dùng `data?.user`, `data?.must_change_password`,
`data?.setup_complete`. Vì /me thực tế trả **flat** `UserResponse`:
- `data?.user` → `undefined` → `isAuthenticated = !!data?.user && !error` =
  `false`.
- `user: CurrentUser | null = data?.user ?? null` → `null` → `isAdmin` false.
- Hậu quả: `useAuthGuard({requireAuth})` → redirect mọi trang HR + ESS về
  `/login`, dù `/api/auth/me` đã trả 200 admin thật (E2E-REPORT §4 bằng chứng:
  `/dashboard -> /login`, `/recruitment/* -> /login`, `/employees -> /login`,
  `/assistant -> /login`).

---

## 3. Diff sửa

### 3.1 `vroom-hr/lib/auth/session.ts` (rewrite, lưu API public không đổi)

Bản cũ (key lines):
```ts
import type { CurrentUser, AuthSessionResponse } from "@/lib/api/auth";

async function fetchSession(): Promise<AuthSessionResponse> {
  return apiFetch<AuthSessionResponse>("/api/auth/me");   // ← SAI shape
}

export function useSession() {
  const { data, isLoading, error, refetch } = useQuery<AuthSessionResponse>({...});
  const isAuthenticated = !!data?.user && !error;          // ← data.user undefined
  const user: CurrentUser | null = data?.user ?? null;     // ← luôn null
  const isAdmin = user?.role === "admin";
  const mustChangePassword = data?.must_change_password ?? false;
  const setupComplete = data?.setup_complete ?? false;
  return { user, isLoading, isAuthenticated, isAdmin, mustChangePassword, setupComplete, error, refetch };
}
```

Bản mới (rewrite toàn file):
```ts
'use client';

import { useQuery } from "@tanstack/react-query";
import type { CurrentUser } from "@/lib/api/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/types";

// /api/auth/me trả flat UserResponse (CurrentUser). KHÔNG wrap trong `user`.
// 401/403 → null (unauthenticated); lỗi khác → throw để React Query retry.
async function fetchCurrentUser(): Promise<CurrentUser | null> {
  try {
    return await apiFetch<CurrentUser>("/api/auth/me");
  } catch (error) {
    if (error instanceof ApiError && (error.statusCode === 401 || error.statusCode === 403)) {
      return null;
    }
    throw error;
  }
}

export function useSession() {
  const { data, isLoading, error, refetch } = useQuery<CurrentUser | null>({
    queryKey: ["session"],
    queryFn: fetchCurrentUser,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.statusCode === 401 || error.statusCode === 403)) {
        return false;
      }
      return failureCount < 2;
    },
    staleTime: 30 * 1000,
  });

  const user: CurrentUser | null = data ?? null;            // flat user
  const isAuthenticated = !!data && !error;                  // /me 200 ⇔ authed
  const isAdmin = user?.role === "admin";
  const mustChangePassword = user?.must_change_password ?? false;
  const setupComplete = !!data;                              // /me 200 ⇔ setup done
  return { user, isLoading, isAuthenticated, isAdmin, mustChangePassword, setupComplete, error, refetch };
}

export function useAuthGuard(options: {...} = {}) { ... }   // giữ nguyên logic
```

Điểm khác bản chất:
1. `fetchCurrentUser` trả `CurrentUser | null` (flat) thay vì `AuthSessionResponse`.
2. `401/403` → `null` (dùng `ApiError.statusCode` thay vì sniff string `"401"`
   trong message — message có thể là `res.statusText` không chứa số).
3. `user = data ?? null` (flat), `isAuthenticated = !!data && !error`,
   `mustChangePassword = user?.must_change_password`, `setupComplete = !!data`.
4. API public `useSession()` (`user`, `isLoading`, `isAuthenticated`, `isAdmin`,
   `mustChangePassword`, `setupComplete`, `error`, `refetch`) và `useAuthGuard`
   (options + return `{user, isLoading, isAuthenticated, isAdmin}`) **giữ nguyên
   hoàn toàn** → các layout/page không phải refactor.

### 3.2 `vroom-hr/lib/api/auth.ts` (chỉ thêm doc comment, KHÔNG đổi type/interface)

`AuthSessionResponse` vẫn là wrapped `{user, must_change_password, setup_complete}`
— đúng cho `/login`, `/setup`, `/change-password`. Thêm block comment ngay trên
`AuthSessionResponse` (line 20→29) cảnh báo KHÔNG áp dụng cho `/me`:

```ts
/**
 * Session shape trả về bởi POST /api/auth/login, /setup, /change-password
 * (BE wrap `user` + `must_change_password` + `setup_complete`).
 *
 * LƯU Ý: KHÔNG áp dụng cho GET /api/auth/me — /me trả flat `CurrentUser`
 * (xem lib/auth/session.ts). Bug cũ (BUG-1): app từng dùng
 * AuthSessionResponse cho /me → `data.user` undefined →
 * isAuthenticated=false → redirect /login dù /me trả 200 admin thật.
 */
export interface AuthSessionResponse {
  user: CurrentUser;
  must_change_password: boolean;
  setup_complete: boolean;
}
```

`CurrentUser` interface (line 6) giữ nguyên — đã là flat khớp `UserResponse` BE
(`id, email, name, avatar_url, employee_id?, role, must_change_password,
gmail_grant_valid, calendar_grant_valid, created_at, last_login`). Không có hàm
`getMe` để sửa (FE gọi /me qua `apiFetch` trực tiếp trong `session.ts`).

### 3.3 `vroom-hr/middleware.ts` — KHÔNG đổi

`middleware.ts` check raw cookie `access_token` + `must_change_password`
(KHÔNG gọi `/api/auth/me`), nên không phụ thuộc shape — confirm đúng không cần sửa.

---

## 4. Sửa nhỏ test-infra để build PASS (ngoài scope auth nhưng chặn verify)

`vroom-hr/playwright.config.ts` có **pre-existing type error** (khác BUG-1):
`trace`, `screenshot`, `video` đặt ở **top-level Config** (line 39–41 cũ) không
có trong Playwright 1.61 `Config` schema — chỉ hợp lệ trong `use`. Vì
`tsconfig.json` include `**/*.ts`, `next build` typecheck dừng tại file này, làm
build FAIL dù auth fix đúng.

Sửa tối thiểu (test scaffolding, không phải feature code): xóa 3 dòng top-level
`trace`/`screenshot`/`video` (giá trị của chúng đã có trong block `use` line 45–47,
không mất hành vi). Đây là test infra do E2E sub-agent tạo (E2E-REPORT §3), không
phải feature recruitment/onboarding/assistant/… — sửa để build verify có thể hoàn
thành, đúng ràng buộc "build PASS".

```diff
   reporter: [["list"], ["html", { open: "never" }]],
-  trace: "retain-on-failure",
-  screenshot: "only-on-failure",
-  video: "retain-on-failure",

   use: {
     baseURL,
     trace: "retain-on-failure",
     screenshot: "only-on-failure",
     video: "retain-on-failure",
   },
```

---

## 5. Grep usage ảnh hưởng + verification

Lệnh: `rg -n "useSession|\.user\b|must_change_password|setup_complete" vroom-hr/app vroom-hr/lib/auth`

Toàn bộ consumer `useSession()` truy cập các field flat trên `CurrentUser` (tồn
tại, không vỡ type):

| File | Dùng từ useSession() | Field flat CurrentUser truy cập | OK |
|---|---|---|---|
| `app/(dashboard)/layout.tsx:32` | `{ user }` | `user?.name` | ✓ |
| `app/(employee)/layout.tsx:21` | `{ user }` | `user?.name`, `user?.email` | ✓ |
| `app/(employee)/employee/page.tsx:9` | `{ user }` | `user?.name` | ✓ |
| `app/(employee)/employee/profile/page.tsx:18` | `{ user }` | `user?.employee_id` | ✓ |
| `app/(employee)/employee/documents/page.tsx:18` | `{ user }` | `user?.employee_id` | ✓ |
| `app/page.tsx:11` | `{ isAuthenticated, isAdmin, isLoading }` | bool fields | ✓ |
| `app/setup/page.tsx:12` | `{ isAuthenticated, setupComplete, isLoading }` | bool fields | ✓ (setupComplete giờ = `!!data`) |
| `app/login/page.tsx:13` | `{ isAuthenticated, isAdmin, isLoading }` | bool fields | ✓ |
| `app/change-password/page.tsx:13` | `{ isAuthenticated, mustChangePassword, isLoading }` | bool fields | ✓ |
| Tất cả page gọi `useAuthGuard({...})` (19 nơi) | dùng `{ user, isLoading, isAuthenticated, isAdmin }` của `useAuthGuard` | API không đổi | ✓ |

Lưu ý đặc biệt:
- `app/login/page.tsx:40,43` dùng `result.must_change_password` / `result.user.role`
  — đây là **response của `POST /login`** (vẫn wrapped `AuthSessionResponse`),
  KHÔNG phải useSession → đúng, không đổi.
- `app/(dashboard)/employees/[id]/page.tsx:285` `account.must_change_password` —
  field từ admin endpoint riêng (EmployeeAccountStatus), không liên quan session.
- `setupComplete`: `app/setup/page.tsx` redirect-if-authed dùng
  `setupComplete && isAuthenticated`. Sau fix `setupComplete = !!data` (= user
  authed ⇔ org đã setup), logic tương đương — khi đã 200 /me thì setup sure hoàn
  tất (BE chỉ trả /me nếu có session hợp lệ ⇒ org + admin tồn tại).
- `app/page.tsx` root redirector: khi chưa authed (`isAuthenticated=false`) vẫn
  gọi riêng `getSetupStatus()` để phân nhánh `/login` vs `/setup` — không phụ
  thuộc `setupComplete` của useSession, không đổi.

→ KHÔNG cần sửa thêm file app nào. Build typecheck PASS xác nhận không vỡ type.

---

## 6. Build verify

```bash
cd /home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage/vroom-hr
node_modules/.bin/next build
```

Tail (PASS):
```
▲ Next.js 15.5.20
- Environments: .env.local

Creating an optimized production build ...
✓ Compiled successfully in 3.4s
Skipping linting
Checking validity of types ...
Collecting page data ...
Generating static pages (32/32)
✓ Generating static pages (32/32)
Finalizing build optimization ...
Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    2.38 kB         114 kB
├ ○ /_not-found                            994 B         103 kB
├ ○ /assistant                           1.31 kB         161 kB
... (32 routes, mọi route HR + ESS build OK) ...
└ ○ /setup                                5.8 kB         117 kB
+ First Load JS shared by all             102 kB

ƒ Middleware                             32.3 kB

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

→ Build PASS (exit 0). Dừng theo ràng buộc. KHÔNG commit.

---

## 7. Sau fix — kỳ vọng E2E

Sau fix, chạy E2E-REPORT §6 ⧹ §3 các test bị chặn bởi BUG-1 (T2 HR Dashboard,
T3 HR provisioning, T5 ESS check-in, T6 ESS leave, T7 ESS payslip, T9 HR AI
Assistant) sẽ vượt được bước auth (không còn redirect `/login`), để lộ các
blocker khác nếu còn (BUG-2 CORS, BUG-3 LLM, BUG-4 Google Workspace). Orchestrator
nên re-run smoke verify T2–T7.