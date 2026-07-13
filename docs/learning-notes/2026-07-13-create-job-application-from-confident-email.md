# Task

Triển khai Issue #183: Tạo Job Application từ email tuyển dụng đã được phân loại tự tin. Khi Gmail ClassificationService phân loại một email là `recruitment` với confidence trên threshold, hệ thống sẽ tự động tạo một bản ghi Job Application — không tạo Candidate, không gọi AI để quyết định intent, chỉ dùng deterministic rules để làm evidence.

# What I changed

1. **Domain enums** (`modules/recruitment/domain/enums.py`): Thêm `ApplicationSource` (direct, employee_referral, agency), `JobApplicationStatus` (new, dismissed, promoted), `JobApplicationProcessingStatus` (pending, completed, failed, permanently_failed).

2. **Entity** (`modules/recruitment/domain/entities.py`): Thêm model `JobApplication` với các trường:
   - `id`: UUID primary key
   - `source_email_message_id`: FK → `email_messages.id` (liên kết tới email gốc)
   - `gmail_message_id`, `gmail_thread_id`: Denormalized từ EmailMessage
   - `source`: ApplicationSource enum (direct, employee_referral, agency)
   - `applicant_name`, `applicant_email`: Nullable; chỉ populate khi source=direct
   - `sender_name`, `sender_email`: Luôn lưu từ email (phân biệt với applicant)
   - `job_opening_id`: Optional FK → `job_openings.id`
   - `status`: JobApplicationStatus (mặc định new)

3. **Repository** (`modules/recruitment/infrastructure/repositories.py`): Thêm `JobApplicationRepository` với các method `create`, `get_by_id`, `get_by_gmail_message_id` (idempotent check), `update`.

4. **Service** (`modules/recruitment/application/job_application_service.py`): Tạo `JobApplicationService` với:
   - `create_from_classification(email, classification_result)`: Entry point duy nhất.
   - Idempotent: kiểm tra JobApplication đã tồn tại cho `gmail_message_id` chưa.
   - Source derivation: từ `matched_signals` của ClassificationResult (referral → employee_referral, agency/headhunter → agency).
   - Applicant identity: copy từ sender khi source=direct; null khi referral/agency.

5. **Gmail ClassificationService** (`modules/gmail/application/classification_service.py`): Thêm optional callback `on_application_created` trong constructor. Callback được gọi trong `_apply_classification` sau khi email được đánh dấu "classified" và category=recruitment. Callback được wrap trong try/except để không bao giờ làm hỏng classification.

6. **Gmail container** (`modules/gmail/container.py`): Wire `JobApplicationService` vào `ClassificationService` qua `on_application_created`.

7. **Alembic migration** (`alembic/versions/060_create_job_applications.py`): Tạo bảng `job_applications` với indexes và foreign keys.

8. **Alembic env.py**: Import `JobApplication` để metadata registration.

9. **Tests** (`tests/modules/gmail/test_job_application_ingestion.py`): 7 integration tests covering:
   - Confident recruitment → tạo JobApplication
   - Idempotent: cùng email không tạo duplicate
   - Non-recruitment → không tạo JobApplication
   - Low confidence → không tạo, vào needs_review
   - Callback failure → classification vẫn preserved
   - Referral signal → source=employee_referral, applicant nullable
   - Agency signal → source=agency, applicant nullable

# The real problem

Làm thế nào để bridge Gmail classification (module gmail) với Job Application ingestion (module recruitment) mà không tạo circular dependency, không để AI tự ý tạo Candidate, và giữ cho provider failure không ảnh hưởng tới classification?

Vấn đề cốt lõi là ranh giới module: Gmail không nên biết về recruitment domain model, nhưng recruitment cần biết về Gmail's ClassificationResult. Giải pháp là dùng callback pattern (inversion of control) — Gmail ClassificationService nhận một optional callback, và container layer (biết cả hai module) wire chúng lại với nhau.

# Why this solution

- **Deep JobApplicationService**: Service chứa toàn bộ policy (idempotent check, source derivation, applicant identity logic). ClassificationService không cần biết các policy này.
- **Callback pattern**: ClassificationService không import recruitment trực tiếp. Callback được inject từ container.
- **Try/except wrapper**: Callback failure không bao giờ làm hỏng classification. Email vẫn được đánh dấu "classified".
- **Idempotent by design**: Key trên `gmail_message_id` — dù classify_batch gọi nhiều lần, chỉ một JobApplication được tạo.
- **Conservative applicant identity**: Chỉ copy sender → applicant khi source=direct; referral/agency giữ applicant nullable.

# Production shape

Trong production:
1. Gmail worker poll emails → lưu EmailMessage → gọi `classify_batch`
2. ClassificationService chạy rules hoặc AI classifier
3. Nếu confident + recruitment → callback tạo JobApplication
4. JobApplication được lưu với status=new, sẵn sàng cho HR review trong Recruitment Inbox
5. Nếu provider fail → email được retry, không tạo JobApplication
6. Nếu AI không chắc chắn → email vào needs_review, không tạo JobApplication

Flow này nằm trong pipeline đồng bộ (trong cùng request/session), không qua ARQ queue.

# Other possible approaches

## Approach A: Direct import (Gmail → Recruitment)

ClassificationService import trực tiếp JobApplicationService và gọi nó.

**Ưu điểm**: Đơn giản, dễ hiểu, ít code.

