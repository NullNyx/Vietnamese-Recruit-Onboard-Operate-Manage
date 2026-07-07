# HR Space — Glossary

Bảng thuật ngữ chuẩn. Dùng từ này xuyên suốt spec, code, doc.
Không synonym, không phát minh từ mới khi đã có.
Nguồn: ADR 0021–0029.

## Actor

**HR** là actor duy nhất. Mọi hành động ghi do HR thực hiện.
Employee không login, không self-service, không quyền ghi.
_Avoid_: Employee, Applicant, User làm actor

## Domain

**Organization**:
Công ty sở hữu instance. Chứa cấu hình (tên, mã số thuế, múi giờ).
Single-tenant MVP; `organization_id` pre-placed trên aggregate roots.
_Avoid_: Company, Tenant, Account, Client

**WorkItem**:
Trung tâm vận hành. Một item trong work queue, có lifecycle
từ activation → complete → archive. Không phải "công việc trong module X".
Status: active / in_progress / waiting / completed / reopened / archived.
Source: inbox / system / manual / dependent.
Works through link tables: People, Document, Contract, WorkItem.
_Avoid_: Task, Case, Ticket, Job

**InboxItem**:
Raw input trước triage. Email, file upload, request, system notification.
Chưa phải work item cho tới khi triage. Status: new / triaged / dismissed.
_Avoid_: Inbox message, raw email entity

**People**:
Common identity/contact layer. Type: employee / candidate / contact.
Không chứa type-specific fields.
Employee and Candidate data đi ở profile extension.
_Avoid_: Employee (khi muốn nói về hồ sơ nhân sự), Contact

**EmployeeProfile**:
Extension 1:1 với People khi type = employee.
Chứa department, position, manager, employment_status, started_at, termination_date.
_Avoid_: Employee (dùng People + EmployeeProfile)

**CandidateProfile**:
Extension 1:1 với People khi type = candidate.
Chứa pipeline_status, summary, source_email, job_opening_ref.
_Avoid_: Applicant

**Document**:
Pure library entity cho file / giấy tờ.
Status: uploaded / verified / rejected / expired.
Không sở hữu relationship collections — link qua link tables.
Không lưu AI suggestion (AISuggestion giữ extraction draft).
Chỉ giữ `applied_extracted_data_json` sau HR confirm.
_Avoid_: Attachment

**Contract**:
Hợp đồng lao động, offer, NDA, amendment.
Status: draft / ready / sent / signed / expired / terminated / cancelled.
Contract type constraint: offer → candidate; labor_contract/amendment/termination → employee.
AI điền template draft, không tự ghi Contract.
_Avoid_: Employment contract (quá hẹp)

**Template**:
Mẫu dùng lại. type: contract / document / checklist / task.
Versioned. scope: org_default / position / department.
Tự không sinh work item — Work service làm phần đó.
_Avoid_: Form mẫu, template không rõ loại

## Work Execution Surfaces

**Today**:
Command Center — entry point mặc định. Decision layer giúp HR quyết định
việc nào làm trước. Không phải dashboard, không phải module page.
_Avoid_: Dashboard, Homepage

**All Work**:
Operations Center — toàn bộ work items đang sống. Tra cứu, filter, search, batch action.
Không giới hạn theo ngày.
_Avoid_: Work list page

**Work Detail**:
Execution Screen — nơi xử lý một work item. Chỉ mở khi cần multi-step /
draft / coordinate. Trả lời 3 câu: việc gì, bước tiếp theo, làm sao hoàn thành nhanh.
Không phải "màn xem toàn bộ entity fields".
_Avoid_: Detail page, Form screen, Record view

**Inbox**:
Intake surface — nơi tiếp nhận đầu vào thô, triage, convert thành work item.
Không phải queue xử lý chính.
_Avoid_: Email inbox

**Context Libraries**:
People, Documents, Contracts, Templates — nơi inspect/reference.
Không phải trung tâm vận hành. Work mở sang đây khi cần context.
_Avoid_: Modules, Trang quản lý employee

## Decision Model

**Decision Label**:
Nhãn quyết định trên Today: Critical / Attention / Planned Today / Waiting.
Derived/cache từ signal + rule evaluation, không phải source of truth.

**Priority Order**:
Thứ tự ưu tiên khi tín hiệu xung đột:
1. Blocking others
2. Overdue
3. Legal / compliance risk
4. External person waiting
5. Manager escalation
6. Due today
7. Due soon
8. Recently changed + unresolved
9. Planned today

## Work Taxonomy

**Action Types**:
Thao tác xử lý việc — độc lập domain.
Intake / Review / Draft / Update / Coordinate / Follow-up / Monitor / Answer / Complete.
Mọi Work Type trải qua một subset.

