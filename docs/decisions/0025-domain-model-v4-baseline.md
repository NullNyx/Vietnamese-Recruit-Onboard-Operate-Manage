# 0025 Domain Model v4 — Baseline

Date: 2026-07-04

## Status

Accepted — Domain Model layer. Baseline để xuống Data Model.

## Context

Tiếp nối Capability Taxonomy + Module Boundary (0024), hội thoại xây Domain Model
qua 4 phiên (v1→v4):

- **v1**: WorkItem center, polymorphic refs, People gộp employee/candidate/contact.
- **User feedback**: polymorphic quá rộng, People gộp không rõ, OnboardingCase nên bỏ,
  8 điểm chính cần chỉnh.
- **v2**: Typed link tables, People core gọn + EmployeeProfile/CandidateProfile extensions,
  onboarding là work pattern, parent/child còn duplication.
- **v3**: WorkItem không god entity, AI boundary riêng (AISuggestion, PromptRun, AIJob),
  shared capability tách khỏi WorkItem, 8 điểm chốt.
- **v4 (delta)**: 7 điểm refine cuối cùng — WorkItemWorkLink 1 chiều,
  controlled typed reference, PromptRun sanitized, contract constraint,
  suggestion vs confirmed state tách, lifecycle rules tối thiểu.

User chốt: v4 làm baseline. Bước kế là **Data Model**.

## Decision

### 1. Nguyên tắc Domain Model

- `WorkItem` là trung tâm — nhưng chỉ sở hữu execution state + work links.
- Không có entity `Today` / `All Work` / `Work Detail` — đây là query/view.
- Không có `OnboardingCase` — onboarding là WorkItem pattern (parent/child).
- `People` là common identity layer — employee/candidate-specific fields ở profile extension.
- Link tables thay polymorphic refs rộng tay.
- AI có boundary riêng — không rải AI state vào Work/Document/Contract.
- Decision Model fields (`priority_score`, `decision_label`, `priority_reason`) là derived/cache.
- `organization_id` pre-placed trên aggregate roots; single-tenant = intentional simplification.

### 2. Entity List

#### 2.1 WorkItem

| Góc | Mô tả |
|-----|-------|
| Purpose | Execution state của một work item |
| Owns | status, source, owner, due, blocking, derived priority |
| Does not own | Collection của Notification/Note/Audit/Links-to-People/Document/Contract |
| Lifecycle | active → in_progress → completed; → waiting; completed → reopened → active; any → archived |

Key fields: id, organization_id, title, status, source, owner_id, due_at, blocking,
waiting_for_external, priority_score *(derived)*, decision_label *(derived)*, priority_reason *(derived)*,
created_at, updated_at, completed_at, archived_at.

Relationships: owner → User, source_inbox_item → InboxItem, outgoing/incoming → WorkItemWorkLink.

#### 2.2 InboxItem

Raw input trước triage. new → triaged (tạo WorkItem) hoặc new → dismissed.
Không là work item cho tới khi triage xong.

#### 2.3 People

Common identity/contact layer. Gọn, không type-specific fields.
type: employee / candidate / contact. Manager_id chỉ ở EmployeeProfile.

#### 2.4 EmployeeProfile

1:1 với People khi type = employee. Chứa department, position, manager_people_id,
employment_status, started_at, termination_date.

#### 2.5 CandidateProfile

1:1 với People khi type = candidate. Chứa pipeline_status, source_email, summary, job_opening_ref.

#### 2.6 Document

Pure library entity. Không sở hữu relationship collections — link tables sở hữu.
Không lưu AI suggestion — chỉ giữ applied_extracted_data_json sau HR confirm.
AISuggestion là nơi giữ extraction draft.

#### 2.7 Contract

Purpose: hợp đồng lao động và draft.
Contract type constraint:
- offer → có thể gắn candidate
- labor_contract / amendment / termination → phải gắn employee
- nda → tùy use case

Lifecycle: draft → ready → sent → signed → expired / terminated; draft → cancelled.

#### 2.8 Template

Mẫu dùng lại. Không tự sinh work item — Work service làm phần đó.

#### 2.9 AISuggestion

AI output chờ HR confirm. source_entity_type/id controlled typed reference
(whitelist: work_item, inbox_item, document, contract, people).
Lifecycle: pending → accepted / rejected / superseded.

#### 2.10 PromptRun

Ghi một lần gọi AI. Chỉ lưu sanitized_prompt / sanitized_response.
Raw payload opt-in, restricted, redacted, retention policy riêng.

#### 2.11 AIJob

AI job nền. Job type: classification / extraction / batch_draft / daily_summary.
Status: queued / running / completed / failed.

#### 2.12 Link Tables

