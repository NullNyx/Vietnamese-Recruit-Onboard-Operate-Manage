# Phase 0 — Foundation Report (Vroom HR)

> Phase 0 Foundation cho tích hợp giao diện AI Studio vào Vroom HR.
> Mục tiêu: biến `vroom-hr/` (AI Studio applet mô phỏng) thành frontend Next.js thật,
> wire backend (BE) thật. Phase 0 là CRITICAL PATH — mọi feature phase sau phụ thuộc.
>
> Source of truth: `docs/ai-studio-ui-integration-plan.md` (section 2 + 4 Phase 0).
> BE contract: `backend/AGENTS.md` (error codes registry),
> `docs/project-status-2026-07-16.md`, `CONTEXT.md`.

## 1. Files added

### API client layer (copy + wire từ `frontend/src/lib/api/*`)
- `vroom-hr/lib/api/auth.ts` — identity: `getSetupStatus`, `login`, `setupFirstRun`,
  `changePassword`; `BASE` được wire bằng `API_BASE_URL` từ `./client`.
- `vroom-hr/lib/api/admin.ts` — admin: `getAuditLogs`, `getRuntimeHealth`,
  whitelist/OAuth/users/ai-config...; `BASE` wire `API_BASE_URL`.
- `vroom-hr/lib/api/recruitment.ts` (31KB) — recruitment: `getMetrics`,
  candidates, job-openings, interviews, cv-review...; `BASE` wire `API_BASE_URL`.
- `vroom-hr/lib/api/` (còn lại): `attendance.ts`, `departments.ts`, `positions.ts`,
  `employees.ts`, `gmail.ts`, `onboarding.ts`, `payslips.ts`, `admin-payslips.ts`,
  `employee-requests.ts`, `assistant.ts`, `employee-assistant.ts`, `admin-schemas.ts`,
  `types.ts`, `index.ts` — copy nguyên vẹn để Phase 1/2/3 dùng (các module này vẫn
  dùng relative path; sẽ wire `API_BASE_URL` ở phase liên quan).
- `vroom-hr/lib/api/__tests__/interview-api.test.ts` — test copy (Phase 1+).
- `vroom-hr/lib/api/client.ts` — **unified fetch wrapper**: `API_BASE_URL` từ
  `NEXT_PUBLIC_API_URL` (fallback `http://localhost:8000`), `credentials: "include"`,
  parse `error_code` → `ApiError`.
- `vroom-hr/lib/api/error-codes.ts` — **error-code registry** tịnh từ
  `backend/AGENTS.md` (Identity/Employee/Recruitment/Attendance/Gmail/Payroll/ESS),
  `ERROR_CODE_MESSAGES` + `getErrorMessage(errorCode)`.
- `vroom-hr/lib/query-client.ts` — copy từ `frontend/src/lib/query-client.ts`
  (React Query, staleTime 30s, gcTime 10m, không retry 4xx).

### Auth & session
- `vroom-hr/lib/auth/session.ts` — `useSession()` (gọi `GET /api/auth/me` qua
  `apiFetch`), `useAuthGuard({ requireAuth, requireAdmin, requireEmployee,
  redirectIfAuthenticated })`.

### Middleware
- `vroom-hr/middleware.ts` — bảo vệ route theo auth cookie (`access_token`),
  force `must_change_password` → `/change-password`. Matcher loại trừ
  `/login|/setup|/change-password|_next|api|static`.

### App routes
- `vroom-hr/app/providers.tsx` — `Providers` bọc `QueryClientProvider` (gọi
  `getQueryClient()` singleton browser).
- `vroom-hr/app/layout.tsx` — root layout dùng `<Providers>` + font Inter,
  JetBrains_Mono (giữ design AI Studio).
- `vroom-hr/app/page.tsx` — **root redirector** role-aware: dùng `useSession()` +
  `getSetupStatus()` → chuyển tới `/setup` | `/login` | `/dashboard` | `/employee`.
