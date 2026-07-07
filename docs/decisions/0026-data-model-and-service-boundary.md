# 0026 Data Model v1 + Service Boundary v1

Date: 2026-07-04

## Status

Accepted — Data Model + Service Boundary baseline. Bước kế: Service Boundary detailed.

## Context

Tiếp nối Domain Model v4 (0025), hội thoại thiết kế Data Model qua 2 bước:

1. **Data Model v1**: 5 design decisions + full table definitions.
2. **Data Model v1 delta**: 9 chỉnh nhỏ trước khi chốt.

Sau đó chuyển sang Service Boundary v1 — 8 services với ownership rõ.
User bổ sung 3 rule cuối: Audit service chỉ helper, AI accept qua target service,
link table ownership chốt.

User chốt: baseline này đủ để đi tiếp Service Boundary detailed.
Không viết migration scripts vội.

## Decision

### 1. Data Model — 5 Design Decisions

| # | Decision | Chi tiết |
|---|----------|----------|
| 1 | organization_id | Pre-place trên mọi aggregate root. Single-tenant MVP → constant |
| 2 | Controlled typed reference | DB enum + service layer enforcement. Whitelist: linked_entity_type, ai_source_entity_type |
| 3 | Lifecycle enforcement | Hybrid: DB constraint (enum, FK, unique) + Service layer (transition, semantic rule) |
| 4 | AI suggestion accepted | Cùng transaction: mutate entity + UPDATE AISuggestion + INSERT AuditEvent |
| 5 | Audit event recording | Cùng transaction với mutation. Async chỉ cho read-only/analytics |

### 2. Data Model — 9 Delta Fixes

| # | Issue | Fix |
|---|-------|-----|
| 1 | `user` là SQL keyword | Đổi thành `app_user` |
| 2 | `contract_type` thiếu `termination` | Thêm `termination` vào enum |
| 3 | `confidence_label` VARCHAR | Thành enum: high / medium / low |
| 4 | `decision_label` VARCHAR tự do | Thành enum: Critical / Attention / Planned / Waiting |
| 5 | `prompt_run.suggestion_ids` UUID[] | Bỏ UUID[]. Dùng `ai_suggestion.prompt_run_id` FK |
| 6 | `ai_job.suggestion_ids` UUID[] | Bỏ UUID[]. Dùng `ai_suggestion.ai_job_id` FK hoặc link table |
| 7 | InboxItem ↔ WorkItem 2 chiều | Giữ 1 chiều: `work_item.source_inbox_item_id`. Inbox query reverse |
| 8 | Link table org cross-org risk | Service layer enforce same organization_id |
| 9 | `created_at` / `updated_at` nullable | NOT NULL DEFAULT now() |

### 3. Data Model — Enum Chốt

(`app_user_role`, `work_item_status`, `work_item_source`, `work_link_type`,
`inbox_item_source`, `inbox_item_status`, `people_type`, `people_status`,
`people_source`, `employment_status`, `contract_type` thêm `termination`,
`contract_status`, `document_type`, `document_status`, `template_type`,
`template_scope`, `suggestion_type`, `suggestion_status`, `confidence_label`,
`ai_job_status`, `ai_job_type`, `notification_type`, `notification_status`,
`decision_label`, `audit_source`, `linked_entity_type`, `ai_source_entity_type`)

### 4. Service Boundary v1

| Service | Owns | Txn | AI touchpoint |
|---------|------|-----|---------------|
| Work Service | WorkItem lifecycle, decision label, assign, complete, reopen, archive, snooze | mutation + audit same txn | acceptSuggestion() qua domain |
| Inbox Service | Intake, classify, triage, dismiss, convert to work | triage → create WorkItem + update InboxItem + audit | — |
| People Service | People, EmployeeProfile, CandidateProfile | CRUD + audit | — |
| Document Service | Document, upload, verify, reject, expire | CRUD + audit | acceptExtraction() |
| Contract Service | Contract lifecycle, draft, ready, sent, signed, terminate | CRUD + audit | acceptDraft() |
| Template Service | Template CRUD, version, archive | CRUD + audit | — |
| AI Service | AISuggestion, PromptRun, AIJob | create suggestion (pending); reject/supersede; KHÔNG tự mutate domain | create suggestion |
| Notification Service | Notification create/send/read/dismiss/snooze | CRUD + audit | — |
| Audit Service | AuditEvent write, redaction, correlation_id | Helper — gọi trong txn của target service | — |
| Reporting Service | Summary, snapshot, answer | Read-only | — |
| Admin Service | app_user, permissions, org config, integration config | CRUD + audit | — |

### 5. Ba Rule Bổ Sung

| # | Rule | Lý do |
|---|------|-------|
| 1 | Audit Service là helper, không tự mở transaction riêng | Audit phải cùng txn với mutation — không thể tách rời |
| 2 | AI suggestion accept phải đi qua target service | AI Service không tự mutate domain. Work/Document/Contract có acceptSuggestion() riêng |
| 3 | Link table ownership chốt | WorkItem*Link → Work Service; ContractDocumentLink → Contract Service; PeopleDocumentLink → Document Service |

### 6. Link Table Ownership

| Link Table | Owner Service | Lý do |
|------------|---------------|-------|
| WorkItemPeopleLink | Work Service | Gắn người vào work item |
| WorkItemDocumentLink | Work Service | Gắn file vào work item |
| WorkItemContractLink | Work Service | Gắn hợp đồng vào work item |
| WorkItemWorkLink | Work Service | Parent/child/dependency giữa work items |
| PeopleDocumentLink | Document Service | Attachment/file lifecycle (nghiêng về Document) |
| ContractDocumentLink | Contract Service | File signed/gắn với contract |

### 7. Cross-Service Rules

- UI không gọi DB trực tiếp
- Cross-service link chỉ qua typed FK / link table
- AI suggestion accept qua target service (WorkService.acceptSuggestion, DocumentService.acceptExtraction, ContractService.acceptDraft)
- Audit helper gọi trong cùng transaction
- Service owns mutation + validation + audit trigger point

### 8. Next Phase — Service Boundary Detailed

User chốt: không viết migration vội. Bước kế là Service Boundary v1 detailed:

Mỗi service ghi rõ:
- Commands
- Queries
- Transaction boundary
- Audit point
- AI touchpoint
- Cross-service dependencies

## Consequences

Positive:
- Data Model sạch — `app_user`, enum đồng bộ, UUID[] loại bỏ.
- Audit trong cùng transaction — không mất trace.
- AI suggestion accept qua target service — domain boundary giữ.
- Link table ownership rõ — không hai service cùng ghi.
- organization_id pre-place — future multi-tenant không migration nặng.
- Service boundary bám module boundary — Work, Inbox, Context Libraries, AI, Admin.

Tradeoffs:
- Cross-org link check phải enforce ở service layer — DB không tự ngăn.
- Decision label là derived/cache — cần event trigger recompute.
- PeopleDocumentLink owner (Document Service) có thể gây nhầm nếu coi đây là hồ sơ employee.
- Service boundary detailed chưa có — chưa thể implement migration hay API.

## References

- ADR 0025: Domain Model v4 Baseline
- ADR 0024: Capability Taxonomy + Module Boundary
- ADR 0023: Interaction Model + Work Lifecycle
