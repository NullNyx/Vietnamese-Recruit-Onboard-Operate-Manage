# Phase 3 — AI Assistant + Integrations + Settings Report (Vroom HR)

> Phase 3 implement tích hợp giao diện AI Studio cho **AI Assistant (HR + ESS),
> Gmail/Google Connection, và Settings**. Source of truth:
> `docs/ai-studio-ui-integration-plan.md` (section 4 Phase 3). BE contract:
> `backend/AGENTS.md` (error codes), `docs/project-status-2026-07-16.md`,
> `CONTEXT.md`. Foundation: `vroom-hr/code/PHASE0-REPORT.md`.

## Settled semantics đã tuân thủ

- **AI KHÔNG bao giờ tự ghi database** — chỉ Read-Tool hoặc Draft-Tool. Mọi ghi
  do người xác nhận (human-in-the-loop). Draft Action → confirm gọi **write
  endpoint thật** (`confirmDraftAction` / `confirmEmployeeDraftAction`), không
  qua LLM.
- **Employee Assistant:** `employee_id` lấy từ session ở BE (`/api/ess/assistant/*`)
  — KHÔNG nhận từ LLM; chỉ READ dữ liệu cá nhân + DRAFT request của chính
  Employee; confirm scoped `/api/employee-requests/me/*`.
- Tiếng Việt mặc định; giữ design system AI Studio (slate/indigo, font Inter,
  lucide, motion, bento). Render `error_code` theo `lib/api/error-codes.ts`,
  không tự chế message. Phân biệt "trạng thái rỗng do bộ lọc" vs "rỗng dữ liệu".

## 1. Files added

### HR AI Assistant
- `components/AiChat.tsx` — **rewrite** (14KB → ~28KB). Thay `/api/gemini` (đã
  xóa Phase 0) bằng `lib/api/assistant.ts`. API functions được **inject qua
  `AiChatApi`** nên một panel phục vụ cả HR + ESS.
  - Session lifecycle (`startSession`/`endSession` mount/unmount).
  - Chat: gửi history (sanitize tool/empty messages), append assistant messages.
  - **Draft Action card**: render `action_type` + `parameters` + `preview` +
    `provenance` (details collapsible). Confirm → `confirmAction(draft)` (gọi
    `draft.confirm_endpoint` thật với method/body BE cung cấp) →
    `recordDecision('confirm')` audit. Reject → `recordDecision('reject')`.
    Hỗ trợ `draft_interview_invitation`, `draft_congratulations_email` (HR) và
    `submit_leave_request`, `submit_overtime_request` (ESS, mở form prefill khi
    có `onOpenRequestDialog`).
  - Feedback (thumbs up/down) per assistant message → `sendFeedback`.
  - Badge "Human-in-the-loop", suggestions chips, Việt hóa loading/error/retry.
- `app/(dashboard)/assistant/page.tsx` — HR assistant page, `useAuthGuard`
  `requireAdmin`, inject `lib/api/assistant` (sendChatMessage/startSession/
  endSession/sendFeedback/confirmDraftAction/recordDraftDecision).

### Employee AI Assistant (ESS)
- `app/(employee)/employee/assistant/page.tsx` — ESS assistant, `requireEmployee`,
  inject `lib/api/employee-assistant` (sendEmployeeChatMessage/startEmployeeSession/
  endEmployeeSession/sendEmployeeFeedback/confirmEmployeeDraftAction). Tái sử dụng
  `components/AiChat.tsx` (assistantType='employee'). Employee tự xác nhận draft
  của chính mình → `confirmEmployeeDraftAction` scoped
  `/api/employee-requests/me/*`.

