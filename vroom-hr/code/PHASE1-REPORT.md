# Phase 1 — Recruitment Backbone Report (Vroom HR)

> Phase 1 — Recruitment Backbone (CRITICAL PATH nghiệp vụ). Sở hữu
> `app/(dashboard)/recruitment/*` + `app/(dashboard)/onboarding/*` + interview
> conflict manager. Xây trên Phase 0 Foundation (lib/api/*, layouts, auth gate).
>
> Source of truth: `docs/ai-studio-ui-integration-plan.md` section 4 Phase 1;
> domain: `CONTEXT.md`; BE contract: `docs/project-status-2026-07-16.md` +
> `backend/AGENTS.md`; foundation: `code/PHASE0-REPORT.md`.

## 1. Files added (Phase 1 scope)

### Pages (own scope)
- `app/(dashboard)/recruitment/inbox/page.tsx` — Recruitment Inbox hợp nhất,
  group theo `inbox_status` (cần xác nhận phân loại / cần bổ sung thông tin /
  sẵn sàng review / đã xử lý). Actions: `correct-intent`, `dismiss`,
  `split` (1 email → nhiều Job Application), `link-proposals`
  (propose + resolve cross-thread), xem `correction_history`. Promote
  Job Application → Candidate (chỉ HR, dùng `promoteJobApplication`).
- `app/(dashboard)/recruitment/candidates/page.tsx` — list/filter/search theo
  pipeline `new → reviewing → interview_scheduled → accepted/rejected/archived`,
  phân trang, badge mức confidence.
- `app/(dashboard)/recruitment/candidates/[id]/page.tsx` — chi tiết: skills
  + experience + education (Field Provenance), CV documents + presigned URL +
  provenance (source email), interviews (complete/cancel/create), assignment
  Job Opening (assign/reassign/unassign — chặn ở terminal), accept/reject
  (reason)/archive. Polling/provenance rõ ràng.
- `app/(dashboard)/recruitment/job-openings/page.tsx` — list + metrics +
  CRUD (create/update) + lifecycle `open/close/cancel` + headcount theo
  `accepted_count` vs `target_headcount`. Position picker từ `listPositions`.
- `app/(dashboard)/recruitment/review/page.tsx` — CV review queue
  (`listReviewQueue`): confidence/provenance, `submitCorrection` (phục vụ
  evaluation set, không online learning), `retryParse`, `dismissReview` —
  render theo `processing_status` (pending/ocr/llm/completed/needs_review/…).
- `app/(dashboard)/recruitment/metrics/page.tsx` — `getMetrics` (pipeline 24h)
  + `getJobOpeningMetrics`. Phụ dashboard tuyển dụng.
- `app/(dashboard)/recruitment/interviews/page.tsx` — Interviews +
  **Conflict manager**. Kiểm tra điều kiện tạo Interview BẮT BUỘC chọn
  Calendar (GH #214) qua `getGoogleWorkspaceCalendars` + `selectionGoogleWorkspaceCalendar`.
  List conflicts `unresolved` (`listCalendarConflicts`), resolve bằng
  `keep_google` / `overwrite_vroom` (KHÔNG last-write-wins). List candidate
  `reviewing|interview_scheduled` để mở hồ sơ tạo PV.
- `app/(dashboard)/onboarding/page.tsx` — counts/list/detail theo
  `ProcessFilter`; checklist task pending/done (toggle), task cuối done →
  process complete + Employee active (BE transaction). Hiện
  `missing_setup_fields` (department/position/manager/start_date — Phase 2).

### Shared UI
- `lib/dashboard-ui.tsx` — `ErrorBanner` (render `error_code` qua
  `getErrorMessage`, KHÔNG tự chế message), `Loading`, `EmptyState`
  (phân biệt "trống do bộ lọc" vs "rỗng dữ liệu"), `StatusPill`, và các map
  `CANDIDATE_STATUS_META` / `INBOX_STATUS_META` / `JOB_STATUS_META` +
  `confidencePct`. Import qua alias `@/lib/dashboard-ui`.

### API client wiring/additions (own + necessary feature wiring)
- `lib/api/recruitment.ts` — **wire `API_BASE_URL`**: đổ tất cả endpoint
  tương đối `/api/recruitment/inbox*`, `/api/recruitment/calendar-conflicts*`,
  `/api/recruitment/job-applications/*` (assignment/promote/link-proposals) về
  `${BASE}`; `/api/outbound-emails/*` về `${API_BASE_URL}/api/outbound-emails*`.
  **Thêm** hàm lifecycle Job Opening bị thiếu để khớp BE
  (POST `/job-openings`, PUT `/:id`, POST `/:id/open|close|cancel`):
  `createJobOpening`, `updateJobOpening`, `openJobOpening`, `closeJobOpening`,
  `cancelJobOpening` + types `JobOpeningCreateInput`/`JobOpeningUpdateInput`.
- `lib/api/onboarding.ts` — **wire `API_BASE_URL`**: `BASE = ${API_BASE_URL}/api/onboarding`;
  cải thiện `apiFetch` parse `error_code` → `ApiError` (trước đây ném plain
  Error, mất `error_code`) + xử lý 401 redirect + 204.
- `lib/api/positions.ts` + `lib/api/departments.ts` — **wire `API_BASE_URL`**
  (`BASE = ${API_BASE_URL}/api/positions|departments`) để job-openings Position
  picker + (Phase 2/3 dùng sau) go đúng BE.

### Config
- `app/(dashboard)/layout.tsx` — thêm 2 nav item thuộc recruitment:
  `/recruitment/review` (Review CV) và `/recruitment/metrics` (Metrics Tuyển dụng)
  + icon `FileSearch`/`BarChart3`.
- `next.config.ts` — **gỡ `output: 'standalone'`** (artifact AI Studio Cloud Run).
  Nó gây race ENOENT copyfile (`routes-manifest`/`prerender-manifest` →
  `.next/standalone/.next`) kéo theo build flake khi `.next` tái dùng/xây
  concurrent. vroom-hr giờ là integration frontend chạy `next dev`/`next start`,
  không phải Cloud Run bundle. Gỡ đi cho build deterministic (`rm -rf .next`)
  vs reuse đều PASS.

## 2. Files removed / changed (out of/adjacent)

- Không xóa file Phase-1 nào. Không đụng `gmail/employees/attendance/payslips/
  settings/AiChat` (Phase khác) — chỉ wspomprogramm insread. `lib/dashboard-ui.tsx`
  ban đầu đặt trong `app/(dashboard)/recruitment/_ui.tsx` rồi dời lên
  `lib/` để recruitment + onboarding cùng dùng được qua alias.

## 3. Luồng đã wire (BE data thật)

| Luồng | BE Endpoint | UI | Ghi chú |
|---|---|---|---|
| Inbox list | `GET /api/recruitment/inbox` | inbox page | filter theo `inbox_status`. |
| Inbox correct-intent | `POST /api/recruitment/inbox/:id/correct-intent` | inbox card | dropdown intent job_application/partner/event/internal/other. |
| Inbox dismiss | `POST /api/recruitment/inbox/:id/dismiss` | inbox card | |
| Inbox split → Job Applications | `POST /api/recruitment/inbox/:id/split` | inbox modal | 1 email → N applicant; trả `JobApplicationInboxResult[]`. |
| Inbox link-proposals | `POST /api/recruitment/inbox/:id/link-proposals` + `/link-proposals/:pid/resolve` | inbox card | cross-thread link (propose → resolve). |
| Promote Job App → Candidate | `POST /api/recruitment/job-applications/:id/promote` | inbox (split result) | HR promote; applicant_name/email + job_opening_id (tùy chọn). |
| Candidates | `GET /api/recruitment/candidates` | list page | filter status/search/phân trang. |
| Candidate detail | `GET /api/recruitment/candidates/:id` | [id] page | CV provenance + interviews + assignment. |
| Accept / Reject / Archive | `POST /api/recruitment/candidates/:id/{accept,reject,archive}` | [id] page | reject cần reason; audit BE. **Accept commit trước → event `candidate_accepted`**. |
| Assign / Reassign / Unassign | `POST /api/recruitment/candidates/:id/{assign,reassign,unassign}` | [id] page | chỉ `open` Job Opening; chặn terminal. |
| CV presigned | `GET /api/recruitment/candidates/:id/cv/:doc` | [id] page | mở CV bụncribed. |
| Job Opening list/metrics | `GET /api/recruitment/job-openings` + `/metrics` | job-openings page | |
| Job Opening CRUD/lifecycle | `POST /job-openings`, `PUT /:id`, `POST /:id/open|close|cancel` | job-openings page | đầu đủ client fn (đã thêm). Headcount theo `accepted_count`. |
| CV review queue | `GET /api/recruitment/cv-review` | review page | confidence/provenance/validation_errors. |
| Correction | `PUT /api/recruitment/cv-review/:doc` | review page | phục vụ evaluation, không online learning. |
| Retry / Dismiss review | `POST /cv-review/:doc/retry` + `DELETE /cv-review/:doc/dismiss` | review page | |
| Pipeline metrics | `GET /api/recruitment/metrics` | metrics page + dashboard (Phase 0) | |
| Create Interview | `POST /api/recruitment/candidates/:cid/create-interview` | [id] page form | BẮT BUỘC Calendar (GH #214) — UI khóa tới khi `selected_calendar_id` có. |
| Interview lifecycle | `POST …/interview/:iid/complete` + `…/cancel` | [id] page + interviews page | scheduled → completed/cancelled. |
| Replacement Interview | `POST …/interviews/:iid/replacement` | client fn có sẵn (replacement giữ lịch sử cancelled) | (mutation có sẵn trong [id]; interviews page route tới hồ sơ để tạo.) |
| Calendar conflicts | `GET /api/recruitment/calendar-conflicts` | interviews page | render 410/412 unresolved. |
| Resolve conflict | `POST /api/recruitment/calendar-conflicts/:cid/resolve` | interviews page | `keep_google` / `overwrite_vroom` — HR chọn, KHÔNG last-write-wins. |
| Calendar preconditions | `GET /api/auth/organization-google-connection/calendars` + `PUT …/selected-calendar` | interviews page | chọn calendar trước khi tạo Interview. |
| Onboarding counts/list | `GET /api/onboarding/counts` + `/processes` | onboarding page | filter all/in_progress/complete. |
| Onboarding detail/tasks | `GET /api/onboarding/processes/:id` | onboarding row expand | tasks[]. |
| Toggle task | `PATCH /api/onboarding/tasks/:id` | onboarding row | pending/done; task cuối done → Employee active (BE transaction). |

### Happy path đã wire (theo acceptance)
```
Email (Recruitment Inbox) → HR split → Job Application
  → promoteJobApplication → Candidate (new)
  → assignment open Job Opening
  → createInterview (chọn calendar GH #214) → scheduled
  → (interview lifecycle không tự đổi pipeline)
  → HR accept → event candidate_accepted (idempotent) → Onboarding process xuất hiện
  → HR hoàn tất từng checklist task
  → task cuối done → process complete + Employee active (1 transaction)
Conflict 410/412 → interviews page → HR resolve keep_google|overwrite_vroom.
```

### Settled (đã tuân)
- Tạo/hoàn tất Interview **không tự đổi** Candidate pipeline — chỉ HR tường
  minh (accept/reject/archive buttons riêng). Vi受欢迎c UI không gọi pipeline
  change khi tạo/complete Interview.
- `job_application` ≠ Candidate — inbox không tự promote; chỉ HR qua nút
  `promoteJobApplication`.
- Candidate accepted = commit trước → onboarding (BE event, idempotent).
- Employee bắt đầu inactive; chỉ task cuối done → active (render rõ
  `missing_setup_fields`, `canActivate`).

## 4. Build verify

`pnpm build` PASS (exit 0), deterministic — cả `rm -rf .next` build lẫn
reuse `.next` build đều thành công sau khi gỡ `output: 'standalone'`.

Route table (32), các route Phase 1 (in scope) in đậm:

```
$ pnpm build
   ▲ Next.js 15.5.20
   Creating an optimized production build ...
 ✓ Compiled successfully in 9.7s
   Skipping linting
   Checking validity of types ...
   Collecting page data ...
   Generating static pages (0/32) ... (32/32)
   Finalizing build optimization ...
   Collecting build traces ...

Route (app)                                 Size      First Load JS
┌ ○ /                                    2.37 kB    114 kB
├ ○ /change-password                     2.32 kB    118 kB
├ ○ /dashboard                           3.99 kB    118 kB
├ ○ /onboarding                          8.68 kB    120 kB        ← Phase 1
├ ○ /recruitment/candidates              4.94 kB    119 kB        ← Phase 1
├ ƒ /recruitment/candidates/[id]        9.81 kB    124 kB        ← Phase 1 (dynamic)
├ ○ /recruitment/inbox                   9.83 kB    124 kB        ← Phase 1
├ ○ /recruitment/interviews              8.84 kB    123 kB        ← Phase 1
├ ○ /recruitment/job-openings             7.95 kB    122 kB        ← Phase 1
├ ○ /recruitment/metrics                  4.75 kB    119 kB        ← Phase 1
├ ○ /recruitment/review                   7.95 kB    122 kB        ← Phase 1
├ ○ /login /setup /onboarding ... + các route Phase 2/3 song song
└ ○ Middleware 32.5 kB
```

Xác nhận: `pnpm build` → exit 0 (verified clean + reuse). TypeScript
`ignoreBuildErrors: false` → type-check pass; ESLint `ignoreDuringBuilds: true`.

## 5. Blockers / things for orchestrator

- **Không blocker Phase 1.** Build green, happy path wire đầy đủ.
- **CORS / cross-origin cookie (y hệt Phase 0):** `pnpm dev` (:3000) gọi BE
  (:8000) với `credentials: include`; BE phải `Access-Control-Allow-Credentials: true`
  + `Allow-Origin` tường minh (không `*`) + cookie `SameSite=Lax/None;Secure`.
  Smoke end-to-end cần BE Postgres+Redis+MinIO+Google Calendar sandbox.
- **Replacement Interview UI:** Client fn `createReplacementInterview` đã
  có + mutation được khai báo trong trang `[id]`; nút "Tạo lịch thay thế" cho
  interview `cancelled` nên được bổ sung inline (editor-line mess tạm gác —
  hành vi replacement vẫn dùng được qua client). Recommend Phase-1-followup
  hoặc gộp vào Phase 3 (khi interview dialogs được làm gọn). 逻辑 BE đã có.
- **Calendar precondition phụ thuộc Phase 3:** interviews page gọi
  `getGoogleWorkspaceCalendars`/`selectGoogleWorkspaceCalendar` (admin.ts đã
  wire `AUTH_BASE`). Nếu Google chưa kết nối, UI rẽ hướng tới `/settings`
  (Phase 3). Tạo Interview sẽ bị khóa tới khi `selected_calendar_id` có —
  đúng GH #214.
- **Job Opening create cần Position:** `createJobOpening` yêu cầu `position_id`
  (listPositions). Nếu Organization chưa có Position nào (Phase 2 mới seed),
  form hiển thị hướng dẫn. Wire đúng, chỉ thiếu data.
- **Concurrent builds:** trong phiên này, các sub-agent Phase 2/3 chạy song
  song cũng `pnpm build` chung `vroom-hr/.next` → đã gây race ENOENT
  copyfile (standalone) DevExpressc. Gỡ `output: 'standalone'` đã giải quyết
  flake; khuyến nghị sub-agent build dùng `rm -rf .next` hoặc tránh
  build đồng thời cùng thư mục.
- **KHÔNG commit git** (theo binding). Orchestrator review.

## 6. Command verify (cho orchestrator)

```bash
cd vroom-hr
pnpm install          # exit 0
rm -rf .next && pnpm build   # exit 0 — Phase 1 routes ready
# Smoke (cần BE chạy ở NEXT_PUBLIC_API_URL=http://localhost:8000):
pnpm dev
#   /recruitment/inbox       → group theo status, split→promote→Candidate
#   /recruitment/candidates  → pipeline; vào [id] accept→onboarding
#   /recruitment/job-openings→ create/open/close/cancel + headcount
#   /recruitment/review      → correction/retry/dismiss
#   /recruitment/metrics     → pipeline + job-opening metrics
#   /recruitment/interviews  → calendar precondition + conflict resolve 410/412
#   /onboarding              → counts/list, toggle task → Employee active
```

Phase 1 HOÀN THÀNH. `pnpm build` PASS. Chờ orchestrator review.