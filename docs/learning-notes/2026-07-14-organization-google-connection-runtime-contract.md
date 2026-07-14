# Task

Thiết lập runtime contract cho `Organization Google Connection` theo issue #212.

# What I changed

- Bổ sung bốn trạng thái hợp lệ: `disconnected`, `connected`, `degraded` và `reauthorization_required`.
- OAuth state chứa nonce, client ID và redirect URI; state được kiểm tra chữ ký, thời hạn, cấu hình và chỉ tiêu thụ một lần ở tầng repository.
- Kiểm tra đầy đủ required scopes, allowed workspace domain và redirect URI trước khi lưu credential.
- Reconnect giữ refresh token đã mã hóa khi Google không trả refresh token mới.
- Thêm cơ chế revoke legacy Google grants và chuyển connection sang `reauthorization_required`, đồng thời xóa credential cấp Organization.
- Xóa Gmail cursor còn gắn với các owner legacy trong cùng bước chuyển đổi.
- Mở route disconnect đúng cấp router và cập nhật response schema cho trạng thái `degraded`.

# The real problem

OAuth grant cũ gắn với HR nhưng Google mailbox và Calendar phải thuộc về một Organization duy nhất. Nếu callback chỉ kiểm tra token hợp lệ mà không ràng buộc state/configuration, callback replay hoặc callback từ OAuth client khác có thể ghi credential vào singleton. Nếu reconnect ghi đè refresh token bằng giá trị rỗng, worker sẽ mất khả năng refresh sau một consent thành công.

# Why this solution

Connection singleton là source of truth cho runtime. State được ký bằng JWT và hash lưu trong singleton; repository dùng row lock khi consume để hai worker không cùng chấp nhận một callback. Credential chỉ đi vào các trường encrypted, còn response chỉ trả trạng thái, email và cờ `has_secret`. Legacy grant bị revoke trước khi đọc status để không còn đường fallback âm thầm.

# Production shape

1. HR gọi authorize endpoint.
2. Service lấy OAuth config hiệu lực, kiểm tra redirect URI và tạo state có nonce/client ID/redirect URI.
3. Callback kiểm tra JWT, hash, nonce, thời hạn và config hiện tại, rồi atomically consume state.
4. Service đổi code lấy token, kiểm tra scope và workspace domain, mã hóa access token, refresh token và client secret rồi upsert singleton.
5. Runtime chỉ đọc trạng thái và credential của Organization singleton; HR identifier chỉ còn là metadata audit.
6. Legacy grant làm connection vào `reauthorization_required`; HR phải reconnect chủ động.

# Other possible approaches

1. **Lưu OAuth state trong Redis với TTL**: phù hợp khi nhiều replica cần state ngắn hạn và muốn tránh ghi state vào bảng connection.
2. **Dùng opaque random state lưu toàn bộ server-side**: phù hợp khi không muốn đưa client ID hoặc redirect URI vào JWT, đổi lại cần thêm bảng/session store và truy vấn lookup.
3. **Giữ legacy grant làm fallback trong thời gian chuyển tiếp**: phù hợp cho migration nhiều bước có rollback, nhưng không phù hợp với hard cutover vì tạo hai runtime owner.

# Why I did not choose those alternatives

Redis không phải dependency bắt buộc của identity callback và làm ownership của state tách khỏi connection singleton. Opaque state cần thêm persistence model trong khi JWT hiện có verifier và expiration chuẩn. Fallback legacy bị loại vì nó cho phép HR cũ tiếp tục sở hữu mailbox sau khi Organization contract đã có hiệu lực; release phải fail closed bằng `reauthorization_required`.

# Key concepts to learn

- OAuth authorization-code flow và offline refresh token.
- CSRF state: chữ ký, nonce, expiry và one-time consumption.
- Row-level locking để bảo vệ invariant trong nhiều worker.
- Encryption at rest khác với masking trong API response.
- Organization ownership khác với HR audit actor.

# Common mistakes

- Dùng `connected_by_user_id` để tìm credential hoặc cursor runtime.
- Xóa refresh token khi token response không có trường `refresh_token`.
- Kiểm tra domain từ email text mà bỏ qua verified `hd` claim.
- Xóa state sau khi đổi token nhưng không có atomic consume, khiến replay đồng thời lọt qua.
- Trả token hoặc client secret trong DTO, audit detail hoặc exception message.

# Small example

Google có thể trả:

```json
{
  "access_token": "new-access",
  "scope": "openid email https://www.googleapis.com/auth/gmail.readonly ..."
}
```

Nếu singleton đang giữ `refresh_token_enc` hợp lệ, callback dùng lại refresh token cũ, mã hóa access token mới và giữ connection `connected`. Nếu legacy grant còn valid, trước tiên grant bị revoke và connection chuyển `reauthorization_required`.

# How to think about this next time

Xác định owner thật trước khi thiết kế API. Sau đó liệt kê mọi credential, cursor và state có thể làm hệ thống quay về owner cũ. Mỗi item phải có một source of truth, một transition fail-closed và một test quan sát được từ public seam. Cuối cùng kiểm tra secrets ở cả storage, response, log và telemetry; mã hóa một nơi không đủ nếu một đường debug khác vẫn in plaintext.