**Work Types**:
Đơn vị việc HR theo dõi trên desk. Không phải module, không phải domain.
W1 Hồ sơ nhân sự, W2 Bộ giấy tờ, W3 Chuẩn bị đi làm (onboarding),
W4 Hợp đồng, W5 Tuyển dụng, W6 Yêu cầu nội bộ, W7 Tác vụ đơn, W8 Hỏi đáp/Báo cáo.
W3 (Chuẩn bị đi làm) là super work type — chứa W2 + W4 + W7.

**Interaction Levels**:
L1 Instant Action — 1 click trên Today.
L2 Inline Action — expand, context ngắn, form nhỏ.
L3 Focused Work — Work Detail, multi-step, draft, coordinate.
L4 Cross-context Work — qua Context Libraries rồi quay lại work.

## AI

**AISuggestion**:
AI output chờ HR confirm. source_entity_type whitelist:
work_item, inbox_item, document, contract, people.
Status: pending / accepted / rejected / superseded.
_Avoid_: AI decision, auto-result, tự ghi

**PromptRun**:
Trace một lần gọi AI. Chỉ lưu sanitized_prompt / sanitized_response.
Raw payload opt-in, restricted, redacted.
_Avoid_: Raw log mặc định

**AIJob**:
AI job nền. Job type: classification / extraction / batch_draft / daily_summary.
Status: queued / running / completed / failed.

**AI Capabilities**:
classify, extract, summarize, fill, suggest, remind, answer, rank.
Hỗ trợ action types, không phải work type hay domain.

**AI Role trong Decision Model**:
detect → suggest → explain.
Không tự quyết: không tự biến item thành Critical không có signal cứng,
không tự xoá item khỏi Today, không tự override priority rule.

## Xác thực & vai trò

**Authentication**:
App login dùng **password**, httpOnly cookies (`access_token`, `refresh_token`).
PBKDF2-SHA-256. Không dùng OAuth để login app.
_Avoid_: Bearer tokens, Google OAuth cho app login

**Gmail OAuth**:
Chỉ dùng cho Gmail Integration (sync mailbox / poll email / ingest inbox item).
Tách biệt với app login. Token Gmail có vòng đời riêng: refresh, revoke, rotate.
Không dùng OAuth này để đăng nhập HR Space.
_Avoid_: dùng OAuth từ Gmail cho app login

**Initial Setup Wizard**:
Luồng một lần tạo SUPER_ADMIN + cấu hình Organization.
Route: `/api/v1/setup/*`. Khóa sau khi hoàn tất.
_Avoid_: gọi nó là onboarding

**SUPER_ADMIN**:
Vai trò cao nhất, tạo bởi Setup Wizard. Quản lý user, gán role, mọi tác vụ HR.
Một SUPER_ADMIN mỗi instance.
_Avoid_: Super User

**HR_ADMIN**:
Vai trò HR đầy đủ: assign/archive work, contract lifecycle, document verify, settings.
_Avoid_: Admin (gây nhầm với SUPER_ADMIN)

**HR_STAFF**:
Vai trò HR giới hạn: read work, update/complete assigned work, add note, read context.
_Avoid_: User (gây nhầm với auth-account)

## Service & API

**WorkService**:
Owns WorkItem lifecycle + WorkItemPeopleLink / WorkItemDocumentLink /
WorkItemContractLink / WorkItemWorkLink.

**InboxService**:
Owns intake, classify, triage, dismiss, convert to work item.

**PeopleService**:
Owns People + EmployeeProfile + CandidateProfile.

**DocumentService**:
Owns Document lifecycle + PeopleDocumentLink.

**ContractService**:
Owns Contract lifecycle + ContractDocumentLink.

**AIService**:
Owns AISuggestion, PromptRun, AIJob.
KHÔNG tự mutate domain entity. Accept đi qua target service.

**AuditService**:
Helper/writer. Ghi AuditEvent trong cùng transaction với mutation.
Không tự mở transaction riêng.

**Idempotency-Key**:
Header cho write/action endpoints.
Same key + same user + same route + same payload hash = idempotent.
Khác payload → 409 IDEMPOTENCY_CONFLICT. Retention 24h.

**If-Unmodified-Since**:
Header cho optimistic concurrency trên entity quan trọng.
409 nếu stale.

## Cross-cutting

**Note**:
Ghi chú nội bộ. linked_entity_type whitelist: work_item, people, document, contract.

**Notification**:
Reminder / alert / daily_brief. linked_entity_type whitelist.
API create internal-only.

**AuditEvent**:
Log action cho transition quan trọng. Cùng transaction với mutation.
Ghi actor, action, entity_type/id, before/after (redacted), reason, source.
_Avoid_: Activity log không rõ source
