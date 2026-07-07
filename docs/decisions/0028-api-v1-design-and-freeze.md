# 0028 API v1 Design + Freeze Decisions

Date: 2026-07-04

## Status

Accepted — API v1 contract frozen. Bước kế: OpenAPI v1 skeleton.

## Context

Tiếp nối Service Boundary (0027), hội thoại thiết kế API v1 qua 3 bước:

1. **API v1 design** — full route groups cho 13 surface: Work, Inbox, People,
   Documents, Contracts, Templates, AI, Notifications, Notes, Audit, Reports,
   Search, Admin, Auth.
2. **API v1 delta** — 10 điểm chỉnh: Notes route, Search handler, Work accept-suggestion,
   Permission matrix, Notification create scope, Audit read-only, Work link delete
   với link_type, Document upload multipart, Idempotency key, route naming consistency.
3. **API v1 freeze delta** — 10 điểm cuối: Public/Internal/Background API,
   202 Accepted pattern, Optimistic concurrency, Bulk route reserve, Filter convention,
   Error code catalog, Versioning policy, Idempotency scope, Route naming consistency,
   API contract freeze.

User chốt: freeze API v1. Bước kế là **OpenAPI v1 skeleton** — khung hợp đồng
trước khi fill detail DTO.

## Decision

### 1. API v1 Route Groups

#### 1.1 Work

| Method | Path | Service |
|--------|------|---------|
| GET | /api/v1/work | WorkService.todayQuery / allWorkQuery |
| GET | /api/v1/work/today | WorkService.todayQuery |
| GET | /api/v1/work/:id | WorkService.workDetailQuery |
| POST | /api/v1/work | WorkService.createWorkItem |
| PATCH | /api/v1/work/:id | WorkService.updateWorkItem |
| POST | /api/v1/work/:id/complete | WorkService.completeWorkItem |
| POST | /api/v1/work/:id/assign | WorkService.assignWorkItem |
| POST | /api/v1/work/:id/reopen | WorkService.reopenWorkItem |
| POST | /api/v1/work/:id/archive | WorkService.archiveWorkItem |
| POST | /api/v1/work/:id/snooze | WorkService.snoozeWorkItem |
| POST | /api/v1/work/:id/accept-suggestion | WorkService.acceptSuggestion |

Link management:
| POST | /api/v1/work/:id/links/people | linkPeople |
| DELETE | /api/v1/work/:id/links/people/:peopleId | unlinkPeople |
| POST | /api/v1/work/:id/links/documents | linkDocument |
| DELETE | /api/v1/work/:id/links/documents/:docId | unlinkDocument |
| POST | /api/v1/work/:id/links/contracts | linkContract |
| DELETE | /api/v1/work/:id/links/contracts/:contractId | unlinkContract |
| POST | /api/v1/work/:id/links/work | linkWork |
| DELETE | /api/v1/work/:id/links/work/:targetId?link_type= | unlinkWork |

#### 1.2 Inbox

| Method | Path | Service |
|--------|------|---------|
| GET | /api/v1/inbox | InboxService.inboxList |
| GET | /api/v1/inbox/:id | InboxService.inboxDetail |
| POST | /api/v1/inbox | InboxService.ingestInboxItem |
| POST | /api/v1/inbox/:id/classify | InboxService.classifyInboxItem |
| POST | /api/v1/inbox/:id/triage | InboxService.convertInboxToWork |
| POST | /api/v1/inbox/:id/dismiss | InboxService.dismissInboxItem |

#### 1.3 People

CRUD: GET/POST /api/v1/people, PATCH/DELETE /api/v1/people/:id, plus archive.
Profiles: employee-profile, candidate-profile subroutes.

#### 1.4 Documents

CRUD + verify, reject, expire, accept-extraction, linkPeople/unlink.

#### 1.5 Contracts

CRUD + send, sign, terminate, expire, create-amendment, accept-draft,
linkDocument/unlink.

#### 1.6 Templates

CRUD + version, archive, activate.

#### 1.7 AI

suggestions (list, detail, create, reject, supersede — KHÔNG có accept),
run-prompt (202 → job_id), jobs (list, detail).

#### 1.8 Notifications

list, unread-count, mark-read, dismiss, snooze.
Internal create only.

#### 1.9 Notes

GET/POST /api/v1/notes, PATCH/DELETE /api/v1/notes/:id.

#### 1.10 Audit

Read-only: list, by-entity, by-actor, detail.

#### 1.11 Search

GET /api/v1/search?q=&type= — handled by SearchQueryHandler, not middleware.

#### 1.12 Reports

daily-summary, weekly-summary, status-snapshot, ask (NL).

#### 1.13 Admin

Users CRUD, settings read/write, integrations config.

#### 1.14 Auth

