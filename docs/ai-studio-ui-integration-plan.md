# Kế hoạch tích hợp giao diện AI Studio vào Vroom HR

> **Mục đích:** dùng giao diện do AI Studio sinh ra tại `vroom-hr/` làm **frontend mới** của Vroom HR, wire trực tiếp với backend (BE) thật đã triển khai ở `backend/`. Tài liệu này là **source of truth** cho các sub-agent thực thi.
>
> **Vai trò:** orchestrator chia task, sub-agent (pi, background workspace) implement. Orchestrator không code.

## 1. Hiện trạng hai nguồn code

### 1.1. Nguồn giao diện mới — `vroom-hr/` (AI Studio applet)

Next.js 15 App Router, React 19, Tailwind 4, `@google/genai`, `lucide-react`, `motion`. **App mô phỏng (simulation) một trang:**

- `app/page.tsx` (~2509 dòng) — monolith: gate setup → "Simulation Controller" (role switcher + simulated IP) → sidebar HR (12 tab) + sidebar ESS (4 tab); toàn bộ state tới từ `localStorage` + seed mock.
- `lib/simulationState.ts` — TS interfaces (`Organization`, `RecruitmentEmail`, `Candidate`, `JobOpening`, `Interview`, `OnboardingProcess`, `Employee`, `AttendanceRecord`, `NetworkAllowlist`, `EmployeeRequest`, `Payslip`, `AuditLog`) + hằng số `INITIAL_*` seed. Đây là **schema gần khớp domain** nhưng là mock, không phải API client.
- `components/SetupWizard.tsx` — UI 3 bước (org → HR account → review → success) với client validation (zod-like), có state "backend unavailable + retry".
- `components/AiChat.tsx` — chat panel; POST `dbSnapshot` nguyên vẹn tới `/api/gemini`; có "proposal card" cho Draft Action.
- `app/api/gemini/route.ts` — Gemini route nhận `dbSnapshot` + history, có fallback mock khi thiếu API key. **Không phải assistant thật** của BE.

### 1.2. Frontend hiện tại — `frontend/` (đã wire BE)

Next.js 14, đã có App Router route đầy đủ (`(dashboard)` cho HR, `(employee)` cho ESS, `login`, `setup`, `change-password`), `middleware.ts`, và **typed API client layer** tại `frontend/src/lib/api/*` khớp BE:

`auth.ts, admin.ts, recruitment.ts (31KB), assistant.ts, employee-assistant.ts, attendance.ts, employee-requests.ts, employees.ts, departments.ts, positions.ts, onboarding.ts, gmail.ts, payslips.ts, admin-payslips.ts, types.ts, admin-schemas.ts` + `query-client.ts`.

### 1.3. Backend — `backend/`

FastAPI, routers đã wire đầy đủ (xem `backend/src/main.py`, `docs/project-status-2026-07-16.md`). Tất cả endpoint, error codes, business rules đã chốt (xem `backend/AGENTS.md` và `CONTEXT.md`).

## 2. Quyết định kiến trúc (orchestrator chốt)

1. **`vroom-hr/` trở thành frontend chính thức.** Giữ thiết kế AI Studio; wire với BE thật.
2. **Tái sử dụng typed API client** từ `frontend/src/lib/api/*` bằng cách **copy** sang `vroom-hr/lib/api/*` (nhánh AI Studio đã có `lib/`). Đây là contract đã test, không reinvent.
3. **Tách monolith `app/page.tsx`** thành App Router routes QUAN SÁT cùng cấu trúc `frontend/src/app`:
   - `app/setup`, `app/login`, `app/change-password`
   - `app/(dashboard)/...` (HR): `dashboard`, `recruitment/{inbox,candidates,job-openings,interviews,review,metrics,[id]}`, `onboarding`, `employees`, `attendance`, `requests`, `payroll/payslips`, `gmail`, `settings`
   - `app/(employee)/employee/{dashboard,profile,documents,attendance,requests,payslips,assistant}`
4. **Thay simulationState (localStorage mock) bằng data hooks thật** (React Query / SWR) gọi `lib/api/*`.
5. **Auth gate thật:** `GET /api/auth/setup-status` → nếu chưa setup thì `SetupWizard` gọi `POST /api/auth/setup` (atomic) → else `/login` (`POST /api/auth/login`, cookie HttpOnly). Role lấy từ `GET /api/auth/me` (session), **không có role switcher giả**. HR/ESS phân nhánh route theo role.
6. **Assistant thật:** xóa route `/api/gemini` mô phỏng; `AiChat` gọi `lib/api/assistant.ts` (HR) / `employee-assistant.ts` (ESS). Draft Action → BE trả proposal → user confirm → frontend gọi **write endpoint thật** (human-in-the-loop, đúng `CONTEXT.md`).
7. **BE base URL** qua `NEXT_PUBLIC_API_URL` (giống `frontend/`). Cookie credentials: `credentials: 'include'`.
8. **Error-code → message:** build `vroom-hr/lib/api/error-codes.ts` từ registry trong `backend/AGENTS.md`; render theo `error_code` BE trả, không tự chế message.
9. **GiữDesignSystem AI Studio** (slate/indigo, font, motion). Không phải Heritage/Warm-Professional của `frontend/` cũ — đây là design system mới do AI Studio quyết.