- `vroom-hr/app/setup/page.tsx` — **port SetupWizard** thành page gọi BE thật:
  `GET /api/auth/setup-status` → `POST /api/auth/setup` (atomic), xử lý
  `AUTH_SETUP_ALREADY_COMPLETED`, backend unavailable + retry, success → dashboard
  no re-login (cookie HttpOnly do BE cấp). Giữ design AI Studio (slate/indigo,
  bento, brand "VR", 3-step wizard, deco background).
- `vroom-hr/app/login/page.tsx` — login gọi `POST /api/auth/login` (cookie HttpOnly),
  redirect theo `must_change_password` + role, render error_code từ BE.
- `vroom-hr/app/change-password/page.tsx` — `POST /api/auth/change-password`,
  bắt buộc khi `must_change_password`, success → dashboard.
- `vroom-hr/app/(dashboard)/layout.tsx` — **HR sidebar** (12 nav item:
  dashboard/recruitment inbox/candidates/job-openings/interviews/onboarding/
  employees/attendance/requests/payroll/gmail/settings) + AI Assistant button +
  logout. Dữ liệu thật (no role switcher giả, no Simulation Controller).
- `vroom-hr/app/(dashboard)/dashboard/page.tsx` — **dashboard với metrics thật**:
  `GET /api/recruitment/metrics` (queue_depth, success_rate, failure_rate,
  avg_processing_time), `GET /api/admin/runtime/health` (services[], status),
  `GET /api/admin/audit-logs` (phân trang). Bento grid AI Studio.
- `vroom-hr/app/(employee)/layout.tsx` — **ESS sidebar** (dashboard/attendance/
  requests/payslips) + Employee Assistant + logout.
- `vroom-hr/app/(employee)/employee/page.tsx` — ESS dashboard scaffold (card
  grid tới feature pages Phase 2/3, không phải feature thật).

### Config
- `vroom-hr/.env.example` — `NEXT_PUBLIC_API_URL=http://localhost:8000`
  (+note legacy GEMINI_API_KEY/APP_URL sẽ thay bằng /api/assistant Phase 3).
- `vroom-hr/pnpm-workspace.yaml` — `allowBuilds` phê duyệt build scripts
  (`sharp`, `@tailwindcss/oxide`, `protobufjs`, `re2`, `unrs-resolver`,
  `@google/genai`) để `pnpm install` + `pnpm build` không lỗi
  `ERR_PNPM_IGNORED_BUILDS`.

## 2. Files removed / changed

### Removed
- `vroom-hr/lib/simulationState.ts` — toàn bộ mock schema + `INITIAL_*` seed.
  Đã xác nhận không còn import nào (xem mục 5 verify).
- `vroom-hr/components/SetupWizard.tsx` — thay bằng `app/setup/page.tsx`
  (page gọi BE thật; component cũ gọi `onComplete` callback mô phỏng).
- `vroom-hr/app/api/gemini/route.ts` + toàn bộ `app/api/` — route mô phỏng
  Gemini đã xóa. **TODO Phase 3**: thay `AiChat` bằng `lib/api/assistant.ts`
  (HR) / `employee-assistant.ts` (ESS) gọi `/api/assistant/*` /
  `/api/ess/assistant/*`; Draft Action confirm → write endpoint thật
  (human-in-the-loop).
- `vroom-hr/app/page.tsx` (monolith ~2509 dòng) — rewrite thành root
  redirector role-aware (47 dòng). Toàn bộ state localStorage +
  "Simulation Controller" + role switcher + simulated IP selector đã xóa.

### Changed
- `vroom-hr/package.json` — đổi `name` → `vroom-hr`; thêm deps
  `@tanstack/react-query`, `zod`, `react-hook-form`,
  `@hookform/resolvers` (giữ `@google/genai`, `motion`, `lucide-react`,
  `clsx`, `tailwind-merge`, `class-variance-authority`).
  Cấu hình build approval chuyển sang `pnpm-workspace.yaml` (pnpm 11+ không đọc
  trường `pnpm` trong package.json nữa).
- `vroom-hr/app/layout.tsx` — thêm `<Providers>` (React Query).