| Link | Từ | Tới | Link type |
|------|----|-----|-----------|
| WorkItemWorkLink | from_work_item_id | to_work_item_id | parent_child / dependency / blocker / related |
| WorkItemPeopleLink | work_item_id | people_id | role nullable |
| WorkItemDocumentLink | work_item_id | document_id | role nullable |
| WorkItemContractLink | work_item_id | contract_id | role nullable |
| PeopleDocumentLink | people_id | document_id | role nullable |
| ContractDocumentLink | contract_id | document_id | role nullable |

WorkItemWorkLink là cơ chế duy nhất cho parent/child (không parent_work_item trên WorkItem).

#### 2.13 Shared Capabilities (controlled typed reference)

| Entity | linked_entity_type whitelist | Ghi chú |
|--------|------------------------------|---------|
| Notification | work_item / people / document / contract | Không phải collection của WorkItem |
| AuditEvent | work_item / inbox_item / people / document / contract / template / user | reason/context bắt buộc cho transition quan trọng |
| Note | work_item / people / document / contract | Không phải collection của WorkItem |

#### 2.14 User / Organization

User: role super_admin / hr_admin / hr_staff.
Organization: single-tenant MVP, organization_id pre-placed.

### 3. Chốt 8 điểm v3 → v4

| # | Vấn đề | v4 |
|---|--------|----|
| 1 | WorkItem god entity | WorkItem chỉ execution state + work links. Không collection Notif/Note/Audit/Link |
| 2 | Notification, Note, Audit collection trên WorkItem | Shared capability — controlled typed ref |
| 3 | Parent/Child hai cơ chế | Chỉ WorkItemWorkLink. Không parent_work_item trên WorkItem |
| 4 | manager_id ở People và EmployeeProfile | Chỉ ở EmployeeProfile |
| 5 | Document relationship collections | Document pure library. Relationships ở link tables |
| 6 | AI không boundary | AISuggestion, PromptRun, AIJob riêng |
| 7 | Decision fields có thể hiểu nhầm SoT | Ghi rõ derived/cache |
| 8 | Multi-tenant không rõ | organization_id pre-placed; single-tenant intentional simplification |

### 4. Chốt 7 điểm refine cuối

| # | Điểm | Quyết định |
|---|------|-----------|
| 1 | WorkItemWorkLink link_type | Chỉ parent_child / dependency / blocker / related. Không parent+child song song |
| 2 | AISuggestion source ref | Controlled typed reference. Whitelist: work_item, inbox_item, document, contract, people |
| 3 | PromptRun data | Chỉ lưu sanitized_prompt / sanitized_response. Raw payload opt-in, restricted, redacted |
| 4 | Contract.person_id | offer → candidate; labor_contract/amendment/termination → employee; nda → tùy |
| 5 | Document.extracted_data_json | Không lưu suggestion. Chỉ applied_extracted_data_json sau HR accept |
| 6 | Note/Notification/Audit ref | Controlled typed reference — whitelist entity types |
| 7 | Lifecycle rules tối thiểu | WorkItem, Contract, AISuggestion có state transition rõ |

### 5. Next Phase — Data Model

User chốt: Domain Model v4 làm baseline. Bước kế là **Data Model**,
cần đi kèm:

- Constraint, index, foreign key, enum, unique rule
- Audit trigger point
- Derived/cache recomputation rule
- organization_id xuất hiện ở aggregate root nào
- Controlled typed reference whitelist ở enum hay validation layer
- Lifecycle enforce ở DB constraint, service layer, hay cả hai
- AI suggestion accepted mutate entity đích trong transaction nào
- Audit event ghi trong cùng transaction hay async

## Consequences

Positive:
- WorkItem không phình — chỉ execution state + work links.
- AI boundary rõ — AISuggestion/PromptRun/AIJob riêng.
- People/Profile tách — employee/candidate extensions không nhồi core.
- Typed link tables — không polymorphic rộng tay.
- Document pure library — không chứa suggestion, không relationship collections.
- Prompt log an toàn — sanitized mặc định, raw opt-in.
- Lifecycle rules tối thiểu — đủ để enforce ở Data Model / Service layer.
- organization_id pre-placed — không block multi-tenant sau này.

Tradeoffs:
- WorkItemWorkLink parent_child cần query join — tradeoff so với self-ref parent_id.
- Controlled typed reference whitelist cần maintain — mỗi entity mới phải cập nhật.
- AI suggestion accepted transaction có thể phức tạp — mutate entity đích + ghi audit + update suggestion status.
- Document không lưu suggestion — cần AIService orchestration giữa AI output và entity update.

## References

- ADR 0024: Capability Taxonomy + Module Boundary
- ADR 0023: Interaction Model + Work Lifecycle
- ADR 0022: IA, Screen Skeletons, Today Decision Model
- ADR 0021: Product Identity + Work Taxonomy
