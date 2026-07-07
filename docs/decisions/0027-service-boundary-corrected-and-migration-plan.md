# 0027 Service Boundary Corrected + Migration Script Plan

Date: 2026-07-04

## Status

Accepted — Service Boundary + Migration plan. Bước kế: API Design.

## Context

Tiếp nối Data Model + Service Boundary baseline (0026), hội thoại chỉnh 2 điểm:

1. **DocumentService và ContractService không own Work link** — WorkService owns.
2. **Migration plan** — table creation order + FK dependency fixes + seed data.

User chốt: corrected commands OK. Migration plan OK sau khi fix 5 FK issues.
Bước kế là **API Design** (trước migration thật).

## Decision

### 1. Service Boundary — Corrected Commands

#### 1.1 Link Table Ownership Rule

> **Link table owner = service sở hữu use case chính của relationship.**

| Link Table | Owner | Use case |
|------------|-------|----------|
| WorkItemPeopleLink | WorkService | Work execution context |
| WorkItemDocumentLink | WorkService | Work execution context |
| WorkItemContractLink | WorkService | Work execution context |
| WorkItemWorkLink | WorkService | Work execution context |
| ContractDocumentLink | ContractService | Contract evidence / signed file |
| PeopleDocumentLink | DocumentService | Hồ sơ / attachment lifecycle |

#### 1.2 DocumentService (corrected)

**Owns:** Document lifecycle + PeopleDocumentLink

Commands:
- uploadDocument
- verifyDocument
- rejectDocument
- expireDocument
- linkDocumentToPeople
- unlinkDocumentFromPeople
- acceptExtraction

**Không có:** `linkDocumentToWork` — WorkService owns WorkItemDocumentLink.

#### 1.3 ContractService (corrected)

**Owns:** Contract lifecycle + ContractDocumentLink

Commands:
- createContract
- updateContractDraft
- changeContractStatus
- sendContract
- signContract
- terminateContract
- expireContract
- createAmendment
- acceptDraft
- linkContractToDocument
- unlinkContractFromDocument

**Không có:** `linkContractToWork` — WorkService owns WorkItemContractLink.

#### 1.4 WorkService (corrected)

Bổ sung link commands:
- linkPeople / unlinkPeople
- linkDocument / unlinkDocument
- linkContract / unlinkContract
- linkWork / unlinkWork

### 2. Migration Script Plan — Approach

- Không viết SQL migration ngay.
- Plan: thứ tự tạo bảng, dependency graph, seed data, script runner.
- Single migration file per entity.
- Idempotent.
- Enum DDL trước table DDL.
- Seed data riêng (default org, super_admin, templates).

### 3. Table Creation Order (corrected)

#### Core tables (16):

```
 1. organization
 2. app_user
 3. template
 4. inbox_item               (FK → organization; KHÔNG có converted_work_item_id)
 5. people
 6. employee_profile
 7. candidate_profile
 8. document
 9. prompt_run
10. ai_job
11. work_item                (FK → organization, user, inbox_item nullable)
12. contract                 (FK → organization, people, template, document nullable, self-ref nullable)
13. ai_suggestion            (FK → organization, user, prompt_run)
14. notification
15. audit_event
16. note
```

#### Link tables (6):

```
17. work_item_work_link
18. work_item_people_link
19. work_item_document_link
20. work_item_contract_link
21. people_document_link
22. contract_document_link
```

#### FK Dependency Fixes (so với bản cũ)

| # | Issue | Fix |
|---|-------|-----|
| 1 | template tạo sau contract | template lên trước contract (3 → 12) |
| 2 | prompt_run tạo sau ai_suggestion | prompt_run lên trước ai_suggestion (9 → 13) |
| 3 | inbox_item có FK vòng tới work_item | Bỏ `converted_work_item_id` khỏi inbox_item. Chỉ giữ `work_item.source_inbox_item_id` 1 chiều |
| 4 | inbox_item có `converted_work_item_id` | Bỏ field này — không còn FK vòng |
| 5 | document trước contract (đã đúng) | Giữ nguyên |

### 4. Migration Rules

| Rule | Chi tiết |
|------|----------|
| Enum DDL | File riêng, chạy trước mọi table |
| created_at/updated_at | `NOT NULL DEFAULT now()` |
| ON DELETE FK | Rõ policy: restrict / cascade / set null |
| people.work_email | Unique non-null cho employee scoped theo organization |
| template unique | `(organization_id, type, name, version)` |
| Seed data | File riêng — không chung với schema migration |

### 5. Next Phase — API Design

User nghiêng về API Design trước migration thật — API sẽ xác nhận
command/query boundary có đủ chưa trước khi khóa schema.

## Consequences

Positive:
- Work link thuộc Work Service — Document/Contract không viết lên link của Work.
- Link table ownership rule rõ hơn: "use case chính của relationship".
- Migration plan có dependency order chính xác — không FK vòng.
- inbox_item bỏ converted_work_item_id — không circular FK.
- prompt_run trước ai_suggestion — FK chain đúng.

Tradeoffs:
- WorkService link commands tăng số lượng (link/unlink cho 4 entity type).
- ContracService phải query WorkItemContractLink qua WorkService read.
- Migration script chưa viết — còn plan.

## References

- ADR 0026: Data Model v1 + Service Boundary v1 baseline
- ADR 0025: Domain Model v4 Baseline
