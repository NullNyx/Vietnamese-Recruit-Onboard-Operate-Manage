# Task

Hoàn thiện Calendar 410/412, relink và conflict UX (GH #216).

# What I changed

1. **CalendarEvent value object** (`value_objects.py`): thêm `start_at`, `end_at`, `timezone` fields để adapter/sync service có thể truyền thông tin thời gian từ Google Calendar API.

2. **Calendar adapter** (`calendar_adapter.py`): thêm `_parse_time_field()` và `_extract_timezone()` để trích xuất `start.dateTime`, `end.dateTime`, `timeZone` từ API response; cập nhật `_parse_event()` để gán các field mới vào `CalendarEvent`.

3. **Calendar sync service** (`calendar_sync_service.py`):
   - Sửa lỗi gọi `get_cursor()`, `clear_sync_token()`, `upsert_cursor()` không có `calendar_id` → giờ pass đúng `calendar_id` của selected calendar.
   - `_apply_changes()` giờ cập nhật `start_at`, `end_at`, `timezone` từ `CalendarEvent` vào `Interview` khi sync.

4. **Candidate service** (`candidate_service.py`):
   - **Keep Google**: `resolve_calendar_conflict` "keep_google" giờ áp dụng đầy đủ phiên bản Google vào Interview: thời gian (`start_at`, `end_at`, `timezone`), `remote_location`, `meeting_link`, `calendar_etag`, `calendar_updated`, và `status` (chỉ khi Google báo `cancelled` rõ ràng).
   - Audit ghi lại `applied_fields` khi resolve conflict.
   - `_capture_calendar_conflict` giờ lưu `start_at`, `end_at`, `timezone` trong `remote_snapshot`.
   - **needs_relink guard**: `reschedule_interview` chặn Calendar write khi `needs_relink=True`, raise `CalendarRelinkRequiredError` (409).

5. **Domain exceptions** (`exceptions.py`): thêm `CalendarRelinkRequiredError` (409, `CALENDAR_RELINK_REQUIRED`) để phân biệt lỗi business-state với validation error.

6. **DI container** (`container.py`): `get_calendar_sync_service` chuyển thành async, đọc `selected_calendar_id` từ `OrganizationGoogleConnection`, fail closed khi không có connection hoặc chưa chọn calendar.

7. **Tests**: cập nhật `FakeSyncCursorRepo` để khớp signature mới (có `calendar_id`), thêm `_FakeConnectionRepo` cho `test_candidate_service.py`, sửa fixture `schedule_service` để wire `connection_repo`, thêm test `CalendarRelinkRequiredError`.

# The real problem

Calendar sync, conflict resolution, và relink còn gap giữa contract ADR-0002 và implementation:

- `CalendarEvent` không mang được thông tin thời gian (`start`/`end`/`timezone`) → sync và "keep Google" không thể cập nhật Interview đúng.
- `CalendarSyncService` gọi cursor repo không pass `calendar_id` → sync trên sai calendar.
- Container hardcode `calendar_id="primary"` → vi phạm "không fallback primary".
- "Keep Google" chỉ update etag, không apply được time/location/status.
- Không có guard cho `needs_relink` → reschedule có thể âm thầm ghi event vào calendar sai.

# Why this solution

1. **CalendarEvent + time fields**: Mở rộng value object trực tiếp vì nó là frozen dataclass đơn giản; các field mới có default `None` nên backward-compatible với mọi call site hiện có.

2. **Pass `calendar_id` vào cursor**: Sửa signature call thay vì thay đổi interface repo — repo đã đúng, chỉ service gọi sai.

3. **Container async**: Đọc `selected_calendar_id` từ DB ở thời điểm resolve dependency. Fail closed khi không có calendar — không fallback `primary`.

4. **Keep Google full apply**: Áp dụng mọi field từ `remote_snapshot` vào Interview, không chỉ etag. Chỉ cancel Interview khi Google báo `status == "cancelled"` — đúng contract ADR "chỉ hủy khi có deletion rõ ràng".

5. **needs_relink guard + CalendarRelinkRequiredError**: Dùng domain exception (409) thay vì `ValueError` (422) để frontend phân biệt được business-state conflict với validation error.

# Production shape

```
Calendar 410 → clear sync_token + page_token cho selected calendar → bounded full sync
Calendar 412 → capture CalendarConflict (gồm start/end/tz) → HR resolve qua UI
Keep Google    → apply time/location/meet/status (chỉ cancel khi explicit) → audit
Overwrite Vroom → confirm + đọc ETag hiện tại + patch → retry 412 → conflict mới
needs_relink   → chặn Calendar write (409) → HR cancel + create replacement
Sync container → async, đọc selected_calendar_id, fail closed
```

# Other possible approaches

1. **CalendarEvent inherit từ Google API response verbatim**: Parse nguyên gốc response JSON thay vì map sang field riêng. Ưu: không cần mapping thủ công. Nhược: phụ thuộc chặt vào API shape, mọi consumer phải biết cấu trúc Google.

2. **Tách keep_google thành command riêng trong SyncService**: Thay vì để trong CandidateService, tạo một `ConflictResolutionService`. Ưu: tách biệt rõ ràng. Nhược: thêm một service class, tăng coupling giữa Candidate và Calendar.

3. **Dùng webhook/push notification thay vì incremental poll**: Ưu: real-time, không cần sync token/410 recovery. Nhược: cần public HTTPS endpoint, Pub/Sub infrastructure, phức tạp cho self-hosted.

# Why I did not choose those alternatives

- **Phương án 1**: `CalendarEvent` đã là value object domain, không nên leak raw API contract. Parse một lần ở adapter, consumer không cần biết Google shape.
- **Phương án 2**: `CandidateService` đã sở hữu conflict resolution từ trước (#157). Tách ra lúc này là refactor không mang giá trị, scope #216 là fix contract gap chứ không restructure module.
- **Phương án 3**: Webhook là future work đã được ghi nhận trong ADR-0002. Incremental poll với 410 recovery phù hợp mô hình self-hosted hiện tại.

# Key concepts to learn

- **Optimistic concurrency với ETag**: Google Calendar trả ETag cho mỗi event; `If-Match` + ETag đảm bảo write không ghi đè thay đổi của người khác. `412 Precondition Failed` = conflict → capture snapshot, tạm dừng, để HR quyết định.
- **Sync token và 410 Gone**: Google Calendar dùng sync token cho incremental sync. Token hết hạn (410) → phải clear token + page token, chạy bounded full sync, không được suy ra deletion từ absence.
- **Bounded full sync**: Khi mất sync token, không fetch toàn bộ calendar history. Chỉ fetch trong cửa sổ giới hạn (30 ngày trước, 90 ngày sau).
- **needs_relink vs lifecycle status**: `needs_relink` là cờ repair độc lập với `status` (scheduled/completed/cancelled). Nó báo hiệu binding Calendar đã mất — HR phải hủy và tạo replacement, không được patch event cũ.
- **Keep Google vs Overwrite Vroom**: Hai hướng resolve conflict khác nhau: keep Google = chấp nhận phiên bản Google vào local; overwrite = push local lên Google với ETag mới nhất.

# Common mistakes

- **Last-write-wins khi sync**: Tự động ghi đè Interview bằng dữ liệu từ Calendar mà không kiểm tra ETag hoặc conflict.
- **Suy ra deletion từ absence**: Event không xuất hiện trong bounded full sync → đánh dấu Interview cancelled. Sai — chỉ hủy khi Google trả status `cancelled` hoặc event bị deleted rõ ràng.
- **Retry 412 vô hạn hoặc tự động**: Nhận 412 rồi fetch ETag mới và retry ngay mà không qua HR.
- **Fallback primary calendar**: Khi chưa chọn selected calendar, dùng `primary` là sai — fail closed.
- **Nhầm needs_relink với lifecycle status**: Thêm `needs_relink` vào enum lifecycle status thay vì xem nó là cờ repair riêng.

# Small example

```python
# Keep Google — apply time/location/status from remote snapshot
if choice == "keep_google":
    interview.calendar_etag = remote_snapshot["etag"]
    interview.start_at = datetime.fromisoformat(remote_snapshot["start_at"])
    interview.end_at = datetime.fromisoformat(remote_snapshot["end_at"])
    interview.timezone = remote_snapshot["timezone"]
    interview.remote_location = remote_snapshot.get("location")
    interview.meeting_link = remote_snapshot.get("meet_link")
    if remote_snapshot.get("status") == "cancelled":
        interview.status = "cancelled"

# Needs relink guard
if interview.needs_relink:
    raise CalendarRelinkRequiredError()
```

# How to think about this next time

1. Khi thêm field vào API response model → kiểm tra xem có consumer nào cần field đó không (sync service, conflict resolution, UI). Nếu có, map một lần ở adapter, không để consumer tự parse.
2. Khi thêm guard/business rule → dùng domain exception với status code đúng (409 cho conflict, 422 cho validation). Không dùng `ValueError` vì nó bị map thành 422.
3. Khi sync token hết hạn (410) → clear CẢ sync_token VÀ page_token cho calendar cụ thể. Bounded full sync, không suy ra deletion.
4. Conflict resolution luôn là quyết định của HR: không retry tự động, không last-write-wins. Mỗi resolution được audit.
