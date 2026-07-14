# Task
Chuyển Gmail ingestion sang cursor cấp Organization Google Connection cho issue #213.

# What I changed
- Thay `SyncCursor.user_id` bằng `organization_singleton_key`, bảo đảm một cursor cho một deployment.
- Đổi repository sang `get_cursor()`, `upsert_cursor(history_id)` và `clear_cursor()` không nhận HR/User.
- Poll incremental, baseline đầu tiên và recovery Gmail `404` dùng cursor Organization.
- Reconnect, disconnect và thu hồi legacy grant xóa cursor để poll kế tiếp tạo baseline mới.
- Thêm migration 071 để gộp cursor cũ theo user thành một cursor Organization.
- Bổ sung test baseline, recovery `404` và ownership migration.

# The real problem
Mailbox dùng chung thuộc Organization, nhưng history cursor cũ lại dùng user ID làm khóa. Khi HR đổi người hoặc reconnect, cursor cũ có thể khiến worker đọc sai lịch sử hoặc tạo competing ingestion stream.

# Why this solution
`CalendarSyncCursor` đã dùng singleton key làm invariant cấp Organization. Gmail cursor áp dụng cùng mô hình: repository không nhận identity của HR, còn `user_id` chỉ còn ở các bản ghi email và audit nơi cần actor/compatibility dữ liệu hiện hữu. Recovery `404` xóa cursor trước bounded full sync để không tiếp tục dùng history ID hết hạn.

# Production shape
Một hàng `sync_cursors` có `organization_singleton_key = "default"`. Poll đầu tiên chỉ gọi `get_latest_history_id` và lưu baseline. Poll sau gọi `history.list` từ cursor. Khi reconnect, disconnect hoặc legacy grant bị thu hồi, hàng cursor bị xóa. Khi Google trả `404`, cursor bị xóa rồi hệ thống chỉ đọc cửa sổ bounded theo cấu hình trước khi lưu history ID mới.

# Other possible approaches
1. Giữ `user_id` nhưng luôn lấy `connected_by_user_id` của Organization connection. Phù hợp khi mỗi mailbox thật sự thuộc từng HR riêng.
2. Gắn cursor trực tiếp với `organization_google_connections.id` bằng foreign key. Phù hợp khi một deployment có nhiều connection lịch sử hoặc cần audit ownership qua nhiều thế hệ.
3. Giữ hàng cursor và đặt một cột singleton key như hiện tại. Phù hợp với mô hình self-hosted một Organization và tương thích với Calendar cursor đang có.

# Why I did not choose those alternatives
Cách 1 vẫn để HR là nguồn ownership runtime và reconnect có thể để lại state cũ. Cách 2 mô hình hóa nhiều connection không tồn tại trong deployment hiện tại, làm tăng migration và lifecycle complexity. Cách 3 phù hợp với singleton invariant đã được dùng trong Calendar và không tạo fallback ownership.

# Key concepts to learn
- Organization singleton ownership khác với actor HR thực hiện thao tác.
- Gmail history ID là cursor tiến dần, không phải identity của người dùng.
- Baseline-only poll ngăn backfill ngầm sau connect/reconnect.
- `404` history recovery cần clear state trước bounded full sync.
- Unique constraint là invariant chống competing cursors.

# Common mistakes
- Truyền `connected_by_user_id` vào `get_cursor` hoặc `upsert_cursor`.
- Dùng historical import để cập nhật incremental cursor.
- Khi reconnect giữ cursor cũ rồi đọc tiếp mailbox account mới.
- Recovery `404` quét toàn bộ mailbox hoặc không giới hạn thời gian.
- Bỏ unique constraint và để nhiều worker tạo nhiều cursor.

# Small example
```python
cursor = await sync_cursor_repo.get_cursor()
if cursor is None:
    history_id = await gmail_adapter.get_latest_history_id(access_token)
    await sync_cursor_repo.upsert_cursor(history_id)
else:
    messages, history_id = await gmail_adapter.fetch_history(
        access_token=access_token,
        start_history_id=cursor.history_id,
    )
```

# How to think about this next time
Xác định owner của external state trước khi chọn khóa database. Nếu tài nguyên thuộc Organization singleton, actor HR chỉ nên đi vào audit và authorization; không được đi vào cursor, baseline hoặc recovery identity. Sau đó tìm module đã có cùng invariant để tái sử dụng mô hình thay vì tạo convention thứ hai.