### Kept (không động vào Phase 0)
- `vroom-hr/components/AiChat.tsx` — component còn tham chiếu `/api/gemini`
  (string trong handler, không phải import). **Không được import ở bất kỳ đâu**
  trong `app/`, nên không ảnh hưởng build. Sẽ wire Phase 3. Đã verify build pass
  (TypeScript type-check + static export đều OK).
- `vroom-hr/lib/api/` các module feature (employees/gmail/onboarding/...) —
  vẫn dùng BASE relative `/api/<module>`; sẽ wire `API_BASE_URL` ở phase liên
  quan. Build pass vì kiểu hợp lệ.

## 3. Luồng đã wire (data thật, BE thật)

| Luồng | Endpoint BE | UI | Ghi chú |
|---|---|---|---|
| First-Run Setup | `GET /api/auth/setup-status` | `app/setup/page.tsx` | Hiển thị wizard khi `setup_complete=false`; backend unavailable → retry. |
| Setup atomic | `POST /api/auth/setup` | `app/setup/page.tsx` | Tạo Organization + HR trong 1 transaction (BE atomic). `AUTH_SETUP_ALREADY_COMPLETED` → chuyển `/login`. Success → cookie HttpOnly, vào `/dashboard` no re-login. |
| Login | `POST /api/auth/login` | `app/login/page.tsx` | Cookie HttpOnly do BE cấp. `must_change_password=true` → `/change-password`. Role admin → `/dashboard`, user → `/employee`. |
| Change password | `POST /api/auth/change-password` | `app/change-password/page.tsx` | Validate client (≥12 ký tự, khác current). Render error_code BE. |
| Session | `GET /api/auth/me` | `lib/auth/session.ts` `useSession()` | React Query cache; `isAdmin`/`mustChangePassword`/`setupComplete`. Redirect dùng `useAuthGuard`. |
| Root routing | `/` | `app/page.tsx` | Role-aware: chưa setup → `/setup`; đã setup chưa login → `/login`; HR → `/dashboard`; Employee → `/employee`. |
| Route guard | cookie `access_token` | `middleware.ts` | Force `must_change_password`; chưa auth trên protected path → `/login`. Guard role chi tiết do BE (403) khi gọi API. |
| Dashboard metrics | `GET /api/recruitment/metrics` | `app/(dashboard)/dashboard/page.tsx` | `queue_depth`, `success_rate`, `failure_rate`, `average_processing_time_ms`. |
| Runtime health | `GET /api/admin/runtime/health` | dashboard | `status` (healthy/degraded/unhealthy) + `services[]` (redis/postgresql/minio/gmail worker). |
| Audit log | `GET /api/admin/audit-logs` | dashboard | `items[]`, `total`, `page`, `page_size`; có phân trang + filter `action_type`. |

## 4. Build verify

```
$ pnpm install   # exit 0 — build scripts approved via pnpm-workspace.yaml allowBuilds

$ pnpm build
   ▲ Next.js 15.5.20
   Creating an optimized production build ...
 ✓ Compiled successfully in 1265ms
   Skipping linting
   Checking validity of types ...
   Collecting page data ...
   Generating static pages (0/9) ... (2/9) (4/9) (6/9)
 ✓ Generating static pages (9/9)
   Finalizing build optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    2.17 kB         114 kB
├ ○ /_not-found                            994 B         103 kB
├ ○ /change-password                     5.58 kB         117 kB
├ ○ /dashboard                           4.55 kB         116 kB
├ ○ /employee                            2.78 kB         114 kB
├ ○ /login                                5.2 kB         117 kB
└ ○ /setup                               5.66 kB         117 kB
+ First Load JS shared by all             102 kB
  ├ chunks/469f4ccc-d3c5441f71e18082.js  54.2 kB
  ├ chunks/754-090853d9f53328cc.js       46.1 kB
  └ other shared chunks (total)          1.86 kB

ƒ Middleware                             32.5 kB
○  (Static)  prerendered as static content
```

