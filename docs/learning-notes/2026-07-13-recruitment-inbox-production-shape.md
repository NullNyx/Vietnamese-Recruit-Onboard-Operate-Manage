# Recruitment Inbox — Production Shape (GH #184)

## Task
Triển khai Recruitment Inbox — một unified HR surface cho các email tuyển dụng cần phân loại thủ công hoặc đã hết lượt thử lại AI provider. Inbox item được tạo tự động khi confidence dưới threshold hoặc provider retry exhausted. HR có thể xem, sửa hướng định tuyến, hoặc bỏ qua item.

## What I changed

### Backend entity & migration
- **RecruitmentInboxItem** entity mới trong `recruitment_inbox_items` table với đầy đủ fields: classification result, correction tracking, dismissal, retry tracking, attachment metadata
- **Không** thêm inbox fields vào `JobApplication` (chỉ có RecruitmentInboxItem là single source of inbox state)
- Migration `061` chỉ tạo `recruitment_inbox_items`; downgrade sạch

### Classification Service
- Thêm `on_uncertain_classification` callback cho recruitment emails dưới threshold
- **Silent callback failure fix**: nếu callback fail, email được đánh dấu `needs_review` với `processing_error` thay vì `needs_classification`
- **Exhausted retry handler**: trong `_classify_single`, khi retries exhausted (>=3), gọi `on_uncertain_classification` callback để tạo inbox item với prediction=null/uncategorized + error metadata

### Inbox Service
- `create_from_classification`: idempotent creation, dismissed item suppression, attachment metadata extraction
- `correct_intent`: lưu correction history; Job Application đủ profile material chuyển `ready_for_review`, thiếu material chuyển `needs_information`, intent khác chuyển `resolved`
- `dismiss_item`: sets dismissed+resolved, raises `InboxItemDismissedError` cho double-dismiss

### Attachment metadata
- `attachments_metadata` JSONB field trên RecruitmentInboxItem: mảng các object {name?, type?, size?}
- Không persist raw content — chỉ safe metadata từ classification evidence

### DI Container
- `get_classification_service` wires `InboxService` + `RecruitmentInboxItemRepository` → `on_uncertain_classification` callback

### API Router
- All endpoints accept `RecruitmentInboxItemRepository` via `Depends(get_inbox_repo)` để testable
- `_require_hr` guard trên mọi endpoint

### Frontend
- `/recruitment/inbox` page với full UI: filter tabs, detail dialog, correct/dismiss actions
- Attachment metadata hiển thị name, type, size
- Nav link từ `/recruitment` page

### Tests
- **Journey tests** (21 tests): uncertain routing, callback failure, exhausted retry, dismissed suppression, filter states, attachment metadata
- **Auth API tests** (10 tests): HTTP boundary, HR vs Employee vs unauthenticated cho mọi endpoint

## The real problem
Vấn đề cốt lõi là single source of inbox state: `JobApplication` cho confident emails, `RecruitmentInboxItem` cho uncertain/exhausted emails — hai entity nhưng cùng biểu diễn inbox state. Nếu đặt inbox fields trên cả hai, sẽ có asymmetric update logic và migration phức tạp. Giải pháp: chỉ `RecruitmentInboxItem` mang inbox state, `JobApplication` là clean entity chỉ cho confident ingestion.

Vấn đề thứ hai: classification callback failure silent. Khi tạo inbox item mà DB fail, email vẫn bị đánh dấu `needs_classification` — HR không biết có lỗi. Fix: khi callback fail, đánh dấu `needs_review` với error message.

Vấn đề thứ ba: exhausted provider retry không tạo inbox item. Provider down 3 lần → email bị đánh dấu `permanently_failed` nhưng không ai biết để review. Fix: gọi uncertain callback trong exhausted branch của `_classify_single`.

## Why this solution
- **Single source of truth**: inbox state chỉ trên RecruitmentInboxItem, JobApplication sạch
- **Fail-safe callbacks**: mọi callback failure đều visible qua processing_status/error
- **Testable DI**: API router dùng `Depends(get_inbox_repo)` thay vì hardcode constructor, cho phép override trong test
- **Idempotent creation**: create_from_classification kiểm tra dismissed và existing item trước khi tạo mới

## Production shape
- Entity: `RecruitmentInboxItem` (table: `recruitment_inbox_items`), không fields trên `JobApplication`
- Status: `needs_classification`, `needs_information`, `ready_for_review`, `resolved`
- Inbox items created from: (a) recruitment emails below confidence threshold, (b) exhausted provider retries
- Corrections: `job_application` → `ready_for_review` khi có attachment metadata, ngược lại → `needs_information`; intent khác → `resolved`; dismissal → dismissed + `resolved`
- Dismissed items: retained, protected from retry recreation, returned idempotently
- Attachments: `attachments_metadata` [{name, type, size}] — safe metadata, no raw content

## Other possible approaches
1. **Inbox fields on JobApplication**: thêm inbox_status + prediction fields vào JobApplication; dùng chung entity cho cả confident và uncertain
2. **Separate inbox service with its own DB table but no callback pattern**: inbox items created via direct service call from classification worker
3. **Status-based routing on EmailMessage**: dùng processing_status trên EmailMessage để HR filter, không cần entity riêng

## Why I did not choose those alternatives
1. **Inbox fields on JobApplication**: asymmetric — confident emails có JobApplication, uncertain thì không. Migration phức tạp, query logic khó maintain. Vi phạm single source of truth.
2. **No callback pattern**: direct service call từ worker tạo coupling giữa gmail module và recruitment module. Callback pattern cho phép DI + test isolation.
3. **Status on EmailMessage**: EmailMessage là Gmail entity, không nên mang recruitment-specific state. RecruitmentInboxItem cho phép recruitment-specific fields (correction_history, dismissed_by) mà không pollute Gmail schema.

## Key concepts to learn
- **FastAPI dependency overrides**: `app.dependency_overrides[get_inbox_repo]` for testable DI
- **Callback pattern in service**: `on_uncertain_classification` callback injected via constructor
- **Idempotent creation**: check dismissed → check existing → create
- **Safe attachment metadata**: extract name/type/size from email entity, not raw content
- **HTTP boundary testing**: `TestClient` + `dependency_overrides` pattern

## Common mistakes
- Quên check dismissed item trước khi tạo mới → retry worker sẽ tạo lại dismissed item
- Quên handle callback failure → silent data loss
- Đặt inbox fields trên JobApplication + RecruitmentInboxItem → duplicate state
- Không expose attachment metadata qua API → HR không biết email có gì
- Hardcode constructor trong router → không testable

## Small example
```python
# Callback wiring in DI container
inbox_repo = RecruitmentInboxItemRepository(session)
inbox_service = InboxService(session=session, inbox_repo=inbox_repo)
return ClassificationService(
    ...,
    on_uncertain_classification=inbox_service.create_from_classification,
)

# Idempotent creation
dismissed = await repo.find_dismissed_by_gmail_message_id(msg_id)
if dismissed:
    return dismissed  # don't recreate
existing = await repo.get_by_gmail_message_id(msg_id)
if existing:
    return existing  # don't duplicate
```

## How to think about this next time
Khi thiết kế tính năng mới:
1. Xác định single source of truth cho mỗi domain concept
2. Thiết kế callback pattern cho cross-module communication
3. Đảm bảo mọi failure path đều visible (không silent catch)
4. Attachment và PII: không persist raw content, chỉ metadata
5. API endpoint phải testable qua DI override
6. Migration phải match entity chính xác — không leftover columns