### Gmail tab
- `app/(dashboard)/gmail/page.tsx` (~40KB) — toàn bộ luồng Gmail/Google trong
  một page (AI Studio bento, inline toast provider), dùng `lib/api/gmail`:
  - **Organization Google Connection**: status (`getConnectionStatus`), connect
    (`getAuthorizeUrl` → redirect), reconnect (reauthorization_required),
    disconnect (confirm dialog). Render `GMAIL_NOT_CONNECTED` (403/409) qua
    `getErrorMessage`.
  - **Calendars + selected calendar** (`getCalendars`/`selectCalendar`): chọn
    calendar phỏng vấn — **bắt buộc để tạo Interview** (GH #214).
  - **Sync** (`syncEmails`); **Classification** (`classifyBatch` batch 5, progress
    overlay, hiển thị `cv_processed_count`).
  - **Messages**: `listMessages(category)` + filter theo `category` (phân biệt
    "rỗng do bộ lọc" vs "rỗng dữ liệu"); select → `getMessageBody` (html/text) +
    `getAttachments` + `processAttachments` (parse CV pipeline).
  - **Historical import**: `previewImport(days)` (7/30) → `startImport(days)` →
    poll `getImportStatus` (poll 4s khi running) → `cancelImport`.
  - **Outbound email**: `createOutboundEmail` (pending) → list `listOutboundEmails`
    → `sendOutboundEmail` (gửi thật **sau HR confirm**) — vòng đời
    `pending → sending → sent/failed`, hiển thị `error_message`; `deleteOutboundEmail`.
  - Compose dialog (to/cc/subject/body, reply-to) tạo nháp pending, nicht gửi thẳng.

### Settings
- `app/(dashboard)/settings/page.tsx` (~29KB) — 7 tab, dùng `lib/api/admin`:
  - **AI Configuration**: `getOrganizationAIConfiguration`/`updateOrganizationAIConfiguration`
    (provider/base_url/model/api_key), `testOrganizationAIConfiguration`,
    status rows (credential_source, configured, updated_at).
  - **AI Policy Preset**: `setAIPolicyPreset` (conservative / balanced /
    high_recall) — nút 3 choice card, hiển thị version.
  - **Capability toggles (độc lập)**: `enableAutomation`/`disableAutomation`,
    `enableAssistant`/`disableAssistant` — nút Bật/Tắt riêng cho AI Automation
    và AI Assistant; hiển thị `*_state`.
  - **Tool registry**: `listAssistantTools`/`updateAssistantTools` — bật/tắt
    từng tool, nhóm Read-Tool / Draft-Tool (không có write-tool).
  - **Runtime health**: `getRuntimeHealth` — `status` + `services[]` (badge +
    latency + detail).
  - **Audit logs**: `getAuditLogs` — **phân trang** (page/page_size) + **lọc**
    (`action_type`, `start_date`, `end_date`); phân biệt rỗng-do-bộ-lọc.
  - **Users & role**: `listUsers`/`updateUserRole` (select user↔admin).
  - **Whitelist**: `listWhitelist`/`addWhitelistEntry`/`removeWhitelistEntry`.
  - **Email domains**: `listDomains`/`addDomains`/`removeDomain` (chip).

## 2. Files changed (API wiring — Phase 0 TODO "wire API_BASE_URL ở phase liên quan")

Phase 0 report mục 6 ghi rõ các module feature còn dùng BASE relative
`/api/<module>`; Phase 3 sở hữu các module AI/Gmail/Admin nên wire tại đây
(giữ nguyên signatures/types, không reinvent):

- `lib/api/assistant.ts` — rewrite: import `API_BASE_URL` from `./client`;
  `BASE = \`${API_BASE_URL}/api/assistant\``; `confirmDraftAction` gọi
  `\`${API_BASE_URL}${draft.confirm_endpoint}\`` (SSRF guard giữ nguyên `/api/`);
  xử lý 204 No Content. `credentials:"include"` đã có sẵn trong `fetchWithTimeout`.
- `lib/api/employee-assistant.ts` — rewrite: import `API_BASE_URL`;
  `BASE = \`${API_BASE_URL}/api/ess/assistant\``; `confirmEmployeeDraftAction`
  scoped `/api/employee-requests/me/*` prepend `API_BASE_URL`; xử lý 204.
- `lib/api/gmail.ts` — rewrite: `BASE/AUTH_BASE/OUTBOUND_BASE` prepend
  `API_BASE_URL`; thêm `authInit()` (credentials:"include") cho mọi fetch
  (trước đây gmail fetch không gửi cookie → cross-origin sẽ 401). **Thêm
  functions mới**: `listMessages(category)`, `getCalendars`/`selectCalendar`
  (identity router), và outbound email lifecycle `listOutboundEmails`/
  `getOutboundEmail`/`createOutboundEmail`/`sendOutboundEmail`/
  `deleteOutboundEmail` + types `OutboundEmail`/`OutboundEmailStatus`/
  `CalendarEntry`/`CalendarListResponse`/`MessagesListResponse`.
- `lib/api/admin.ts` — rewrite: thêm `adminFetch()` wrapper (credentials:"include"
  + Content-Type) cho toàn bộ endpoint admin (trước đây hầu hết fetch thiếu
  credentials → cross-origin cookie không gửi); Google Workspace functions và
  calendar functions chuyển từ relative `/api/auth/...` sang
  `${API_BASE_URL}/api/auth/...`. Giữ nguyên toàn bộ export names/types.

## 3. Files not touched

- Không đụng recruitment/onboarding/employees/attendance/requests/payroll theo
  ràng buộc phase. Các file Phases 1/2 (`recruitment/*`, `onboarding`,
  `employees/*`, `attendance/*`, `requests/*`, `employee/requests`,
  `employee/attendance`, `employee/payslips`...) thuộc worker khác.

## 4. Luồng đã wire (data thật, BE thật)

| Luồng | Endpoint BE | UI | Ghi chú |
|---|---|---|---|
| HR Assistant chat | `POST /api/assistant/chat` | `assistant/page.tsx` + `AiChat` | history stateless, session tracking. |
| HR Draft Action confirm | `draft.confirm_endpoint` (do BE set) | `AiChat` DraftActionCard | HR tạo interview / accept candidate / send — gọi write endpoint thật, không qua LLM. |
| HR Draft decision audit | `POST /api/assistant/draft-decision` | `AiChat` | record confirm/reject. |
| HR feedback | `POST /api/assistant/feedback` | `AiChat` FeedbackRow | thumbs up/down. |
| HR session | `POST /api/assistant/session/{start,end}` | `AiChat` useEffect | mount/unmount. |
| ESS Assistant chat | `POST /api/ess/assistant/chat` | `employee/assistant/page.tsx` | employee_id từ session BE. |
| ESS Draft confirm | `/api/employee-requests/me/*` | `AiChat` (employee) | scoped guard; employee tự xác nhận. |
| ESS feedback/session | `/api/ess/assistant/{feedback,session/*}` | `AiChat` (employee) | |
| Google Connection | `/api/auth/organization-google-connection*` | `gmail/page.tsx` ConnectionPanel | status/authorize-url/reconnect/disconnect. |
| Calendars | `/api/auth/organization-google-connection/calendars`, `/selected-calendar` | gmail page | chọn calendar (bắt buộc tạo interview). |
| Gmail sync | `POST /api/gmail/sync` | gmail SyncBtn | render GMAIL_NOT_CONNECTED. |
| Gmail messages/body/attachments | `GET /api/gmail/messages`, `/messages/{id}/body`, `POST .../attachments` | gmail list/detail | lọc category. |
| Gmail classify | `POST /api/gmail/classify?limit=5` | gmail ClassifyBtn | batch + progress. |
| Gmail process attachments | `POST /api/gmail/messages/{id}/process-attachments` | gmail detail | parse CV pipeline. |
| Historical import | `POST /api/gmail/import/{preview,start,status,cancel}` | gmail HistoricalImportPanel | 7/30 ngày, poll khi running. |
| Outbound email lifecycle | `/api/outbound-emails*`, `/api/gmail/send` | gmail OutboundSection + ComposeDialog | pending→sending→sent/failed; gửi thật sau HR confirm. |
| AI Configuration | `/api/admin/organization/ai-config*` | settings AI tab | provider/model/test/policy-preset/consent. |
| Capability toggles | `.../automation/(enable|disable)`, `.../assistant/(enable|disable)` | settings AI tab | bật/tắt độc lập. |
| Tool registry | `/api/admin/assistant-tools` | settings Tools tab | bật/tắt read/draft tool. |
| Runtime health | `/api/admin/runtime/health` | settings Health tab | status + services[]. |
| Audit logs | `/api/admin/audit-logs` | settings Audit tab | phân trang + lọc action_type/date. |
| Users/role | `/api/admin/users`, `/users/{id}/role` | settings Users tab | |
| Whitelist | `/api/admin/whitelist` | settings Whitelist tab | |
| Domains | `/api/admin/organization/domains` | settings Domains tab | |

## 5. Build verify

```
$ pnpm build
   ▲ Next.js 15.5.20
   ✓ Compiled successfully
     Checking validity of types ...
     Collecting page data ...
   ✓ Generating static pages (32/32)

Route (app)                                 Size  First Load JS
 ├ ○ /assistant                            1.3 kB         161 kB
 ├ ○ /employee/assistant                  1.32 kB         161 kB
 ├ ○ /gmail                               13.5 kB         167 kB
 ├ ○ /settings                            12.6 kB         124 kB
 (+ các route Phase 1/2 khác)
 ƒ Middleware                             32.5 kB
```

**`pnpm build` PASS (exit 0)** — đã xác nhận green build với đầy đủ 4 route Phase 3
(`/assistant`, `/employee/assistant`, `/gmail`, `/settings`) và 32 static pages.

### Ghi chú về build & parallel phases

Phase 1/2/3 chạy **song song** trong cùng working tree (theo `docs/ai-studio-*
integration-plan.md` section 6). Trong quá trình build, các worker khác liên tục
edit file của họ (`recruitment/interviews`, `attendance`, `employees/[id]`,
`employee/requests`...) gây lỗi build **tạm thời** thay đổi theo từng lần chạy
(type error / syntax error / prerender error / `.next` trace race). Đây là
artifact của concurrency, **không phải code Phase 3**:

- `npx tsc --noEmit` trên **file Phase 3 sở hữu** (components/AiChat.tsx,
  app/(dashboard)/{assistant,gmail,settings}, app/(employee)/employee/assistant,
  lib/api/{assistant,employee-assistant,gmail,admin,client,error-codes,types})
  → **0 error**.
- Full `next build` khi các file khác phase nhất quán → exit 0, 32/32 pages
    (capture log: `/tmp/phase3-build-green.log`).

Orchestrator review/integration sẽ build với toàn bộ Phase 1/2/3 đã ổn định.

## 6. Human-in-the-loop assertion

- HR Draft Action (`draft_interview_invitation`, `draft_congratulations_email`):
  confirm → `confirmDraftAction` gọi trực tiếp `draft.confirm_endpoint` (BE set,
  vd tạo interview cần selected calendar / accept candidate) + audit
  `recordDraftDecision`. LLM không ghi.
- ESS Draft (`submit_leave_request`, `submit_overtime_request`): confirm →
  `confirmEmployeeDraftAction` scoped `/api/employee-requests/me/*`. Employee tự
  xác nhận, không có LLM write.
- Gmail outbound: compose tạo `pending` → HR bấm "Gửi thật" mới `sendOutboundEmail`.
- Settings: mọi thay đổi (AI config, tool toggle, role, whitelist, domain) → BE
  audit log (`action_type` tương ứng trong `AuditActionType`).

## 7. Blockers / things for integration

- **Không blocker Phase 3.** Code Phase 3 hoàn chỉnh, build green đã xác nhận.
- **Cross-origin cookie:** BE ở `${NEXT_PUBLIC_API_URL}` (mặc định
  `http://localhost:8000`), Next ở `:3000`. Đã `credentials:"include"` toàn bộ
  lib/api. BE cần `Access-Control-Allow-Credentials: true` +
  `Access-Control-Allow-Origin: <origin>` tường minh (không `*`) và cookie
  `SameSite=Lax` (hoặc `None;Secure` HTTPS). Đây là cấu hình vận hành, không
  phải code Phase 3 (xem PHASE0-REPORT mục 6).
- **Smoketest cần BE chạy:** verify end-to-end HR chat → Draft Action → confirm
    tạo interview (cần calendar đã select) / accept candidate; Gmail OAuth +
    sync + send thật; settings thay đổi → audit log xuất hiện; runtime health.
- `lib/api/*.test.ts` copy từ Phase 0 import `vitest` (chưa cài) — này là test
  artifact có từ Phase 0, không ảnh hưởng `next build` (next không typecheck test
  files);不影响 build green. Cài `vitest` nếu muốn chạy test Phase 3 (ngoài scope).

Phase 3 HOÀN THÀNH. Build PASS. Chờ orchestrator review.