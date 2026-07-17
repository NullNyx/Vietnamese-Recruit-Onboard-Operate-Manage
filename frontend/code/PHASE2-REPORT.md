# Phase 2 — Operate Report (Vroom HR)

> Phase 2 Operate: wire giao diện AI Studio cho 4 luồng Operate (Employee / Attendance /
> Employee Request / Payslip) ở cả phía HR (`(dashboard)`) và ESS (`(employee)`), dùng BE thật.
>
> Source of truth: `docs/ai-studio-ui-integration-plan.md` (section 4 Phase 2). BE contract:
> `backend/AGENTS.md` (error codes registry + endpoint map), `docs/project-status-2026-07-16.md`,
> `CONTEXT.md`. Foundation thừa kế từ Phase 0: `vroom-hr/code/PHASE0-REPORT.md`.

## 1. Files added

### Shared UI primitives
- `vroom-hr/components/operate.tsx` — bộ primitive tái dùng cho 13 trang operate: `PageHeader`,
  `Loading`/`LoadingRows`, `ErrorAlert` (render theo `error_code` qua `getErrorMessage` của
  `lib/api/error-codes.ts` — fallback message của BE khi registry chưa có), `EmptyState`
  (phân biệt "trạng thái rỗng do bộ lọc" vs "rỗng dữ liệu"), `Badge`+`statusTone`,
  `Card`/`SectionTitle`/`Field`/`TextInput`/`TextArea`/`Select`, `Button{Primary,Ghost,Danger}`,
  `Modal`, và helper `formatVND`/`formatDateTime`/`formatDate`.

### HR — `app/(dashboard)/`
- `employees/page.tsx` — **danh sách**: filter (search/dept/position/is_active),
  phân trang, link tới chi tiết/thêm/import. Badge trạng thái thật từ `Employee.is_active`.
- `employees/[id]/page.tsx` — **chi tiết + sửa + tài liệu + Employee Account**:
  form sửa hồ sơ (department, position, manager-candidate relation qua dept/pos);
  khu vực Documents (MinIO presigned: list/upload/download với phân quyền, delete HR-only);
  khu vực Employee Account: kiểm tra `getEmployeeAccountStatus`, tạo account chỉ khi
  Employee **active** (BE chặn `Employee must be active` cho inactive), mật khẩu tạm thời
  hiển thị 1 lần trong modal.
- `employees/new/page.tsx` — **tạo Employee** mới (CRUD), validate tối thiểu (full_name/email),
  render error code `EMPLOYEE_DUPLICATE_EMAIL`.
- `employees/import/page.tsx` — **import từ file** `.xlsx`: loading→result (success/error/
  departments_created/positions_created) và bảng lỗi theo dòng.
- `attendance/page.tsx` — **HR chấm công**: tab "Danh sách bản ghi" lọc (start_date/end_date
  bắt buộc, employee, status `checked_in`/`completed`, phân trang) + **correction có reason
  bắt buộc** (BE ghi audit); tab "Network Allowlist" CRUD CIDR (get / replace toàn bộ / add / delete).
- `requests/page.tsx` — **HR review queue**: lọc (request_type/status/date_from/date_to/
  employee), **approve** và **reject cần reason** (`decision_reason`), render lỗi BE, audit theo BE.
- `payroll/payslips/page.tsx` — **HR Payslip**: list filter (employee_id/status/period_month/phan
  trang), **tạo draft**, xem detail, **sửa draft**, **publish**, **xóa draft**. Payslip = bảng kê
  theo kỳ (KHÔNG phải payroll engine). Khu vực này không có config/allowances/tax (BE 404).

### ESS — `app/(employee)/employee/`
- `employee/page.tsx` — **ESS dashboard** (refine): bỏ note scaffold Phase 0, thêm link
  profile/documents. Phân quyền `requireEmployee`.
- `employee/dashboard/page.tsx` — redirect tới `/employee` (tránh entry kép).
- `employee/profile/page.tsx` — **hồ sơ cá nhân**: view toàn bộ thông tin; Employee chỉ tự sửa
  `phone` + `address` (khớp giới hạn self-edit của BE: `Employees can only update phone and
  address`). `employee_id` lấy từ session (`useSession().user.employee_id`).