**Nhược điểm**: Tạo dependency từ gmail module vào recruitment module. Gmail module mất tính độc lập. Nếu sau này muốn tách thành package riêng, sẽ khó khăn.

## Approach B: Domain event / Pub-sub

Sau khi classification hoàn tất, emit một domain event (ví dụ: `EmailClassified`). Một consumer/subscriber ở recruitment module lắng nghe event và tạo JobApplication.

**Ưu điểm**: Decoupling hoàn toàn. Gmail module không cần biết recruitment tồn tại.

**Nhược điểm**: Overengineering cho issue-scoped bridge. Event bus (ARQ) chạy async, có latency. Cần xử lý eventual consistency, failure handling phức tạp hơn. Issue #183 chỉ cần synchronous bridge.

## Approach C: Intermediate table / Webhook

ClassificationService ghi vào một bảng trung gian (ví dụ: `classification_events`). Recruitment module poll bảng này và xử lý.

**Ưu điểm**: Decoupling mạnh, không có import dependency.

**Nhược điểm**: Polling overhead, eventual consistency, cần cleanup. Quá nặng cho issue scope.

# Why I did not choose those alternatives

- **Direct import** (Approach A): Tạo tight coupling. Gmail module đang clean và có thể tái sử dụng. Thêm import vào recruitment sẽ phá vỡ modularity. Tuy nhiên, container layer đã import cả hai module — đây là nơi đúng để wire.

- **Domain event** (Approach B): Event-driven là kiến trúc tốt cho future Recruitment Inbox (parent issue #180), nhưng issue #183 là minimal bridge. Thêm event bus sẽ introduce async complexity, testing khó khăn hơn. Classification vốn là sync operation — việc thêm Job Application cũng nên sync.

- **Intermediate table** (Approach C): Quá phức tạp. Thêm bảng trung gian, poller, cleanup logic. Không cần thiết cho issue scope này.

# Key concepts to learn

1. **Callback / Strategy pattern**: Cho phép module A (Gmail) gọi module B (Recruitment) mà không cần import B. Container wire chúng lại.

2. **Idempotent persistence**: Dùng business key (gmail_message_id) để đảm bảo mỗi message chỉ tạo một JobApplication. Không cần transaction phức tạp.

3. **Seam design**: Ranh giới giữa classification và ingestion là `ClassificationResult` → `JobApplication`. Service ở recruitment biết về ClassificationResult (import từ gmail), nhưng ClassificationService không biết về JobApplication.

4. **Tabs vs Spaces**: Project dùng 4-space indent. Khi dùng apply_patch hoặc Python script để edit file, cần match chính xác whitespace.

5. **Alembic pattern**: Migration manual (không auto-generate) với upgrade/downgrade rõ ràng. Index và FK được tạo riêng.

# Common mistakes

1. **Import circularity**: ClassificationService cố gắng import JobApplicationService từ recruitment. Giải pháp: callback pattern + TYPE_CHECKING.

2. **ClassificationResult confusion**: Có hai class tên `ClassificationResult` — một ở `gmail.infrastructure.ai_classifier` (dùng cho kết quả classification), một ở `recruitment.domain.value_objects` (contract cho LLM). Không nhầm lẫn, dùng cái nào cho đúng mục đích.

3. **Không xử lý callback failure**: Nếu callback raise exception mà không catch, classification sẽ fail. Luôn wrap callback trong try/except.

4. **Idempotent check sai key**: Dùng `gmail_message_id` (unique string từ Gmail) chứ không phải `id` (UUID của EmailMessage). Mỗi email từ Gmail có một message ID duy nhất.

5. **Tabs vs Spaces**: Khi dùng file manipulation tools, dễ bị nhầm lẫn giữa tabs và spaces. Luôn kiểm tra với `cat -An` hoặc `repr()`.

# Small example

```python
# ClassificationService nhận callback từ container
service = ClassificationService(
    rules_classifier=rules,
    ai_classifier=ai,
    email_repo=repo,
    audit_logger=logger,
    settings=settings,
    session=session,
    on_application_created=job_app_service.create_from_classification,
)

# Khi confident recruitment email được classify:
# 1. _apply_classification gọi callback
# 2. job_app_service.create_from_classification chạy
# 3. Kiểm tra idempotent (get_by_gmail_message_id)
# 4. Derive source từ matched_signals
# 5. Tạo JobApplication với applicant identity phù hợp
# 6. Callback failure không ảnh hưởng tới classification

# Source derivation:
# - matched_signals=["referral"] → source="employee_referral"
# - matched_signals=["agency"] → source="agency"
# - matched_signals=["subject:ứng tuyển"] → source="direct"
```

# How to think about this next time

1. **Start with the seam**: Xác định rõ ranh giới giữa hai module. Input/output contract là gì? Ở đây là `(EmailMessage, ClassificationResult) → JobApplication`.

2. **Callback first, direct import later**: Khi cần bridge hai module, luôn dùng callback/strategy pattern trước. Nếu sau này thấy callback không đủ, mới chuyển sang direct import.

3. **Idempotent by default**: Service nào tạo record từ external input nên có idempotent check. Dùng business key (gmail_message_id) làm unique constraint logic.

4. **Try/except around bridge code**: Code bridge (nơi hai module gặp nhau) luôn wrap trong try/except. Module A không nên fail vì lỗi ở module B.

5. **Test the seam, not the internals**: Test integration test ở mức `ClassificationService.classify_batch()` với mock repository, không test internal method của `JobApplicationService` riêng lẻ.
