# Employee Record & Contract Documents — Slice Design

Mục tiêu: xây dựng Employee Record làm module lõi, và Contract & Employment Documents làm slice đầu.

## 1. Nguyên tắc

- HR/Admin là actor duy nhất.
- Employee Record là source of truth cho mọi nghiệp vụ nhân sự.
- Không có employee-facing actor, không employee login, không self-service.
- Mọi write action đều qua HR/Admin.
- Audit bắt buộc cho mọi thay đổi.
- Template (hợp đồng) là điểm mở rộng.

## 2. Phạm vi

### In scope

- Employee Profile: tạo, cập nhật, xem lịch sử thay đổi
- Document management: upload CCCD, bằng cấp, giấy tờ; verify/reject; theo dõi hết hạn
- Contract management: tạo draft từ template, review, export, gia hạn, chấm dứt
- Contract Amendment: phụ lục hợp đồng
- Employment Events: ghi nhận mọi thay đổi hồ sơ
- Audit log cho mọi write action
- AI hỗ trợ điền template, tóm tắt hồ sơ (nếu implement Assistant)

### Out of scope

- Employee self-service / portal
- Employee login
- Payroll
- Attendance / leave
- Performance review / training
- Onboarding (recruitment slice riêng)
- Offboarding (sẽ xây sau)

## 3. Actor

| Actor | Role |
|-------|------|
| HR/Admin | Tạo, sửa, xoá, xem Employee Record, Document, Contract, Contract Amendment, Employment Event |

## 4. Entity model

### 4.1 Employee

- id
- employee_code unique
- full_name
- email nullable
- phone nullable
- birth_date nullable
- id_number nullable
- personal_tax_code nullable
- employment_status: active / resigned / terminated / suspended
- department
- position
- start_date
- termination_date nullable
- note nullable
- audit fields (created_at, updated_at, created_by, updated_by)

### 4.2 Document

- id
- employee_id
- type: id_card / diploma / insurance / contract_related / other
- file_path
- status: uploaded / verified / rejected / expired
- note nullable
- uploaded_by_hr_id
- verified_by_hr_id nullable
- verified_at nullable
- audit fields

### 4.3 EmploymentEvent

- id
- employee_id
- event_type: profile_update / promotion / transfer / status_change / termination / document_update / contract_update
- before_json nullable
- after_json nullable
- actor_hr_id
- note nullable
- created_at

### 4.4 ContractTemplate

- id
- name
- version
- content
- file_path nullable
- status: active / archived
- audit fields

### 4.5 Contract

- id
- employee_id
- contract_number unique nullable
- template_id nullable
- contract_type: labor / offer / nda / other
- status: draft / pending_signature / active / expired / terminated / cancelled
- signed_on nullable
- started_on
- ended_on nullable
- file_path nullable
- content text
- signed_document_path nullable
- audit fields

### 4.6 ContractAmendment

- id
- contract_id
- name
- content text
- file_path nullable
- signed_document_path nullable
- status: draft / pending_signature / signed / cancelled
- signed_on nullable
- audit fields

## 5. Business rules

- `employee_code` là duy nhất
- `email` nullable (không dùng làm định danh nghiệp vụ)
- Contract `status` lifecycle: draft → pending_signature → active → expired | → terminated | → cancelled
- Không thể tạo ContractAmendment trên contract đã terminated/cancelled
- `before_json` / `after_json` trong EmploymentEvent không lưu raw salary/payroll data nếu chưa có policy
- AI extraction chỉ tạo suggestion, không tự update Document

## 6. Screen map (draft)

### 6.1 Employee List
- Entry: Dashboard / Menu
- Hiển thị danh sách Employee, search, filter (department/status)
- Cột chính: `employee_code`, `full_name`, `department`, `position`, `employment_status`, `start_date`, `contract_status/latest_contract`
- Click → Employee Detail

### 6.2 Employee Detail
- Tabs: Profile / Documents / Contracts / Events
- Profile: xem/sửa thông tin + employment status
- Documents: upload, verify/reject, xem file
- Contracts: danh sách hợp đồng + phụ lục
- Events: timeline thay đổi

