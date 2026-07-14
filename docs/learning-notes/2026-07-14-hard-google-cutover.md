# Task
Hoàn tất các runtime path còn dùng Google credential theo HR/User trong Calendar và CV processing, phục vụ hard release gate của #218.

# What I changed
- Candidate service và Calendar adapter chỉ mô tả/đòi hỏi calendar được Organization chọn rõ ràng, không có fallback `primary`.
- Recruitment container bỏ wiring `OAuthService`/`OAuthGrantRepository` khỏi Calendar runtime.
- ARQ CV processing lấy access token từ Organization Google Connection thay vì OAuth grant của user trong email.
- Cập nhật integration fixture để phản ánh contract mới.

# The real problem
Một số caller đã migrate nhưng dependency wiring và worker vẫn giữ compatibility path cũ. Điều này khiến code có thể vô tình coi HR là credential owner, dù domain contract đã chuyển ownership về Organization.

# Why this solution
Seam chính nằm ở dependency container và worker boundary: Calendar/CV đều nhận credential từ singleton Organization Google Connection. User ID vẫn có thể tồn tại cho audit và dữ liệu lịch sử, nhưng không được dùng để tìm hoặc sở hữu Google token.

# Production shape
OAuth callback ghi token vào đúng một Organization Google Connection. Calendar commands đọc connection đó và selected calendar. Gmail/CV workers cũng đọc connection singleton; OAuth grant cũ không còn là nguồn credential runtime.

# Other possible approaches
1. Xóa toàn bộ bảng OAuth grant ngay trong một migration hard cutover; phù hợp khi mọi deployment đã được backup và không cần rollback dữ liệu cũ.
2. Giữ bảng grant chỉ làm historical record nhưng loại bỏ mọi repository call khỏi runtime; phù hợp khi cần rollback/audit migration mà vẫn muốn boundary runtime rõ ràng.

# Why I did not choose those alternatives
Không xóa bảng ngay vì migration/rollback gate vẫn cần dữ liệu lịch sử và khả năng chẩn đoán deployment cũ. Chọn cách thứ hai, đồng thời gỡ caller runtime, để hard cutover an toàn hơn mà không giữ compatibility behavior.

# Key concepts to learn
- Credential ownership khác với audit actor.
- Singleton Organization boundary không cần `user_id` để cách ly tenant.
- Compatibility code chỉ thực sự biến mất khi không còn caller runtime.
- Explicit configuration tốt hơn implicit provider default trong workflow có side effect.

# Common mistakes
- Dùng `connected_by_user_id` để lấy token.
- Cho Calendar tự fallback sang `primary`.
- Chỉ sửa service nhưng quên ARQ worker hoặc dependency container.
- Nhầm dữ liệu audit `user_id` với owner của credential.

# Small example
```python
connection = await connection_repo.get_singleton()
if connection is None or connection.status != "connected":
    raise CalendarGrantMissingError()
access_token = crypto.decrypt(connection.access_token_enc)
```

# How to think about this next time
Vẽ credential boundary trước khi sửa caller. Sau đó tìm toàn bộ nơi tạo adapter, refresh token, đọc cursor và chạy worker; mỗi điểm phải trả lời được: credential thuộc về ai, còn actor chỉ dùng cho audit ở đâu.
