# Security / Privacy Docs — Vroom HR

Mục tiêu: chốt nguyên tắc bảo mật, privacy, quyền truy cập, và xử lý PII cho Vroom HR. Hệ thống là self-hosted, one deployment per company.

## 1. Phạm vi

### In scope

- auth model
- role / permission matrix
- PII handling
- secret management
- data access scope
- retention / delete policy
- audit requirements
- backup / recovery

### Out of scope

- public multi-tenant SaaS isolation
- consumer social auth features
- employee-facing policy
- payroll-specific compliance beyond stored HR data

## 2. Security principles

- least privilege
- deny by default
- human confirmation required before write actions
- audit-first
- self-host by design
- no shared deployment across companies

## 3. Identity and auth model

### 3.1 Organization boundary

One deployment serves exactly one Organization. No cross-company data access exists by design.

### 3.2 Auth

- server-managed session via httpOnly secure cookie
- SameSite=Lax/Strict
- CSRF protection trên write endpoints
- refresh token rotation
- session expiry handled server-side

### 3.3 User roles

MVP: single `HR` role.

Future extension:

- HR Admin: quản lý template, export, retention setting
- HR Member: xử lý onboarding case

### 3.4 System / AI

System và AI không có user identity. AI access được guard bởi tool set, không phải DB role.

## 4. Permission model

### 4.1 Default rule

Deny unless explicitly allowed.

### 4.2 Access scope

HR can access:

- Candidate records in scope
- OnboardingCase records
- DocumentItem records
- ContractDraft records
- OnboardingTask records
- TimelineItem records
- Reminder records
- AuditLog records

### 4.3 Write scope

All write actions require HR confirmation.
AI can never write directly.

## 5. PII handling

### 5.1 PII examples

- full name
- email
- phone
- address
- ID number
- contract content
- CV content
- document images
- extracted fields

### 5.2 Rules

- store only data needed for onboarding
- avoid duplicate PII copies unless necessary for preview/extraction
- redact sensitive fields in UI: ID numbers che một phần mặc định
- keep extracted suggestions separate from confirmed entity data
- do not expose raw PII in logs
- encrypt PII at rest where possible
- use TLS for all traffic
- restrict database backup access

### 5.3 Encryption

- data at rest encrypted where feasible
- object storage files encrypted server-side
- TLS enforced for all client-server traffic
- database backup files restricted to admin/operator only

### 5.4 Document storage

- uploaded files stored in object storage
- access only through authenticated application path
- signed/temporary URL only when needed
- never expose direct public bucket access

## 6. Secret management

- app secrets stored outside repo
- no credentials in markdown, logs, or client-side bundle
- AI provider keys, DB creds, mail creds, storage creds kept server-side only
- rotate secrets when exposed or when provider changes

## 7. Audit and logging

### 7.1 Audit requirements

All important actions must be auditable:

- create/update/confirm/cancel onboarding data
- upload/review/reject documents
- create/update contract drafts
- create/update tasks
- confirm AI drafts
- apply extracted suggestions

### 7.2 Audit content

Audit log should capture:

- actor
- action
- object
- timestamp
- source: manual / ai_suggestion / system
- correlation_id when one AI action produces multiple changes
- before/after when relevant — redacted for sensitive fields (ghi "field changed" thay vì raw value)

### 7.3 Logging rules — PII-safe

Application logs must never contain:

- CV text or parsed CV content
- contract body or draft text
- document OCR result
- ID numbers (CCCD, tax code, passport)
- raw AI prompt/response containing PII
- secrets or auth tokens

Mọi log phải dùng structured format, cho phép filter field nhạy cảm.

### 7.4 Sensitive audit diff

Với sensitive fields (ID number, contract content), audit không lưu `before/after` đầy đủ.
Chỉ lưu `field_name: changed` hoặc `field_name: [redacted diff]`.

### 7.5 Audit export

Audit export được phép với HR Admin. Export phải được ghi audit.

## 8. AI privacy boundary

### 8.1 Data access

- AI tools receive minimum data needed for task
- use read tools, not raw unrestricted DB dumps
- extracted suggestions remain separate until HR applies them
- AI draft content is editable before confirm

### 8.2 Provider mode

AI provider must be configurable:

- local / self-hosted model preferred for sensitive deployments
- external provider allowed only if company policy permits
- prompts/responses containing PII should not be retained beyond provider policy
- company must be able to switch provider without data migration

### 8.3 Training

No training on customer data unless explicitly enabled by deployment policy.
Default: off.

## 9. Retention and deletion

### 9.1 Retention categories

Không gom chung. Mỗi loại có vòng đời riêng.

| Data type | Default retention | Policy |
| --- | --- | --- |
| Documents / files | Per company policy | System default cho demo: 12 months |
| Candidate metadata | Per company policy | Anchor to onboarding complete date |
| AuditLog | Per company policy | System default: 24 months |
| AI draft (confirmed) | Per company policy | Draft không confirm có thể xoá sau N ngày |
| AI draft (unconfirmed) | 7 days | Tự động clean |

### 9.2 Deletion / anonymization

When deletion is required:

- remove or anonymize PII where possible
- preserve audit trail metadata only — redact or remove sensitive content
- do not leave orphaned file references
- file deletion should cascade to storage

### 9.3 Export

HR data export should be explicit and authenticated.
Export scope: per-case or per-period.

## 10. Backup & recovery

- encrypted backups
- access restricted to admin / operator
- restore process must preserve audit integrity
- backup test restore at least once per phase

## 11. Incident / abuse response

If data exposure or misuse is suspected:

- disable affected tokens / creds immediately
- review audit logs
- rotate secrets
- review file access and recent writes
- document incident in internal ops notes
- notify company admin

## 12. Open questions

Đã trả lời:

- Retention: company policy, system default cho demo
- Redact ID number: có, che một phần mặc định
- Audit export: có, HR Admin
- AI draft storage: MVP store khi HR confirm hoặc save draft, preview tạm không lưu

Còn mở:

1. CSRF token nên dùng custom token hay built-in framework (FastAPI CSRF middleware / double-submit cookie)?
2. AI provider config cần UI hay chỉ env var?
3. Backup schedule nên daily hay được HR Admin trigger on-demand?

## 13. Next step

After review, update checklist → UX flow / screen map.