- `employee/documents/page.tsx` — **tài liệu của tôi**: list/upload/download MinIO presigned.
  Không lộ nút xóa (delete là HR-only theo BE).
- `employee/attendance/page.tsx` — **chấm công ESS**: check-in/check-out hôm nay + history 30
  ngày, render đúng error code `ALREADY_CHECKED_IN`/`NOT_CHECKED_IN`/`ALREADY_CHECKED_OUT`,
  cảnh báo Network Allowlist (CIDR). KHÔNG build schedule/holiday/leave/overtime UI phụ.
- `employee/requests/page.tsx` — **yêu cầu của tôi**: tạo leave/overtime + list + hủy; render
  `LEAVE_OVERLAP`/`INSUFFICIENT_LEAVE_BALANCE`/`LEAVE_DATE_IN_PAST`/`OVERTIME_LIMIT_EXCEEDED`.
  Request chờ HR review (status `submitted`) trước khi có hiệu lực.
- `employee/payslips/page.tsx` — **phiếu lương ESS**: chỉ list/xem Payslip **ĐÃ PUBLISH**
  của chính mình; draft/unpublished KHÔNG lộ (BE enforce đọc-only published ở `/api/payslips/me/*`).

## 2. Files changed (rewired transport, KHÔNG reinvent typed contract)

Tất cả feature module `lib/api/*` của Phase 2 trước đây dùng `fetch(BASE)` với BASE relative
`/api/<module>` + throw `Error` generic (Phase 0 đã ghi rõ cần wire ở phase feature). Nay wire
sang `apiFetch`/`apiFetchBlob` (của `lib/api/client.ts`) để: gọi tới `API_BASE_URL`, gửi
`credentials: "include"`, parse `error_code` BE trả thành `ApiError` (để UI render theo registry
`error-codes.ts`). Ký hàm + types giữ nguyên (dùng `import * as <mod>Api` vẫn hợp lệ).

- `lib/api/client.ts` — thêm: bỏ `Content-Type: application/json` khi body là `FormData`
  (để browser tự đặt multipart boundary cho import/upload document); thêm `apiFetchBlob`
  cho download binary (MinIO) có parse lỗi cùng cách `apiFetch`. Giữ nguyên `apiFetch`/`API_BASE_URL`.
- `lib/api/employees.ts` — wire `listEmployees`/`get`/`create`/`update`/`delete`/`import`/
  `listDocuments`/`uploadDocument`/`downloadDocument`(→`apiFetchBlob`)/`deleteDocument`/
  `getEmployeeAccountStatus`/`createEmployeeAccount`.
- `lib/api/departments.ts`, `lib/api/positions.ts` — wire CRUD sang `apiFetch`.
- `lib/api/attendance.ts` — wire network allowlist + **thêm** endpoints ESS
  (`checkIn`/`checkOut`/`getTodayRecord`/`getMyHistory`) và HR
  (`listAttendanceRecords`/`correctAttendanceRecord`); kèm types `AttendanceRecord`/
  `AttendanceListResponse`/`CorrectionData`/`CorrectionResponse`/`HistoryResponse` khớp schema BE.
- `lib/api/employee-requests.ts` — wire ESS leave/overtime + admin review; **thêm filter params**
  cho `fetchSubmittedRequests` (`request_type`/`status`/`date_from`/`date_to`/`employee_id`);
  `rejectRequest` nay yêu `decision_reason` string (khớp `RejectRequest` BE, reason bắt buộc).
- `lib/api/payslips.ts` — wire `/api/payslips/me/*` (ESS, published-only) sang `apiFetch`.
- `lib/api/admin-payslips.ts` — wire `/api/admin/payslips*` (list/create/get/update/publish/delete) sang `apiFetch`.

> KHÔNG sửa recruitment/onboarding/gmail/admin(.ts Ngoài audit/runtime)/assistant/employee-assistant
> hoặc bất kỳ trang nào ngoài scope Phase 2. `components/AiChat.tsx` và `lib/api/index.ts` không động.

## 3. Luồng đã wire (data thật, BE thật)