login/logout/refresh/me — JWT httpOnly cookies.

### 2. API v1 — 10 Freeze Decisions

| # | Decision | Chi tiết |
|---|----------|----------|
| 1 | Public / Internal / Background | Public `/api/v1/` JWT; Internal `/api/v1/internal/` service token; Background job queue worker token |
| 2 | Long-running → 202 Accepted | AI run-prompt, report generate, extract → 202 + job_id. Track qua GET /api/v1/jobs/:id |
| 3 | Optimistic concurrency | WorkItem/Contract/Document/People — `updated_at` comparison. Template — `version` integer. 409 nếu stale |
| 4 | Bulk endpoints (reserve) | `POST /resource/bulk/action`. Body `{ ids, payload }`. Response `{ succeeded, failed }`. Chưa implement |
| 5 | Filter convention | `?status=a,b&sort=-field&page=1&size=20`. Comma-separated, DESC prefix `-`. Thống nhất mọi module |
| 6 | Error code catalog | VALIDATION_ERROR, PERMISSION_DENIED, RESOURCE_NOT_FOUND, INVALID_STATUS_TRANSITION, DUPLICATE_RESOURCE, CONFLICT, AI_SUGGESTION_MISMATCH, IDEMPOTENCY_CONFLICT, INTERNAL_ERROR |
| 7 | API versioning | `/api/v1/`. Additive → không bump. Breaking → `/v2`. Deprecated endpoint có header `Sunset:` |
| 8 | Idempotency scope | `Idempotency-Key` header. Match: same key + user + route + payload hash. Mismatch payload → 409 IDEMPOTENCY_CONFLICT. Retention 24h |
| 9 | Route naming | Action `POST /resource/:id/action`. State `PATCH /resource/:id`. List `GET /resource`. Detail `GET /resource/:id`. Link `POST /resource/:id/links/target`. Unlink `DELETE /resource/:id/links/target/:id` |
| 10 | API contract freeze | Request/response/error DTO shape + route frozen. Implementation không freeze |

### 3. Permission Matrix

| Role | Work write | Contract lifecycle | Admin/Config |
|------|-----------|-------------------|--------------|
| hr_staff | Update/complete assigned work | Read | None |
| hr_admin | Assign, archive, full mutation | Send, sign, terminate | Settings read/write |
| super_admin | Full | Full | User, role, integration, AI config |

### 4. Conventions

- prefix: `/api/v1`
- response envelope: `{ data, meta, error }`
- pagination: `{ data, meta: { page, size, total } }`
- error: `{ error: { code, message, details } }`
- auth: cookie-based JWT
- organization_id từ current_user, không từ request path
- multipart/form-data cho file upload
- AI accept qua target entity endpoint (không qua AI route)
- Audit write internal-only

### 5. Implementation Order

User chốt: OpenAPI trước migration.

```
1. OpenAPI v1 skeleton     ← bắt đầu tại đây
2. Error catalog + DTO schema
3. Enums + migration scripts
4. DB models + constraints
5. Middleware nền (auth, permission, org scope, idempotency, error handler)
6. Service layer (Work → Inbox → People → Document → Contract → Template → AI → Notification → Note → Audit → Reports/Search → Admin/Auth)
7. API handlers
8. Tests
9. Integration
```

### 6. Next Phase — OpenAPI v1 Skeleton

Skeleton gồm:
- path groups
- operationId naming convention (map về service command/query)
- shared schemas: SuccessEnvelope\<T\>, PaginatedEnvelope\<T\>, ErrorEnvelope
- error schema
- auth scheme (cookie-based JWT)
- pagination/filter schema
- job schema
- idempotency header (`Idempotency-Key`)
- concurrency header (`If-Unmodified-Since`)
- action endpoint khai báo: idempotency required, error codes

Chưa define full DTO field. Mục tiêu: FE có route map, Backend biết handler mapping,
AI/codegen scaffold được.

## Consequences

Positive:
- API v1 contract frozen — FE/AI/Backend cùng bám.
- 10 freeze decisions bao phủ: async, concurrency, bulk, filter, error, versioning, idempotency, naming.
- Permission matrix rõ — hr_staff không bị khóa hoàn toàn.
- OpenAPI skeleton first — khung trước detail.
- Public/Internal/Background tách — không lẫn security boundary.

Tradeoffs:
- Idempotency payload hash + retention 24h cần storage.
- Bulk route reserve chưa implement — pattern cần maintain.
- OpenAPI skeleton chưa fill DTO — cần thêm 1 phiên detail.
- API contract freeze có thể chậm iteration nếu phát hiện thiếu endpoint.

## References

- ADR 0027: Service Boundary Corrected + Migration Plan
- ADR 0026: Data Model v1 + Service Boundary v1
- ADR 0025: Domain Model v4 Baseline