**`pnpm build` PASS** (exit 0). 7 trang route + middleware được sinh static.

## 5. Verify: không còn simulation

```
$ rg -n "simulationState|localStorage|INITIAL_EMAILS|setCurrentRole|Simulation Controller|setSimulatedIp|simulatedIp" app components lib
(no output)   # exit 0 — không còn match

$ ls app/api
app/api removed        # xóa hẳn thư mục

$ ls lib/simulationState.ts
simulationState.ts removed
```

`components/AiChat.tsx` còn chuỗi `'/api/gemini'` trong handler (component Phase 3,
không import ở đâu, không ảnh hưởng build) — sẽ wire Phase 3.

## 6. Blockers / things for Phase 1-3

- **Không blocker Phase 0.** Build pass, scaffold route + auth + data layer sẵn.
- **Smoke test cần BE chạy:** khi `next dev` + BE ở `NEXT_PUBLIC_API_URL`,
  `/setup` gọi `setup-status`/`setup` thật; `/login` gọi `login` thật;
  `/` dùng `/me` rồi redirect; `/dashboard` hiện metrics/health/audit thật.
  (Phase 0 chưa chạy smoke end-to-end với BE — cần BE Postgres+Redis+MinIO để
  verify cookie cross-origin; CORS của BE tại `http://localhost:8000` phải cho
  origin `http://localhost:3000` + `credentials: include`.)
- **Cross-origin cookie:** `pnpm dev` mặc định ở `:3000`, BE ở `:8000`. BE phải
  set cookie với `SameSite=Lax` (hoặc `None;Secure` khi HTTPS) và
  `Access-Control-Allow-Credentials: true` + `Access-Control-Allow-Origin`
  tường minh (không `*`). Nếu BE hiện chưa cho, Phase 0 accept có thể cần
  Next rewrite proxy `NEXT_PUBLIC_API_URL` → relative `/api/*` (alternative:
  đặt `NEXT_PUBLIC_API_URL` rỗng + thêm rewrite `next.config.ts`). Đây là cấu
  hình vận hành, không phải code Phase 0.
- **Feature pages (Phase 1/2/3):** scaffold route sẵn nhưng chưa implement:
  - Phase 1: `recruitment/inbox|candidates|job-openings|interviews|review|metrics`
    + `onboarding`.
  - Phase 2: `employees`, `attendance`, `requests` (HR + ESS), `payroll/payslips`,
    `employee/attendance|requests|profile|documents`.
  - Phase 3: `assistant` (HR `lib/api/assistant.ts`), `employee/assistant`
    (`employee-assistant.ts`), `gmail`, `settings`. **`components/AiChat.tsx`
    phải thay `/api/gemini` bằng `lib/api/assistant.ts`** + Draft Action confirm
    → write endpoint thật.
- **API base wiring module còn lại:** các module `lib/api/` feature
  (employees/gmail/onboarding/attendance/...) vẫn dùng BASE relative
  `/api/<module>`; sẽ wire `API_BASE_URL` ở phase feature liên quan
  (giống `auth.ts`/`admin.ts`/`recruitment.ts` đã làm).
- **pnpm-workspace.yaml `allowBuilds`** đã phê duyệt build scripts; nếu thêm
  package native mới cần update file này.

## 7. Command verify (cho orchestrator)

```bash
cd vroom-hr
pnpm install          # exit 0 (build scripts approved)
pnpm build            # exit 0 — 7 static routes + middleware
# Smoke (cần BE chạy ở NEXT_PUBLIC_API_URL=http://localhost:8000):
pnpm dev              # http://localhost:3000
#   /        → /setup (chưa setup) | /login (đã setup) | /dashboard | /employee
#   /setup   → wizard gọi BE setup-status + setup
#   /login   → login BE (cookie HttpOnly)
#   /dashboard → metrics /api/recruitment/metrics + /api/admin/runtime/health
#                + audit /api/admin/audit-logs
```

Phase 0 HOÀN THÀNH. Build PASS. Chờ orchestrator review.