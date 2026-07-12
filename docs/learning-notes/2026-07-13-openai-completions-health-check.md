# Task

Sửa health check của Organization AI Configuration để hỗ trợ provider dạng OpenAI completions không triển khai endpoint khám phá model, sau đó cấu hình Cline với model DeepSeek V4 Flash.

# What I changed

- Thay health check `GET /models` bằng request tối thiểu `POST /chat/completions` sử dụng đúng model đã cấu hình.
- Truyền model qua mọi health-check path: test candidate, Deployment key, enable capability và đổi credential source.
- Chuyển test mocks sang completions endpoint và thêm regression test kiểm tra path cùng model trong payload.
- Cấu hình Cline qua HR UI, chấp nhận data policy và bật độc lập AI Automation cùng AI Assistant.

# The real problem

OpenAI-compatible không có nghĩa provider bắt buộc hỗ trợ toàn bộ OpenAI API. Cline hỗ trợ completions contract nhưng không có `GET /models`. Health check cũ kiểm tra một capability tùy chọn không phải capability production thực sự sử dụng, nên báo provider unavailable dù completion hoạt động.

# Why this solution

Health check nên kiểm tra đúng hợp đồng runtime cần thiết. Request completion tối thiểu xác nhận đồng thời Base URL, credential, model và chat-completions compatibility. Nó loại bỏ false negative từ endpoint model discovery tùy chọn.

# Production shape

Mỗi lần test connection hoặc bật capability sẽ phát sinh một completion request nhỏ tới provider. Request có prompt cố định, `max_tokens=4`, không chứa dữ liệu Organization và dùng timeout 30 giây. Provider failure vẫn được chuyển thành lỗi an toàn, không persist candidate credential khi test thất bại.

# Other possible approaches

1. Thử `GET /models`, nếu 404 thì fallback sang `/chat/completions`. Phù hợp khi cần giữ discovery validation cho provider hỗ trợ đầy đủ OpenAI API.
2. Dùng endpoint cấu hình riêng cho health check. Phù hợp với hệ thống hỗ trợ nhiều provider contract khác nhau và operator biết endpoint health chuẩn.
3. Chỉ kiểm tra TCP/HTTP reachability của Base URL. Phù hợp cho readiness hạ tầng nhẹ, không cần xác nhận credential hoặc model.

# Why I did not choose those alternatives

- Fallback `/models` tạo request thừa và vẫn lấy endpoint tùy chọn làm đường chính.
- Health endpoint riêng làm tăng cấu hình và chưa cần thiết khi scope hiện tại chỉ cam kết OpenAI-compatible completions.
- Reachability không chứng minh key hợp lệ, model tồn tại hay completion contract dùng được.

# Key concepts to learn

- Compatibility thường là compatibility theo capability, không phải toàn bộ API surface.
- Health check có giá trị nhất khi đi qua đúng production contract.
- Candidate secret phải được test trước khi mã hóa/persist để rotation mang tính transactional.
- Health request không nên gửi dữ liệu domain thật.

# Common mistakes

- Giả định mọi OpenAI-compatible provider đều có `/models`.
- Chỉ test Base URL mà không test model.
- Dùng prompt chứa dữ liệu thật cho health check.
- Persist key trước rồi mới test connection.
- Quên cập nhật các health-check path phụ như enable capability hoặc Deployment key.

# Small example

```python
await client.post(
    f"{base_url}/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": model,
        "messages": [{"role": "user", "content": "Reply with OK."}],
        "max_tokens": 4,
        "stream": False,
    },
)
```

# How to think about this next time

Trước khi chọn health endpoint, xác định capability tối thiểu mà application thật sự yêu cầu. Viết contract test cho provider chỉ hỗ trợ capability đó, không vô tình yêu cầu endpoint tùy chọn. Sau đó truy vết mọi caller của health check để đảm bảo candidate test, activation và runtime gates dùng cùng một contract.