### 6.3 Contract Detail
- Trong tab Contracts của Employee Detail
- Hoặc page riêng khi click contract
- Hiển thị nội dung, trạng thái, phụ lục
- Actions: edit draft, upload signed, renew, terminate, export

### 6.4 Template Management (sub-page)
- Danh sách ContractTemplate
- Create / edit / archive

## 7. Audit

Mọi write action ghi AuditLog:
- actor: HR ID
- action: create / update / delete / status_change / verify / upload / sign
- entity_type: employee / document / contract / contract_amendment / contract_template
- entity_id
- before_json / after_json: với PII redacted
- source: manual / ai_suggestion / system
- correlation_id nullable

Những write ảnh hưởng hồ sơ nhân sự ghi thêm EmploymentEvent.

## 8. API error codes

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | duplicate_employee_code | employee_code đã tồn tại |
| 400 | invalid_status_transition | status không hợp lệ |
| 404 | employee_not_found | Không tìm thấy Employee |
| 404 | contract_not_found | Không tìm thấy Contract |
| 409 | contract_already_terminated | Không thể sửa contract đã chấm dứt |
| 413 | file_too_large | File vượt quá giới hạn |
| 415 | unsupported_file_type | File không đúng định dạng |

## 9. Flow rules

### Flow 1: Onboard Employee

```
Employee List → Create Employee → Profile tab → Documents tab → Contracts tab
```

1. HR mở `Employee List` → click `Create Employee`
2. HR điền `employee_code`, `full_name`, `department`, `position`, `employment_status`, `start_date`
3. Submit → Employee created, default status `active`
4. HR vào `Employee Detail`
5. HR sang `Documents tab` → upload CCCD → status `uploaded`
6. HR upload bằng cấp → status `uploaded`
7. HR verify từng document → status `verified`
8. HR sang `Contracts tab` → `Create Contract`
9. HR chọn `ContractTemplate`, điền `contract_number`, `started_on`, `ended_on`, nhập nội dung
10. Submit contract → `draft`
11. HR mark ready / send for signing → `pending_signature`
12. HR upload signed file + `signed_on` → `active`

### Flow 2: Employee Change

```
Employee Detail → Profile tab → Edit → Save
```

1. HR mở `Employee Detail`
2. Tab `Profile` → Edit → đổi `department`, `position`, `note`
3. Submit → save. `EmploymentEvent` ghi `before_json` / `after_json`, `event_type` phù hợp

### Flow 3: Contract Renewal

```
Employee Detail → Contracts tab → Contract Detail → Renew
```

1. HR mở `Contract Detail` của contract đang `active`
2. Click `Renew`
3. Chọn `ContractAmendment` hoặc tạo `Contract` mới
4. HR điền nội dung → submit
5. Nếu amendment → `contract_id` gắn với contract cũ, status `draft`
6. Nếu contract mới → `contract_number` mới, status `draft`

### Flow 4: Employee Exit

```
Employee Detail → Profile tab → Change Status → Save
```

1. HR mở `Employee Detail`
2. Tab `Profile` → `Change Status`
3. HR chọn `resigned` hoặc `terminated`, nhập `termination_date`, `note`
4. Submit → save. `EmploymentEvent` ghi `termination` hoặc `status_change`

Rule:
- `resigned` / `terminated` chặn create contract mới
- cho phép upload document loại `exit` / `offboarding` / `admin-only`
- chặn profile update nghiệp vụ, trừ note và hồ sơ hành chính

### Flow 5: AI Contract Draft

```
Contract Detail → Generate Draft
```

1. HR chọn `ContractTemplate`
2. AI (nếu implement) đọc Employee info → điền template → preview
3. HR review, sửa → confirm
4. Contract tạo với content đã điền, status `draft`
5. `AuditLog` source `ai_suggestion`

Note: flow này là nice-to-have, không ảnh hưởng MVP acceptance nếu chưa làm.

## 10. Next step

Sau review: UI screens detail → data model migration → API routes.
