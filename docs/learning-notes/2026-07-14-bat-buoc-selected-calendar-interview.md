# Task

Bắt buộc selected Calendar cho Interview (Issue 214)

# What I changed

## Backend

- **`CalendarEventSpec.calendar_id`**: Chuyển từ optional (`"primary"` default) thành required, không còn fallback implicit.
- **`CalendarPort` protocol**: `delete_event`, `get_event`, `list_events` yêu cầu `calendar_id` (bỏ default).
- **`CalendarAdapter`**: Xoá `calendar_id: str = "primary"` khỏi `delete_event` và `get_event`; cập nhật docstring.
- **`CalendarSyncService`**: `calendar_id` là required parameter trong `__init__`, không còn default.
- **`CandidateService`**:
  - Thêm `OrganizationGoogleConnectionRepository` dependency (`connection_repo`).
  - Thay `_assert_calendar_grant` (dùng HR `OAuthGrant`) bằng `_ensure_org_connection_active` (dùng org connection status).
  - Thay `_with_calendar_token` (dùng HR access token) bằng `_with_org_token` (dùng org access token + refresh).
  - Thêm `_resolve_org_calendar_id()` — trả về `selected_calendar_id` hoặc fail closed.
  - Thêm `_refresh_org_token()` — refresh token qua Google OAuth endpoint lưu connection.
  - `create_interview`, `cancel_interview`, `schedule_interview`, `reschedule_interview` dùng org calendar_id.
  - `Interview` entity được persist `calendar_id`.
- **`Interview.calendar_id`**: Thêm field mới (nullable) + migration 072.
- **`OrganizationGoogleConnectionResponse`** và **`GoogleWorkspaceConnectionResponse`**: Thêm `selected_calendar_id`.
- **Identity router**: Calendar list/select routes được đưa ra module level (không còn indented trong `callback_google_connection`). Xoá session leak (`get_db_session().__anext__()`), dùng `Depends(get_db_session)`.
- **Container**: Wire `connection_repo` vào `get_candidate_service`.

## Frontend

- **`GoogleWorkspaceConnection` type**: Thêm `selected_calendar_id`.
- **`admin.ts`**: Thêm `CalendarEntry`, `CalendarListResponse`, `getGoogleWorkspaceCalendars()`, `selectGoogleWorkspaceCalendar()`.
- **`oauth-config-form.tsx`**: Thêm calendar selection dropdown khi connection active; xoá option "dùng lịch chính".

## Tests

- Cập nhật `_make_spec` helpers thêm `calendar_id`.
- `FakeCalendarPort`: `delete_event`, `get_event`, `list_events` nhận `calendar_id` required.
- `build_calendar_harness`: Thêm fake `OrganizationGoogleConnectionRepository` với selected calendar.
- Cập nhật CalendarEventSpec, CalendarAdapter, CalendarSyncService tests cho signature mới.

# The real problem

Trước issue 214, mọi Calendar operation dùng `"primary"` mặc định mỗi khi không có selected calendar. Điều này sai ownership model (HR `primary` khác Organization calendar) và tạo implicit fallback dễ gây lỗi không rõ ràng. Khi Organization connection mới connect, chưa ai chọn calendar, HR có thể tạo interview mà không biết lịch sẽ ghi vào calendar nào.

# Why this solution

Fail-closed trên selected calendar là cách đơn giản nhất để buộc HR chọn calendar. Organization token ownership đã được triển khai ở issue 212 (connection singleton) — issue này chỉ cần wire nó vào scheduling flow. Các method mới (`_with_org_token`, `_resolve_org_calendar_id`) mirror pattern mà Gmail `SendService` đã dùng, tái sử dụng cùng `OrganizationGoogleConnectionRepository`.

# Production shape

```
HR mở Settings → Organization Google Connection
  → thấy "Lịch tuyển dụng: Chưa chọn"
  → click chọn calendar từ dropdown
  → PUT /api/auth/organization-google-connection/selected-calendar
  → selected_calendar_id lưu ở connection row

Khi tạo interview:
  1. CandidateService đọc connection singleton
  2. Check status == "connected" và selected_calendar_id != null
  3. Decrypt org access token (refresh nếu expired)
  4. Tạo Calendar event trên selected calendar
  5. Lưu calendar_id vào Interview row

Nếu chưa chọn calendar → 403 CALENDAR_GRANT_MISSING với message rõ ràng
```

# Other possible approaches

1. **Dùng `primary` của Organization Shared Account**: fallback về primary calendar của shared account thay vì fail closed. Dễ dùng hơn nhưng vi phạm ADR (Organization có thể có nhiều calendar, HR cần chọn đúng calendar cho recruitment).

2. **Dùng idempotent key mapping**: Tự động tạo một calendar cho recruitment (qua Calendar API) nếu chưa có selected calendar. Tiện lợi nhưng tạo side effect không mong muốn và khó revoke.

3. **Legacy dual-write**: Giữ HR grant flow song song với org token, cho HR chọn fallback behavior. Không clean, kéo dài technical debt, trái với "hard cutover" của parent issue.

# Why I did not choose those alternatives

- **Approach 1** (primary fallback): ADR-0002 chốt không dùng `primary`. HR có thể vô tình tạo interview trên calendar sai.
- **Approach 2** (auto-create calendar): Không rõ calendar name, visibility, ACL. Nếu Google API rate limit, interview creation sẽ fail ngẫu nhiên.
- **Approach 3** (dual-write): Parent issue #211 yêu cầu hard cutover, không dual-wire. Maintain hai codepath tăng complexity và testing surface.

# Key concepts to learn

- **Fail-closed vs fail-open trong security/config validation**: Khi thiếu config, fail sớm (trước khi gọi API) với message rõ hơn là fail muộn với lỗi bí ẩn.
- **Organization-owned token vs User-owned token**: Token thuộc Organization (singleton) giúp Calendar operation không phụ thuộc HR session lifetime.
- **Repository pattern cho singleton testing**: Dùng SimpleNamespace + duck typing trong test harness cho phép test org connection paths mà không cần real DB.

# Common mistakes

- **Để sót "primary" fallback trong error handler hoặc docstring**: Issue này có 3 lần phải grep lại toàn bộ codebase vì fallback ẩn trong method mới thêm.
- **Quên persist calendar_id lúc tạo Interview**: Calendar_id cần được lưu để update/delete sau này dùng đúng calendar, không fallback về "selected hiện tại".
- **Dùng `get_db_session().__anext__()` thay vì `Depends`**: Leak session, không được FastAPI lifecycle quản lý.

# Small example

```python
# Before (implicit primary fallback):
spec = CalendarEventSpec(summary="Interview", start=..., end=..., timezone=...)

# After (calendar_id required):
spec = CalendarEventSpec(summary="Interview", start=..., end=..., timezone=...,
                         calendar_id="recruitment@company.vn")
```

# How to think about this next time

Khi thiết kế integration với external API (Gmail, Calendar), luôn đặt câu hỏi: "Nếu config thiếu, behavior mong đợi là gì?" và "Cần token/user nào làm ownership?". Tránh fallback mặc định vì nó chỉ delayed error, không giải quyết vấn đề. Failing sớm với actionable error message là engineering best practice.
