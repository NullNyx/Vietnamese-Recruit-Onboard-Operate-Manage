# Task
Backfill Candidate calendar fields vào Interview (GH #215) — loại bỏ legacy calendar fields khỏi Candidate và chuyển hoàn toàn read/write path sang Interview entity.

# What I changed
- Tạo migration `074_backfill_interviews_drop_candidate_calendar_fields.py`:
  - Backfill Interview cho mọi Candidate còn legacy calendar fields chưa có Interview row.
  - Đánh dấu `needs_relink=True` cho tất cả Interview legacy (cả từ migration 046 và backfill mới) vì không thể xác minh quyền truy cập event qua Organization Shared Google Account trong migration.
  - Kiểm tra no-duplicate invariant: mỗi Candidate có legacy data phải có đúng một Interview tương ứng.
  - Xoá partial unique index `ix_candidates_calendar_event_id`.
  - Xoá ba cột legacy: `calendar_event_id`, `interview_start_at`, `interview_timezone`.
  - Downgrade tạo lại cột và backfill từ Interview (không gây mất dữ liệu).
- Xoá `calendar_event_id`, `interview_start_at`, `interview_timezone` khỏi `Candidate` entity.
- Thêm `calendar_id` vào `Interview` entity để lưu selected calendar được dùng khi tạo event.
- Cập nhật `CandidateService`:
  - `schedule_interview` → `_persist_interview_schedule` nhận và lưu `calendar_id` vào Interview.
  - `reschedule_interview`: không còn fallback đọc `candidate.calendar_event_id`; không còn ghi dual-write lên Candidate; lưu `calendar_id` vào Interview.
  - `_cancel_interview_event`: không còn fallback đọc `candidate.calendar_event_id`.
  - `_persist_interview_schedule`: không còn ghi dual-write lên Candidate; lưu `calendar_id`.
  - `create_interview`: lưu `calendar_id` vào Interview constructor.
- Cập nhật `CandidateRepository.create`: không còn `exclude` calendar fields.
- Cập nhật test harness (`_interview_support.py`): xoá legacy params khỏi `make_candidate` và `_SNAPSHOT_FIELDS`.
- Mở rộng migration test: kiểm tra `needs_relink=True` cho legacy Interview và xác nhận legacy columns đã bị xoá.

# The real problem
Legacy Candidate calendar fields (`calendar_event_id`, `interview_start_at`, `interview_timezone`) vẫn là source of truth thứ hai sau khi Interview entity đã được giới thiệu. Service code dual-write và dual-read tạo risk tạo duplicate event, mất đồng bộ, và làm migration rollback phức tạp.

# Why this solution
Migration một giai đoạn (một cutover duy nhất) thay vì giữ compatibility projection dài hạn. Điều này tránh dual-write, đơn giản hoá runtime path, và đảm bảo Interview là source of truth duy nhất cho lịch phỏng vấn.

# Production shape
- Migration chạy một lần, backfill Interview cho Candidate legacy, drop columns.
- Service code chỉ đọc/ghi Interview entity; không còn Candidate fallback.
- Interview mới luôn lưu `calendar_id` của selected calendar.
- Legacy event không xác minh được → `needs_relink=True` → HR repair qua UI.

# Other possible approaches
1. **Giữ compatibility projection lâu dài**: Candidate vẫn có calendar fields, service dual-write. Migration chỉ verify, không drop columns.
2. **Backfill + drop ngay mà không cần no-duplicate check**: Migration tạo Interview và drop columns mà không verify dữ liệu.

# Why I did not choose those alternatives
Phương án 1 kéo dài dual-write và tạo nguy cơ desync; ai đó có thể đọc từ Candidate mà bỏ qua Interview. Phương án 2 không an toàn — nếu có Candidate bị duplicate calendar_event_id hoặc thiếu Interview, migration sẽ drop dữ liệu không recover được. Kiểm tra no-duplicate invariant là mandatory.

# Key concepts to learn
- **Cutover migration** — một lần chuyển đổi dứt điểm thay vì dual-write.
- **needs_relink** — cờ độc lập với Interview lifecycle, cho biết event không truy cập được.
- **No-duplicate invariant** — mỗi Candidate có đúng một Interview mapping với legacy data.
- **Downgrade data-preserving** — rollback tạo lại cột và backfill từ Interview.

# Common mistakes
- Quên cập nhật test harness fixture khi xoá entity field.
- Migration 074 chạy `setval` trên UUID column (không có sequence).
- Để sót `candidate.calendar_event_id` fallback trong service code.
- Dual-write chỉ update Interview nhưng quên xoá Candidate field write.

# Small example
```python
# Trước (dual-write):
candidate.calendar_event_id = event_id
candidate = await self._candidate_repo.update(candidate)
interview.calendar_id = calendar_id
self._session.add(interview)

# Sau (Interview-only):
interview.calendar_id = calendar_id
self._session.add(interview)
```

# How to think about this next time
Khi chuyển đổi mô hình dữ liệu, xác định rõ:
1. Migration strategy: một cutover hay nhiều phase?
2. Runtime paths: còn fallback nào không?
3. Test fixtures: cần cập nhật mock/factory gì?
4. Rollback: downgrade có phục hồi dữ liệu không?
