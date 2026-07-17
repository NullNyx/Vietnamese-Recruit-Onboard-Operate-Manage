# Báo cáo tình hình project Vroom HR

> **Snapshot:** 2026-07-16
> **Commit tham chiếu:** `b2a4814` (fix frontend header navigation — dark mode, breadcrumb, hover, layout, PR #253)
> **Phạm vi:** mã nguồn backend, frontend, migration, test và ADR hiện có trong repository.
> **Mục đích:** ghi nhận trạng thái hiện tại của hệ thống; đây là snapshot cần cập nhật lại khi code thay đổi.
> **Lưu ý:** thay thế snapshot `docs/project-status-2026-07-14.md`. Kể từ snapshot đó có **23 commit + 5 migration** (Alembic `070` → `075`).

## 1. Kết luận nhanh

| Hạng mục | Tình hình hiện tại | Đánh giá |
|---|---|---|
| Nền tảng | FastAPI + SQLModel + PostgreSQL + Redis + MinIO + ARQ; frontend Next.js/TypeScript/Tailwind/shadcn/ui | Đã có khung chạy đầy đủ |
| Database | Alembic ở revision `075` (head), 75 migration | Đã có migration liên tục |
| Identity | First-Run Setup atomic, local login, JWT cookie, refresh/logout, đổi mật khẩu, role HR/admin, whitelist, domain và audit log | Đã triển khai |
| Backbone tuyển dụng | Gmail → AI Automation → Job Application/Recruitment Inbox → Candidate → HR review → Interview → quyết định → Onboarding → Employee | Đã có các module và worker tương ứng |
| Gmail/Calendar | Organization Google Connection, ingestion, historical import, gửi email, Interview và calendar conflict; **ownership đã được enforce runtime** | Đã triển khai và đã hoàn tất chuyển đổi ownership |
| Onboarding | Event `candidate_accepted` đưa vào ARQ; tạo Employee inactive và checklist; hoàn tất checklist thì kích hoạt Employee | Đã triển khai |
| Employee Self-Service | Hồ sơ, tài liệu, chấm công, request, Payslip và Employee Assistant | Đã triển khai theo quyền Employee active |
| Attendance | Backend có check-in/check-out, lịch sử, HR correction và network allowlist; trang danh sách HR đã có | Backend/UI chính đã triển khai; các trang phụ (schedule/holiday/leave/overtime) đã bị gỡ khỏi UI |
| Payslip | HR tạo/sửa/publish/xóa draft; Employee chỉ xem Payslip đã publish | Đã triển khai một phần nghiệp vụ payroll |
| Payroll engine | Cấu hình lương, phụ cấp, thuế và tính payroll chưa có; trang frontend trả 404 (`notFound()`) | Chưa triển khai |
| AI Assistant | Read-Tool và Draft-Tool; không cấp write-tool cho LLM; HR xác nhận rồi frontend gọi write endpoint thật; Phase 1 có Context Block Builder + quality metrics | Đã triển khai theo human-in-the-loop |
| AI Automation | Phân loại email, parse CV, provenance, evaluation set, telemetry và rollout guardrails | Đã triển khai; cần tiếp tục đo chất lượng vận hành |
| UI/Design system | Redesign sang font Inter + palette "Warm Professional" (đỏ + amber + xanh, radius 6px) + Motion animations + 9 Playwright visual snapshot | Đã triển khai |
| Kiểm thử | 187 backend test + 51 frontend test + 9 Playwright snapshot | Đang duy trì |

**Kết luận:** repository đã vượt qua mức scaffold. Backbone tuyển dụng, onboarding, quản lý Employee, chấm công, request, Payslip và hai loại Assistant đều có code backend được wiring vào `backend/src/main.py`. Kể từ snapshot 07-14, ba hạng mục "đang hoàn thiện" lớn đã đóng: enforcement Google runtime ownership, migration Calendar/Interview, và gỡ placeholder attendance/payroll. Hai khoảng trống thật còn lại là **payroll engine** và **attendance UI phụ** (cả hai đã được gỡ/404 hóa chứ không còn placeholder "đang phát triển").

## 2. Nguồn và cách xác định trạng thái

| Nguồn | Nội dung dùng để đối chiếu |
|---|---|
| `backend/src/main.py` | Router thực sự được đăng ký và các worker/bootstrap liên quan |
| `backend/src/modules/**` | API, application service, domain entity, repository và worker |
| `frontend/src/app/**` | Các trang UI thật và các trang đã gỡ |
| `backend/alembic/versions/` | Lịch sử schema; revision hiện tại `075` (kiểm bằng `uv run alembic heads`) |
| `backend/tests/`, `frontend/src/**/__tests__` | Phạm vi contract đang được kiểm thử |
| `CONTEXT.md` và `docs/adr/` | Thuật ngữ domain, boundary và quyết định an toàn |

Các nhãn trong báo cáo:

- **Đã triển khai:** có route/service/UI hoặc worker tương ứng trong code hiện tại.
- **Đang hoàn thiện:** đã có một phần code hoặc backend, nhưng UI/contract/migration chưa hoàn chỉnh.
- **Chưa triển khai:** UI hoặc backend hiện chỉ trả 404/chưa có implementation nghiệp vụ.
- **Ngoài phạm vi:** được ghi nhận trong domain nhưng không thuộc release hiện tại.

## 3. Bảng tổng hợp đầy đủ tính năng hệ thống

| Nhóm | Tính năng | Logic và hành vi hiện tại | Bề mặt hệ thống | Trạng thái |
|---|---|---|---|---|
| Identity | First-Run Setup | Deployment mới kiểm tra `setup-status`; request setup tạo Organization và tài khoản HR đầu tiên trong một transaction nguyên tử (ADR-0001), trả authenticated session; xử lý concurrent setup chỉ một request thành công. | `/api/auth/setup-status`, `/api/auth/setup`, `/setup` | Đã triển khai |
| Identity | Đăng nhập và session | Local email/password login; access/refresh token trong HttpOnly cookie; refresh, logout, change-password; hỗ trợ cờ bắt buộc đổi mật khẩu. | `/api/auth/login`, `/refresh`, `/logout`, `/change-password`, `/me` | Đã triển khai |
| Identity | Phân quyền HR | Role `admin` là HR; dependency `require_admin` bảo vệ endpoint quản trị. Employee active được xác định riêng, không đồng nhất với User/HR. | `identity`, `employee` dependencies | Đã triển khai |
| Identity | Whitelist và allowed email domains | HR quản lý whitelist đăng nhập và domain được phép; mọi thay đổi quan trọng có audit. | `/api/admin/whitelist`, `/api/admin/organization/domains`, UI admin | Đã triển khai |
| Identity | User/role management | HR xem danh sách User và thay đổi role theo chính sách service; bootstrap super-admin qua `AUTH_SUPER_ADMIN_EMAIL` hoặc demo seed. | `/api/admin/users`, `/api/admin/users/{id}/role`, UI Users | Đã triển khai |
| Identity | Audit log | Ghi audit cho thay đổi role, setup, AI config, recruitment, onboarding, attendance correction và các integration action; HR xem log có phân trang/lọc. | `/api/admin/audit-logs`, repository/service audit | Đã triển khai |
| Organization | Organization settings | Một deployment tương ứng một Organization; lưu tên, mã số thuế, timezone, ngày nghỉ và domain theo domain glossary. | Identity/recruitment organization settings, UI settings | Đã triển khai một phần |
| Google | Organization Google Connection | Một connection dùng chung cho Organization; HR cấu hình OAuth, authorize, callback, reconnect, xem status, calendars, selected-calendar. Token/client secret phải được mã hóa ở backend theo ADR. **Ownership runtime đã được enforce** (commit `688e96d`). | `/api/auth/organization-google-connection*`, UI OAuth/Gmail | Đã triển khai |
| Google | Gmail ingestion | Gmail worker poll định kỳ (ARQ cron); connection singleton được kiểm tra trước khi poll; cursor/history và idempotency chống nhập trùng; cursor đã organization-scoped (migr `071`). | `gmail/worker.py`, `/api/gmail/sync`, Redis/ARQ | Đã triển khai |
| Google | Historical email import | HR preview cửa sổ 7/30 ngày, start, theo dõi status và cancel; import tách khỏi cursor sync mới. | `/api/gmail/import/*`, UI Historical Import | Đã triển khai |
| Gmail | Email workspace | Xem danh sách message, lấy body, đọc attachment metadata, lọc category/trạng thái xử lý và xem item cần HR review. | `/api/gmail/messages*`, UI Gmail | Đã triển khai |
| Gmail | Gửi email | Có outbound email command với vòng đời `pending → sending → sent/failed`; send/retry có idempotency; gửi thật chỉ sau hành động xác nhận của HR. | `/api/outbound-emails*`, `/api/gmail/send`, UI compose/send | Đã triển khai |
| AI Automation | Phân loại intent email | AI phân loại `job_application`, `partner`, `event`, `internal`, `other`; `job_application` là intent ứng tuyển, không phụ thuộc có CV hay không. Provider lỗi không làm mất event; item chờ retry hoặc xử lý tay. | Gmail classification service/worker, `/api/gmail/classify` | Đã triển khai |
| AI Automation | Parse CV | Attachment hợp lệ được fetch/validate, lưu bền vững khi đi vào Backbone Flow, parse thành structured draft; có OCR/MinIO adapter và checksum chống trùng; provenance ở migr `069`. | `/api/gmail/attachments/*`, recruitment CV processor | Đã triển khai |
| AI Automation | Provenance và correction | Structured field giữ provenance chỉ ra nguồn email/CV và mức cần HR xác nhận; HR có correction action, dữ liệu correction phục vụ đánh giá nhưng không biến thành online learning mù. | CV review, correction/evaluation services | Đã triển khai |
| AI Automation | Evaluation/rollout | Có Evaluation Set/Sample, telemetry rollout, policy preset, baseline/shadow/canary/rollback và guardrail recall; migr `067`/`070` thêm telemetry metadata và policy preset + capability consents. | `/api/recruitment/evaluation/*`, admin AI config/telemetry | Đã triển khai |
| Recruitment | Recruitment Inbox | Một workspace hợp nhất cho email/Job Application: cần xác nhận phân loại, cần bổ sung thông tin, sẵn sàng review, đã xử lý. Item không chắc chắn không tự tạo Candidate. Có correct-intent/dismiss/split/link-proposals/corrections. | `/api/recruitment/inbox*`, UI `/recruitment/inbox` | Đã triển khai |
| Recruitment | Job Application | AI có thể tạo Job Application từ email; một thread có thể nối nhiều message, một message có thể tách nhiều application; HR mới có quyền promote thành Candidate. Migr `068` thêm job application contract. | `/api/recruitment/job-applications*`, inbox actions | Đã triển khai |
| Recruitment | Candidate pipeline | Candidate đi qua `new → reviewing → interview_scheduled → accepted/rejected/archived`; có list/detail/filter/search, CV, accept/reject/archive và audit. | `/api/recruitment/candidates*`, UI recruitment | Đã triển khai |
| Recruitment | Job Opening | HR tạo, sửa, mở, đóng, hủy Job Opening; Candidate chỉ assignment vào Job Opening đang `open`; có metrics/headcount theo Candidate accepted. | `/api/recruitment/job-openings*`, UI Job Openings | Đã triển khai |
| Recruitment | Candidate assignment | Candidate có thể chưa gán hoặc gán tối đa một Job Opening; assign/reassign/unassign bị chặn ở status terminal. | Candidate service/router/UI dialogs | Đã triển khai |
| Recruitment | Review queue | HR xem CV review queue, confidence/provenance, thực hiện correction và tiếp tục xử lý. | `/api/recruitment/cv-review`, UI `/recruitment/review` | Đã triển khai |
| Recruitment | Metrics | Dashboard metrics cho pipeline và Job Opening; dùng dữ liệu live từ repository/service. | `/api/recruitment/metrics`, UI metrics | Đã triển khai |
| Interview | Tạo Interview | Interview là entity riêng, có round, start/end UTC, timezone IANA, mode, participant Employee/external và liên kết Calendar event; migr `072`/`073` thêm `interview_calendar_id` và `calendar_id` cho sync cursors; tạo event không tự đổi Candidate status. Bắt buộc selected Calendar (GH #214). | Candidate interview routes, UI interview dialogs | Đã triển khai |
| Interview | Lifecycle | `scheduled → completed/cancelled`; reschedule giữ entity; replacement tạo Interview mới và giữ lịch sử cancelled; complete/cancel không tự đổi Candidate pipeline. Migr `074` backfill Candidate calendar fields vào Interview và drop legacy columns (GH #215). | `/create-interview`, `/interviews/{id}/complete`, `/cancel`, `/replacement` | Đã triển khai |
| Calendar | Sync và conflict | Có selected calendar, sync cursor, ETag/conflict endpoint, xử lý deleted event và relink; conflict cần HR chọn hướng giải quyết thay vì last-write-wins; 410/412 conflict UX (GH #216). | Calendar adapter/sync/conflict router, UI conflict manager | Đã triển khai |
| Onboarding | Kích hoạt từ accepted | `accept_candidate` commit status rồi publish event `candidate_accepted`; ARQ consumer validate payload và retry tối đa 3 lần. | Recruitment event publisher, `onboarding/worker.py` | Đã triển khai |
| Onboarding | Tạo process nguyên tử | `start_from_event` idempotent theo candidate; tạo Employee inactive, OnboardingProcess và checklist trong một transaction. | Onboarding service/repository | Đã triển khai |
| Onboarding | Checklist và activation | HR xem process/count/detail; cập nhật task pending/done; hoàn tất task cuối cùng hoàn tất process và bật `Employee.is_active = true` trong cùng transaction. | `/api/onboarding/*`, UI `/onboarding` | Đã triển khai |
| Employee | Hồ sơ Employee | CRUD Employee, filter/list/detail, department, position, manager; Candidate accepted là nguồn chuyển vào Employee qua onboarding. | `/api/employees*`, UI Employees | Đã triển khai |
| Employee | Employee Account | HR xem/tạo account cho Employee; chỉ Employee active đủ điều kiện nhận account và đăng nhập ESS. | `/api/employees/{id}/account`, auth dependencies | Đã triển khai |
| Employee | Import và tài liệu | Import Employee từ file; tài liệu lưu qua MinIO, list/download/delete có phân quyền. | `/api/employees/import`, `/api/documents*`, UI import/documents | Đã triển khai |
| Attendance | Check-in/check-out | Employee active check-in/check-out theo ngày; ghi IP/source, ngăn thao tác trùng và kiểm tra network allowlist/trusted proxy. | `/api/attendance/me/*`, ESS attendance | Đã triển khai |
| Attendance | HR record và correction | HR lọc record theo date/Employee/status, sửa giờ vào/ra với reason bắt buộc và audit. | `/api/attendance/records*`, UI Attendance | Đã triển khai |
| Attendance | Network allowlist | HR xem, thay thế, thêm, xóa CIDR cho phép chấm công. | `/api/attendance/settings/network*`, settings UI | Đã triển khai |
| Attendance | Schedule/holiday/leave/overtime UI | Trang schedules, holidays, leave và overtime đã bị gỡ khỏi frontend (`46199ec`); nav chỉ còn "Danh sách". Leave/overtime request vẫn có ở module Employee Request. | Frontend attendance subpages | Chưa triển khai (đã gỡ) |
| Employee Request | Leave request | Employee active tạo/hủy/xem request nghỉ; request thuộc Employee và chờ HR review. | `/api/employee-requests/leave*`, ESS Requests | Đã triển khai |
| Employee Request | Overtime request | Employee active tạo/hủy/xem request làm thêm; validate thời gian và trạng thái. | `/api/employee-requests/overtime*`, ESS Requests | Đã triển khai |
| Employee Request | HR review | HR lọc queue, approve hoặc reject; reject cần reason; quyết định được audit. | `/api/admin/employee-requests*`, UI admin requests | Đã triển khai |
| Payslip | HR Payslip CRUD | HR list theo filter, tạo draft, xem, sửa draft, publish và xóa draft; Payslip là bảng kê theo kỳ, không phải payroll calculation engine. | `/api/admin/payslips*`, UI Payroll | Đã triển khai |
| Payslip | Employee Payslip | Employee active chỉ list/xem Payslip đã publish của chính mình; draft/unpublished không lộ ra. | `/api/payslips/me*`, ESS Payslips | Đã triển khai |
| Payroll | Config/allowance/tax | Các trang cấu hình lương, phụ cấp, thuế TNCN trả 404 qua `notFound()` (`46199ec` gỡ placeholder, `f0a1d07` localize terminology); chưa có engine tính payroll trong backend. | `/payroll/config`, `/allowances`, `/tax` | Chưa triển khai |
| HR Assistant | Hội thoại HR | HR dùng chat để đọc dữ liệu recruitment/onboarding và tạo draft email; tool registry có 8 Read-Tool + 2 Draft-Tool, không có write-tool cho LLM. | `/api/assistant`, UI admin Assistant | Đã triển khai |
| HR Assistant | Human-in-the-loop | Draft Action có action type, params, preview, provenance và confirm endpoint; HR review/confirm, frontend gọi write endpoint thật, không gọi write qua LLM. | Assistant service + DraftActionCard | Đã triển khai |
| HR Assistant | Context & quality | Context Block Builder inject context động (`59f685c`); quality metrics + safe config (`3aaaf29`); migr `075` tạo 3 bảng assistant quality. | `assistant/application/context_builder.py`, `infrastructure/quality_models.py` | Đã triển khai |
| Employee Assistant | Hội thoại Employee | Chỉ Employee active truy cập; employee_id lấy từ session, không nhận từ LLM; đọc dữ liệu cá nhân và draft request thuộc chính Employee; có chat/feedback/session-start/session-end. | `/api/ess/assistant/*`, ESS Assistant | Đã triển khai |
| Runtime | Health/worker heartbeat | Runtime endpoint và Redis heartbeat theo dõi API/Gmail worker/Onboarding worker; admin xem capability health. | `/api/runtime/health`, admin runtime panel | Đã triển khai |
| Frontend | Shell và navigation | Có dashboard HR, ESS layout riêng, navigation theo nhóm Nhân sự/Tuyển dụng/Chấm công/Lương/Hệ thống, responsive/mobile components; header dark mode + breadcrumb + hover (#253). | `frontend/src/app`, `components` | Đã triển khai |
| Frontend | Design system | Inter font + palette "Warm Professional" (đỏ + amber + xanh, radius 6px) + Motion LazyMotion/AutoAnimate; 9 Playwright visual snapshot test. | `globals.css`, `layout.tsx`, `visual-snapshot.spec.ts` | Đã triển khai |

## 4. Logic luồng hoạt động chính

### 4.1. First-Run Setup và đăng nhập

Đây là cánh cửa duy nhất của deployment mới, khớp `docs/setup-flow-redesign.md` và ADR-0001.

| Bước | Actor | Xử lý | Kết quả |
|---:|---|---|---|
| 1 | Browser | Gọi `GET /api/auth/setup-status` (anonymous) | Biết deployment đã có HR hay chưa; thất bại → màn "Không khả dụng" + "Thử lại" |
| 2 | HR đầu tiên | Wizard 3 bước: (1) organizationName, (2) name/email/password(≥12)/password_confirmation, (3) xem lại | Validate client bằng zod; giữ dữ liệu không nhạy cảm khi quay lại/refresh không persist mật khẩu |
| 3 | Backend | `POST /api/auth/setup` tạo Organization + HR trong transaction nguyên tử (`auth_service.setup_first_run` commit cả hai trước khi cấp session) | Không có trạng thái setup dở dang |
| 4 | Backend | Phát hành access/refresh cookie | HR vào dashboard mà không cần login lần hai |
| 5 | HR | Có thể cấu hình domain, OAuth, AI và Google connection sau đó | Setup tối thiểu tách khỏi integration cấu hình |

Xử lý concurrent setup: chỉ một request thành công, các request còn lại nhận lỗi ổn định `AUTH_SETUP_ALREADY_COMPLETED` và không tạo thêm record.

### 4.2. Backbone tuyển dụng

```text
Email đến
  → Organization Google Connection / Gmail ingestion (ARQ cron worker, cursor org-scoped)
  → AI Automation phân loại intent
  → Job Application hoặc Recruitment Inbox cần review
  → HR correction/link/split/dismiss hoặc promote
  → Candidate
  → HR reviewing và assignment vào Job Opening (nếu có)
  → Tạo Interview / gửi invitation sau khi HR xác nhận (bắt buộc selected Calendar)
  → HR tường minh chuyển Candidate pipeline
  → accepted / rejected / archived
  → accepted event
  → OnboardingProcess + Employee inactive
  → hoàn tất checklist
  → Employee active + Employee Account
  → Employee Self-Service
```

Các invariant quan trọng:

1. `job_application` không đồng nghĩa Candidate. AI có thể tạo Job Application nhưng chỉ HR promote Candidate.
2. Candidate có tối đa một Job Opening assignment tại một thời điểm; Job Opening phải `open` cho assignment mới.
3. Tạo/hoàn tất Interview không tự động đổi Candidate pipeline.
4. Candidate `accepted` được commit trước, sau đó event `candidate_accepted` được enqueue; consumer onboarding idempotent và retry ≤3.
5. Employee bắt đầu `inactive`; chỉ khi task cuối của onboarding hoàn tất mới thành `active`.
6. Chỉ Employee active nhận Employee Account và truy cập ESS.

### 4.3. Gmail và AI Automation

| Bước | Xử lý | Boundary an toàn |
|---:|---|---|
| 1 | Worker kiểm tra Organization Google Connection ở trạng thái connected | Không có connection thì thoát sạch, không poll |
| 2 | Poll incremental theo cursor/history (org-scoped); historical import là job riêng | Idempotency theo Gmail message/thread và checksum attachment |
| 3 | Lưu metadata tối thiểu, đưa nội dung cần phân loại vào pipeline | Không coi Gmail label là processing state của Vroom |
| 4 | AI trả intent + structured draft/provenance | Provider lỗi giữ item ở trạng thái chờ/review, không làm mất email |
| 5 | Intent chắc chắn đi tiếp; intent mơ hồ vào Recruitment Inbox | Không tạo Candidate tự động từ tín hiệu không đủ chắc chắn |
| 6 | HR correction/review/promote | Correction được audit và dùng cho evaluation |

### 4.4. Interview và Calendar

1. HR nhập round, khung giờ, timezone, mode, interviewer và external attendee.
2. Backend kiểm tra Organization connection, email attendee, calendar đã chọn (bắt buộc) và conflict metadata.
3. Calendar event được tạo/cập nhật/hủy với idempotency/ETag theo contract.
4. Interview lưu lịch sử riêng; reschedule giữ record, replacement tạo record mới sau khi record cũ cancelled.
5. Calendar RSVP hoặc thay đổi event chỉ tạo thông tin/cảnh báo; không tự hủy Interview và không tự đổi Candidate pipeline.
6. Nếu Google trả conflict `410` (sync token hết hạn) hoặc `412` (ETag), hệ thống yêu cầu xử lý conflict/bounded full sync thay vì âm thầm ghi đè (GH #216).

### 4.5. Onboarding và vòng đời Employee

1. `accept_candidate` cập nhật Candidate và publish `candidate_accepted`.
2. Onboarding worker validate payload; event hỏng được audit và không gọi service.
3. Event hợp lệ gọi `start_from_event`, tạo idempotent Employee inactive + process + task checklist.
4. HR cập nhật task `pending/done`.
5. Task cuối hoàn tất → process complete + Employee active trong một transaction.
6. HR tạo Employee Account sau khi Employee active.
7. Employee đăng nhập ESS để xem hồ sơ/tài liệu/chấm công/request/Payslip và dùng Employee Assistant.

### 4.6. Employee Request, Attendance và Payslip

| Luồng | Employee | HR | Trạng thái dữ liệu |
|---|---|---|---|
| Nghỉ phép/tăng ca | Tạo, xem, hủy request của chính mình | Xem queue, approve/reject; reject cần lý do | Request chờ review trước khi có hiệu lực |
| Chấm công | Check-in/check-out, xem hôm nay/lịch sử | Xem toàn bộ record, correction có reason/audit | Attendance Record tách khỏi leave/overtime/Payslip |
| Payslip | Chỉ xem Payslip đã publish của chính mình | Tạo/sửa draft, publish, xóa draft | Draft không lộ qua ESS |

### 4.7. AI Assistant và Draft Action

```text
HR/Employee gửi chat
  → Assistant xác định scope theo session
  → LLM chỉ được gọi Read-Tool hoặc Draft-Tool
  → trả live data hoặc Draft Action có preview/provenance
  → người dùng review
  → frontend gọi write endpoint thật khi confirm
```

Read-Tool hiện có: `count_candidates_by_status`, `list_interviews_for_candidate`, `get_onboarding_task_details`, `list_in_progress_onboarding`, `search_candidates`, `get_candidate_parsed_cv`, `list_job_openings`, `get_department_info`.
Draft-Tool hiện có: `draft_interview_invitation`, `draft_congratulations_email`.

AI autonomous có khả năng tự ghi database **không thuộc phạm vi hiện tại**.

## 5. Bảng route/API theo module

| Module | Prefix/API chính | Trách nhiệm |
|---|---|---|
| Identity | `/api/auth/*` | setup, login, session, Google connection, calendars, selected-calendar |
| Admin | `/api/admin/*` | user/role, whitelist, domains, OAuth, AI config, tools, audit, employee-requests, payslips |
| Employee | `/api/employees/*`, `/api/departments/*`, `/api/positions/*`, `/api/documents/*` | hồ sơ, tổ chức, account, import, tài liệu |
| Gmail | `/api/gmail/*`, `/api/outbound-emails/*` | sync/import/message/attachment/classification/send |
| Recruitment Inbox | `/api/recruitment/inbox/*` | review, correction, dismiss, split, link proposals |
| Job Application | `/api/recruitment/job-applications/*` | list/detail/promotion và application actions |
| Candidate | `/api/recruitment/candidates/*` | pipeline, CV, Interview, accept/reject/archive, assignment |
| Job Opening | `/api/recruitment/job-openings/*` | create/list/open/close/cancel/metrics |
| Review/Evaluation | `/api/recruitment/cv-review/*`, `/api/recruitment/evaluation/*` | review queue và evaluation set/sample |
| Calendar conflict | `/api/recruitment/calendar-conflicts/*` | list và resolve conflict |
| Onboarding | `/api/onboarding/*` | count/list/detail/task completion |
| Attendance | `/api/attendance/*` | network allowlist (get/put/add/delete), Employee check-in/out/today/history, HR records/correction |
| Employee Request | `/api/employee-requests/*`, `/api/admin/employee-requests/*` | request của Employee và HR review |
| Payslip | `/api/admin/payslips/*`, `/api/payslips/me/*` | HR Payslip và Employee read-only |
| HR Assistant | `/api/assistant/*` | chat và record draft decision |
| Employee Assistant | `/api/ess/assistant/*` | scoped Employee chat/feedback/session |
| Runtime | `/api/runtime/health` | health và worker heartbeat |

## 6. Trạng thái frontend

| Khu vực UI | Trang/khả năng | Trạng thái |
|---|---|---|
| Auth | `/setup` (3-step wizard), `/login`, `/change-password` | Có flow tương ứng |
| HR dashboard | dashboard, header navigation (dark mode + breadcrumb + hover), sidebar, mobile navigation | Có |
| Recruitment | pipeline, inbox, detail, review, job openings, metrics, interview dialogs, conflict manager | Có |
| Gmail | connection, sync, historical import, list/detail, attachment, classification, compose | Có |
| Organization/Admin | AI settings, OAuth, users, whitelist, domains, audit, assistant, assistant-tools, runtime health | Có |
| Employee | list/detail/edit/new/import/documents/departments/positions | Có |
| Onboarding | process list, counts, detail, checklist update | Có |
| Attendance (chính) | HR records và correction, network allowlist | Có |
| Attendance (phụ) | schedules, holidays, leave, overtime | Đã gỡ (page.tsx xóa, nav trim) |
| Payslip | HR list/detail/new/publish; ESS list/detail | Có |
| Payroll (phụ) | config, allowances, tax | Trả 404 (`notFound()`) |
| ESS | dashboard, profile, documents, attendance, requests, Payslips, Employee Assistant | Có |

## 7. Khoảng trống và rủi ro cần theo dõi

| Vấn đề | Bằng chứng hiện tại | Tác động | Hướng xử lý đề xuất |
|---|---|---|---|
| `DESIGN.md` lệch code | `DESIGN.md` ghi Heritage/Fraunces/terracotta nhưng code (`ba7682b`) dùng Inter + "Warm Professional" | AI/đọc docs hiểu sai design system | Cập nhật `DESIGN.md` hoặc ghi ADR design mới |
| Tài liệu domain bị lệch thời điểm | `CONTEXT.md` mô tả Onboarding là mắt xích còn thiếu, nhưng code đã có publisher, worker, process và activation | Sai lệch giữa glossary và code | Cập nhật phần trạng thái, giữ nguyên thuật ngữ domain |
| Payroll chưa là payroll engine | Payslip CRUD/publish có; config/allowance/tax trả 404, không có calculation engine | Kỳ vọng sai về payroll | Chốt roadmap: chỉ Payslip hay có thêm calculation engine, cấu hình, thuế và phụ cấp |
| Attendance UI phụ đã gỡ | Backend check-in/check-out/correction có; 4 trang phụ đã xóa khỏi UI | HR không thao tác schedule/holiday/leave/overtime từ HR UI (leave/overtime có ở module Employee Request) | Build UI khi sẵn sàng hoặc giữ gỡ để tránh quảng bá tính năng chưa có |
| Snapshot có thể cũ | Báo cáo tĩnh không tự cập nhật | Tình hình sau commit mới có thể thay đổi | Tạo lại báo cáo theo ngày hoặc chuyển sang lệnh sinh báo cáo live |
| Smoke test E2E chưa chạy trên deployment thật | Chưa verify end-to-end First-Run Setup → Employee active trên Postgres/Redis/MinIO/Google sandbox | Rủi ro vận hành chưa được phát hiện | Chạy smoke test đầy đủ |

## 8. Tiêu chí để gọi là production-ready

- Chạy đầy đủ migration/rollback và test idempotency cho Gmail, outbound email, Interview, onboarding.
- Xác minh secret không xuất hiện trong response/log/telemetry/backup debug.
- Chốt phạm vi payroll: chỉ Payslip hay có thêm calculation engine, cấu hình, thuế và phụ cấp.
- Cập nhật `README.md`/`CONTEXT.md`/`DESIGN.md` để phản ánh code hiện tại.
- Smoke test end-to-end từ First-Run Setup đến Employee active trên deployment có Postgres/Redis/MinIO/Google sandbox.
- Đo chất lượng vận hành AI Automation (recall/precision theo Evaluation Set) trước khi bật policy preset high-recall.

## 9. Migration mới kể từ snapshot 2026-07-14

| Revision | Nội dung |
|---|---|
| `071` | Organization-scoped Gmail cursor |
| `072` | Add `interview_calendar_id` |
| `073` | Add `calendar_id` to sync cursors |
| `074` | Backfill Candidate calendar fields vào Interview và drop legacy columns (GH #215) |
| `075` | Tạo 3 bảng assistant quality |

## 10. Tài liệu tham chiếu

- [`CONTEXT.md`](../CONTEXT.md) — glossary và boundary domain.
- [`README.md`](../README.md) — tech stack và quick start hiện tại.
- [`DESIGN.md`](../DESIGN.md) — design system (cần cập nhật).
- [`docs/setup-flow-redesign.md`](setup-flow-redesign.md) — spec First-Run Setup.
- [`docs/adr/0001-atomic-first-run-setup.md`](adr/0001-atomic-first-run-setup.md)
- [`docs/adr/0002-organization-google-workspace-integration.md`](adr/0002-organization-google-workspace-integration.md)
- [`docs/adr/0003-organization-ai-configuration.md`](adr/0003-organization-ai-configuration.md)
- [`docs/adr/0004-job-application-classification-boundary.md`](adr/0004-job-application-classification-boundary.md)
- [`docs/adr/0005-ai-optimization-guardrails.md`](adr/0005-ai-optimization-guardrails.md)
- [`docs/project-status-2026-07-14.md`](project-status-2026-07-14.md) — snapshot trước (đã cũ).