## 3. Phạm vi BE — endpoint map (theo module, để sub-agent wire)

| Module BE | Endpoint chính | Usage UI AI Studio |
|---|---|---|
| Identity | `GET /api/auth/setup-status`, `POST /api/auth/setup`, `/login`, `/refresh`, `/logout`, `/change-password`, `/me` | Setup wizard, login, session gate |
| Admin | `/api/admin/{users,users/{id}/role,whitelist,organization/domains,audit-logs}` | Settings, users, whitelist, audit |
| Google | `/api/auth/organization-google-connection*` | Gmail connection, calendars, selected-calendar |
| Gmail | `/api/gmail/{sync,messages,attachments,classification}`, `/api/outbound-emails*`, `/api/gmail/import/*` | Inbox, compose, historical import |
| Recruitment | `/api/recruitment/{inbox,job-applications,candidates,job-openings,cv-review,metrics,calendar-conflicts}` | Recruitment tab group |
| Onboarding | `/api/onboarding/*` | Onboarding list/detail/checklist |
| Employee | `/api/employees*`, `/api/departments*`, `/api/positions*`, `/api/documents*`, `/api/employees/{id}/account` | Employee dir, import, documents |
| Attendance | `/api/attendance/{me/*,records*,settings/network*}` | ESS check-in/out, HR correction, allowlist |
| Employee Request | `/api/employee-requests/{leave,overtime}*`, `/api/admin/employee-requests*` | ESS requests, HR review queue |
| Payslip | `/api/admin/payslips*`, `/api/payslips/me*` | HR Payslip CRUD/publish, ESS read |
| HR Assistant | `/api/assistant/*` | AiChat (HR) + Draft Action confirm |
| ESS Assistant | `/api/ess/assistant/*` | AiChat (ESS) |
| Runtime | `/api/runtime/health` | Dashboard worker health |

**Error codes:** render theo registry trong `backend/AGENTS.md` (ví dụ `AUTH_SETUP_ALREADY_COMPLETED`, `LEAVE_OVERLAP`, `INSUFFICIENT_LEAVE_BALANCE`, `ALREADY_CHECKED_IN`, `OVERTIME_LIMIT_EXCEEDED`, `INVALID_STATUS_TRANSITION`, `GMAIL_NOT_CONNECTED`, `PERIOD_ALREADY_CLOSED` …).

## 4. Phân task theo phase (dispatch sub-agent)

### Phase 0 — Foundation (CRITICAL PATH, blocks mọi thứ) — 1 worker

Mục tiêu: `vroom-hr/` boot được như frontend thật, gate auth/setup/login dùng BE, scaffold route + data layer sẵn cho feature.

- Copy `frontend/src/lib/api/*` → `vroom-hr/lib/api/*`; tạo `lib/api/client.ts` (fetch base URL + `credentials:'include'` + error-code parse); `lib/api/error-codes.ts`.
- Copy `frontend/src/lib/query-client.ts`; setup `Providers` (React Query) trong `app/layout.tsx`.
- Tạo `lib/auth/session.ts` + `useSession()` (gọi `/api/auth/me`); `middleware.ts` bảo vệ route theo role.
- `app/setup/page.tsx`: port `SetupWizard` gọi `GET setup-status` + `POST setup` thật; xử lý `AUTH_SETUP_ALREADY_COMPLETED`, backend unavailable + retry, success → dashboard no re-login.
- `app/login/page.tsx` + `app/change-password/page.tsx`: port từ `frontend/` hoặc viết mới theo design AI Studio, gọi BE thật.
- Tách `app/(dashboard)/layout.tsx` (HR sidebar, badges thật) + `app/(employee)/layout.tsx` (ESS sidebar) từ monolith; xóa "Simulation Controller" + role switcher + simulated IP.
- `app/(dashboard)/dashboard/page.tsx`: metrics thật (`/api/recruitment/metrics`, `/api/runtime/health`) + audit log (`/api/admin/audit-logs`).
- Xóa `app/api/gemini/route.ts` (sẽ thay bằng client gọi `/api/assistant` ở Phase 3).
- Tạo convention: mỗi feature page dùng hook `lib/api/<module>` + render theo error_code; reuse UI primitives từ `components/` ( карточки, list, badge, proposal card).
- Acceptance: `pnpm build` pass; smoke `/setup`→`/login`→dashboard với BE chạy; không còn `localStorage` simulation.