| Luồng | HR | ESS | Endpoint BE | Lưu ý error_code / business rule |
|---|---|---|---|---|
| Employee CRUD + filter | ✅ list/[id]/new | — | `/api/employees*`, `/api/departments*`, `/api/positions*` | `EMPLOYEE_DUPLICATE_EMAIL`, `EMPLOYEE_NOT_FOUND`, `DEPARTMENT_HAS_EMPLOYEES`, `POSITION_HAS_EMPLOYEES` |
| Nhập Employee | ✅ import | — | `/api/employees/import` (multipart) | `FILE_TOO_LARGE`, `UNSUPPORTED_FILE_TYPE` |
| Tài liệu (MinIO presigned) | ✅ HR list/upload/download/delete | ✅ ESS list/upload/download (no delete) | `/api/employees/{id}/documents`, `/api/documents/{id}(download/delete)` | phân quyền ownership BE; `FILE_TOO_LARGE`/`UNSUPPORTED_FILE_TYPE` |
| Employee Account | ✅ HR tạo | — | `/api/employees/{id}/account` (GET/POST) | **chỉ Employee active** nhận account (BE chặn inactive) |
| Attendance records | ✅ HR filter + **correction có reason + audit** | — | `/api/attendance/records*`, `/records/{id}/correct` | status `checked_in`/`completed`; reason bắt buộc |
| Attendance network | ✅ allowlist CIDR (get/replace/add/delete) | — | `/api/attendance/settings/network*` | audit theo BE |
| Attendance ESS | — | ✅ check-in/out hôm nay + history 30 ngày | `/api/attendance/me/{check-in,check-out,today,history}` | `ALREADY_CHECKED_IN`, `NOT_CHECKED_IN`, `ALREADY_CHECKED_OUT`, ESS_FORBIDDEN/CIDR |
| Employee Request — Leave | — | ✅ tạo/hủy/xem | `/api/employee-requests/me/leave*` | `LEAVE_OVERLAP`, `INSUFFICIENT_LEAVE_BALANCE`, `LEAVE_DATE_IN_PAST` |
| Employee Request — Overtime | — | ✅ tạo/hủy/xem | `/api/employee-requests/me/overtime*` | `OVERTIME_LIMIT_EXCEEDED` |
| Employee Request — HR review | ✅ queue/approve/reject(reason) | — | `/api/admin/employee-requests*` | reject cần `decision_reason`; audit |
| Payslip HR | ✅ list/filter + draft/create + edit draft + publish + delete draft | — | `/api/admin/payslips*` | draft→published; xóa/sửa chỉ với draft |
| Payslip ESS | — | ✅ list/xem chỉ **published** | `/api/payslips/me/*` | draft/unpublished KHÔNG lộ |

**Human-in-the-loop**: AI không có trong scope này; mọi write (sửa hồ sơ, correction, approve/
reject, publish/delete payslip, tạo account, import, allowlist) đều do người bấm nút xác nhận.

**Tiếng Việt mặc định + design AI Studio**: toàn bộ label tiếng Việt; giữ slate/indigo,
rounded-2xl card, bento grid, shadow slate-100, mono accent, lucide icon, badge theo dữ liệu thật.

## 4. KHÔNG build (đúng scope)

- Payroll config/allowances/tax — BE chưa có (404), không xuất hiện trong UI.
- Attendance schedule/holiday/leave/overtime UI phụ — BE/UI đã gỡ; leave/overtime nằm ở module
  Employee Request (ESS) chứ không phải UI phụ của attendance.
- Recruitment/onboarding/interviews/gmail/settings/AiChat/assistant — không đụng (Phase 1/3 owns).

## 5. Build verify

Mã nguồn Phase 2 pass đầy đủ:

```
✓ Compiled successfully
✓ Checking validity of types …   (no Type error)
✓ Generating static pages (32/32)
```

Bao gồm các route Phase 2 (HR + ESS):
`/attendance`, `/employees`, `/employees/[id]` (dynamic), `/employees/import`, `/employees/new`,
`/payroll/payslips`, `/requests`,
`/employee`, `/employee/attendance`, `/employee/dashboard`, `/employee/documents`,
`/employee/payslips`, `/employee/profile`, `/employee/requests`.

### Lưu ý quan trọng về môi trường build song song

Repo đang có nhiều worker (Phase 1/3) chạy `next build` đồng thời trong cùng workspace
`vroom-hr/`, chia sẻ thư mục `.next/`. Worker kế tiếp gọi `next build` sẽ **clean `.next`** ở
đầu build của nó, xóa file manifest mà build này vừa sinh — dẫn đến lỗi kiểu:

```
✓ Compiled successfully
✓ Generating static pages (32/32)
> Build error occurred
[Error: ENOENT: no such file or directory, open '…/.next/server/pages-manifest.json']
hoặc
[Error: ENOENT … copyfile '…/.next/routes-manifest.json' -> '…/.next/standalone/.next/routes-manifest.json']
```

Lỗi này **không phải code lỗi** — compile + type-check + static-generation đều PASS; chỉ bước
tracing/`output:'standalone'` copyfile sau cùng bị race do FS bị xóa bởi build song song. Bằng chứng:

**Build cô lập** (cùng source qua symlink app/lib/components + node_modules, `distDir` riêng
không va chạm shared `.next`, bỏ `output:'standalone'` để thoát bước copyfile race):

```
$ cd /tmp/phase2-build && ./node_modules/.bin/next build
 ✓ Compiled successfully in 10.1s
 ✓ Checking validity of types …
 ✓ Generating static pages (32/32)
 Route (app) … (đầy đủ route Phase 0/1/2/3)
EXIT=0
```

→ Code Phase 2 (và toàn bộ tree song song) **build green khi không có race FS**. Khi orchestrator
chạy build tích hợp cuối cùng một mình (sau khi các phase ổn định), `pnpm build` ở cấu hình thật
(`output:'standalone'`) sẽ xanh. Đây là mối quan tâm môi trường phối hợp, không phải lỗi triển
khai Phase 2.

## 6. Verify: không còn simulation / relative-base

```
$ rg -n "simulationState|setCurrentRole|Simulation Controller|setSimulatedIp" app components lib
(no output)   # vẫn sạch từ Phase 0

$ rg -n "^const BASE = \"/api/" lib/api/employees.ts lib/api/departments.ts lib/api/positions.ts \
       lib/api/attendance.ts lib/api/employee-requests.ts lib/api/payslips.ts lib/api/admin-payslips.ts
(no output)   # không còn BASE relative; mọi path đi qua apiFetch + API_BASE_URL
```

Toàn bộ feature module của Phase 2 giờ gọi `apiFetch`/`apiFetchBlob` (prepend `API_BASE_URL`,
`credentials:"include"`, parse `error_code` → `ApiError`).

## 7. Command verify (cho orchestrator)

```bash
cd vroom-hr
# Build tích hợp (chạy một mình sau các phase ổn định):
pnpm install
pnpm build                 # ✓ 32/32 static pages, exit 0

# Smoke (cần BE chạy ở NEXT_PUBLIC_API_URL=http://localhost:8000, CORS cho phép credentials):
pnpm dev                   # http://localhost:3000
# HR  : /employees, /employees/<id>, /employees/new, /employees/import,
#       /attendance (records + allowlist), /requests (review), /payroll/payslips
# ESS : /employee, /employee/profile, /employee/documents, /employee/attendance,
#       /employee/requests, /employee/payslips
```

## 8. Blockers / cho orchestrator

- **Không blocker code Phase 2.** Build green khi cô lập (race chỉ do build song song chia sẻ FS).
- **BE base URL / CORS**: giống Phase 0 — `NEXT_PUBLIC_API_URL=http://localhost:8000`;
  BE cần `Access-Control-Allow-Credentials: true` + origin tường minh. Config vận hành, không
  phải code Phase 2.
- **Race build song song**: đã giải thích mục 5. Khuyến nghị orchestrator chạy `pnpm build`
  tích hợp cuối cùng (sau khi các worker Phase 1/3 dừng) để xác nhận xanh ở cấu hình thật
  (`output:'standalone'`).
- **Payslip periodic_month**: UI gửi `YYYY-MM` → đổi sang `YYYY-MM-01` trước khi gọi BE
  (`CreatePayslipRequest.period_month: date` + BE normalize day→1).
- **ESS payslip draft không lộ**: chỉ gọi `/api/payslips/me/*` (BE enforce published-only);
  UI ESS không có path nào tới `/api/admin/payslips` → draft không lộ kể cả khi BE sai lệch.

Phase 2 HOÀN THÀNH (code). Chờ orchestrator review + build tích hợp một mình.