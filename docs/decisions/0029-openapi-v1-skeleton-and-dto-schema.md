# 0029 OpenAPI v1 Skeleton + DTO Schema v1

Date: 2026-07-04

## Status

Accepted — API contract skeleton đã validate. Bước kế: route handler / service implementation.

## Context

Sau khi API v1 freeze (0028), hội thoại đi vào OpenAPI v1 skeleton.
Mục tiêu: chốt contract trước implementation.

User yêu cầu:
- validate `docs/api/openapi.v1.skeleton.yaml`
- fill DTO schema v1
- thêm request/response schema cho command quan trọng
- chưa implement handler, chưa migration

Kết quả được báo cáo trong hội thoại:
- `docs/api/openapi.v1.skeleton.yaml` valid
- `operationId` unique: 102/102
- schemas core và request đã được gắn cho route quan trọng

## Decision

### 1. OpenAPI skeleton validated

File chuẩn để dùng:
- `docs/api/openapi.v1.skeleton.yaml`

Có mirror ở root `openapi.v1.skeleton.yaml`, nhưng source of truth là file trong `docs/api/`.

### 2. Skeleton contains

- path groups
- `operationId` naming convention = `Service_command`
- shared envelopes
- error catalog
- auth scheme
- pagination/filter schema
- job schema
- `Idempotency-Key`
- `If-Unmodified-Since`
- public/internal/background split pattern

### 3. DTO schema v1 added

#### 3.1 Shared envelopes

- `SuccessEnvelope_WorkItemDetail`
- `SuccessEnvelope_InboxItemDetail`
- `SuccessEnvelope_PeopleDetail`
- `SuccessEnvelope_DocumentDetail`
- `SuccessEnvelope_ContractDetail`
- `SuccessEnvelope_TemplateDetail`
- `SuccessEnvelope_AISuggestionDetail`
- `SuccessEnvelope_NoteDetail`
- `SuccessEnvelope_NotificationDetail`
- `SuccessEnvelope_AuditEventDetail`
- `SuccessEnvelope_JobAccepted`
- `SuccessEnvelope_CurrentUser`
- `SuccessEnvelope_UserSession`
- `SuccessEnvelope_ReportSummary`
- `SuccessEnvelope_Empty`

Paginated envelopes:
- `PaginatedEnvelope_WorkItemSummary`
- `PaginatedEnvelope_InboxItemSummary`
- `PaginatedEnvelope_PeopleSummary`
- `PaginatedEnvelope_DocumentSummary`
- `PaginatedEnvelope_ContractSummary`
- `PaginatedEnvelope_TemplateSummary`
- `PaginatedEnvelope_AISuggestionSummary`
- `PaginatedEnvelope_NotificationSummary`
- `PaginatedEnvelope_NoteSummary`
- `PaginatedEnvelope_AuditEventSummary`

#### 3.2 Domain DTO schemas

- `WorkItemDTO`
- `InboxItemDTO`
- `PeopleDTO`
- `EmployeeProfileDTO`
- `CandidateProfileDTO`
- `DocumentDTO`
- `ContractDTO`
- `TemplateDTO`
- `AISuggestionDTO`
- `NoteDTO`
- `NotificationDTO`
- `AuditEventDTO`

#### 3.3 Request schemas added

- `CreateWorkItemRequest`
- `UpdateWorkItemRequest`
- `CompleteWorkItemRequest`
- `ConvertInboxToWorkRequest`
- `UploadDocumentRequest` with `metadata_json`
- `CreateContractRequest`
- `AcceptSuggestionRequest`
- `CreateNoteRequest`

### 4. Route schemas already gắn

#### Work
- `POST /work`
- `GET /work/{workId}`
- `PATCH /work/{workId}`
- `POST /work/{workId}/complete`
- `POST /work/{workId}/accept-suggestion`

#### Inbox
- `POST /inbox/{inboxId}/triage`

#### Documents
- `POST /documents`

#### Contracts
- `POST /contracts`

#### Notes
- `POST /notes`

### 5. API contract rules confirmed

- `AcceptSuggestionRequest` đi qua target entity endpoint, không qua AI route.
- Auth dùng cookie-based JWT.
- `Idempotency-Key` và `If-Unmodified-Since` là headers chuẩn.
- Shared envelopes là contract chung cho FE/backend/AI.
- Route skeleton chưa full field detail cho tất cả DTO; chỉ chốt shape khung.

### 6. Implementation boundary

Chưa làm:
- route handler
- service implementation
- migration scripts

Đã làm:
- YAML valid
- operationId unique
- route map rõ
- schema khung đủ để scaffold

## Consequences

Positive:
- FE và backend có hợp đồng chung.
- operationId unique và naming theo service_command.
- Route quan trọng đã có request/response schema.
- OpenAPI skeleton đủ để scaffold codegen / handlers.

Tradeoffs:
- Một số wrapper schema còn generic/stub.
- Full field detail vẫn cần thêm ở phase route-by-route.
- Mirror root file tồn tại nhưng không phải source of truth.

## References

- ADR 0028: API v1 Design + Freeze Decisions
- docs/api/openapi.v1.skeleton.yaml