### Phase 1 — Recruitment Backbone (sau Phase 0) — 1 worker

- `recruitment/inbox`, `recruitment/job-applications` → `/api/recruitment/inbox*`, `job-applications*` (correct-intent/dismiss/split/link-proposal/corrections).
- `recruitment/candidates` (+`[id]`) → pipeline `new→reviewing→interview_scheduled→accepted/rejected/archived`; accept/reject/archive; assignment (tối đa 1 Job Opening `open`).
- `recruitment/job-openings` → CRUD + open/close/cancel + headcount theo Candidate accepted.
- `recruitment/review` → CV review queue + provenance + correction.
- `recruitment/metrics`.
- `recruitment/interviews` (+ conflict manager) → tạo Interview (bắt buộc selected Calendar), lifecycle scheduled→completed/cancelled, reschedule/replacement, calendar conflict `410/412`.
- `onboarding` → count/list/detail, task pending/done, complete→Employee active.
- Settled: tạo Interview/complete interview **không tự đổi** Candidate pipeline (HR tường minh).
- Acceptance: lộycky path Email→Inbox→promote→Candidate→Interview→accept→Onboarding→checklist→Employee active chạy được với BE.

### Phase 2 — Operate (sau Phase 0, song song Phase 1) — 1 worker

- `employees` (+`[id]`, import, documents, account) → `/api/employees*`, departments, positions, documents (MinIO presigned), account creation (chỉ Employee active).
- `attendance` (HR records + correction có reason/audit, network allowlist CRUD) + ESS `attendance` (check-in/out hôm nay + history, validate CIDR/`ALREADY_CHECKED_IN`).
- `requests` (HR review: approve/reject cần reason) + ESS `requests` (leave/overtime: `LEAVE_OVERLAP`, `INSUFFICIENT_LEAVE_BALANCE`, `LEAVE_DATE_IN_PAST`, `OVERTIME_LIMIT_EXCEEDED`).
- `payroll/payslips` (HR list/create draft/edit/publish/delete) + ESS `payslips` (read-only đã publish; draft không lộ).
- **Không build** payroll config/allowance/tax (BE chưa có → 404) và attendance schedule/holiday UI phụ (đã gỡ).
- Acceptance: 4 luồng operate (Employee/Attendance/Request/Payslip) HR+ESS wire BE, render đúng error codes.

### Phase 3 — AI + Integrations (sau Phase 0, song song) — 1 worker

- `AiChat` (HR): thay `/api/gemini` bằng `/api/assistant/*`; giữ proposal card nhưng confirm → gọi **write endpoint thật** (tạo interview, accept candidate, send email). Draft-Tool chỉ `draft_interview_invitation`, `draft_congratulations_email`.
- `employee/assistant`: `/api/ess/assistant/*` (scoped, employee_id từ session).
- `gmail` tab: Organization Google Connection (OAuth/status/calendars/selected), sync, historical import preview/start/cancel, messages/attachments, classification view, compose/send (outbound `pending→sending→sent/failed`, chỉ gửi thật sau HR confirm).
- `settings`: AI Configuration (provider/model, policy preset, bật/tắt Automation/Assistant), tool registry bật/tắt, runtime health, audit logs (phân trang/lọc), whitelist/domains, users/role.
- Settled: AI **không bao giờ tự ghi**; mọi ghi do người xác nhận. Employee Assistant chỉ đọc/draft của chính Employee.
- Acceptance: chat HR tạo Draft Action → confirm → ghi thật; Gmail connect+send; settings thay đổi được audit.

## 5. Quy tắc chung cho sub-agent

- Đọc `CONTEXT.md`, `docs/project-status-2026-07-16.md`, `backend/AGENTS.md` trước khi code.
- Dùng thuật ngữ domain chuẩn (Organization, Candidate, Job Application, Interview, Onboarding, Employee active/inactive, Employee Request, Payslip, Draft Action …). Không tự đổi tên.
- Mọi write do người xác nhận; AI chỉ read/draft.
- Render badge/thông báo theo dữ liệu thật (không badge giả; phân biệt "trạng thái rỗng do bộ lọc" vs "rỗng dữ liệu").
- Tiếng Việt mặc định trong UI.
- Không reinvent API client — dùng `vroom-hr/lib/api/*` (đã copy ở Phase 0).
- Mỗi PR phải pass `pnpm build` + `pnpm lint`; ưu tiên test cho luồng critical.
- Báo cáo theo template: file đã sửa/thêm, luồng đã wire, blocker (nếu có).

## 6. Mối ràng buộc phase

```
Phase 0 (Foundation) ── blocks ──┬── Phase 1 (Backbone)
                                  ├── Phase 2 (Operate)
                                  └── Phase 3 (AI+Gmail)
```

Phase 1/2/3 chạy song song sau khi Phase 0 land và build pass.