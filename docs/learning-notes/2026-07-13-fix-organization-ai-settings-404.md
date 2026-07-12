# Task

Sửa lỗi trang Organization AI Settings của issue #171 chỉ hiển thị `Not Found` vì API cấu hình AI trả HTTP 404.

# What I changed

- Đưa route `PUT /api/admin/organization/ai-config` ra đúng module scope để FastAPI đăng ký route.
- Thêm regression test kiểm tra cả GET và PUT core routes được đăng ký.
- Khởi động lại backend đang chạy code cũ và xác minh OpenAPI cùng giao diện thật.

# The real problem

Có hai lớp lỗi chồng lên nhau. Backend container đã khởi động trước khi route mới tồn tại nên process đang chạy không có cả GET route. Đồng thời source hiện tại đặt decorator và handler PUT bên trong handler test connection do sai indentation; kể cả restart thì PUT vẫn không được đăng ký.

# Why this solution

Route registration là behavior quan sát được và là seam nhỏ nhất bắt đúng lỗi indentation. Sửa scope của handler giữ nguyên contract API và không làm frontend phụ thuộc vào workaround. Restart backend là cần thiết để process nạp route table mới.

# Production shape

Production phải build/redeploy backend sau thay đổi route. Startup hoặc deployment smoke test nên kiểm tra OpenAPI/HTTP route quan trọng thay vì giả định bind-mounted source tự reload trong process production.

# Other possible approaches

1. Thêm một Next.js API route riêng để tự trả dữ liệu hoặc proxy sang path khác. Phù hợp khi frontend cần BFF contract độc lập với backend.
2. Bật auto-reload cho backend container. Phù hợp trong môi trường development để source bind mount được nạp lại nhanh.
3. Chỉ restart container mà không sửa source. Phù hợp nếu source route table hoàn toàn đúng và lỗi duy nhất là stale process.

# Why I did not choose those alternatives

- BFF workaround sẽ che lỗi backend và nhân đôi contract.
- Auto-reload không sửa route PUT bị nested; đồng thời không nên là yêu cầu production.
- Chỉ restart khôi phục GET nhưng để lại lỗi PUT, khiến flow lưu cấu hình tiếp tục thất bại.

# Key concepts to learn

- Decorator FastAPI chỉ đăng ký route khi statement decorator được thực thi lúc import module.
- Một function định nghĩa bên trong function khác không được thực thi cho tới khi function ngoài chạy; route decorator bên trong vì thế không xuất hiện trong route table lúc startup.
- Bind mount cập nhật file không đồng nghĩa process Python đã reload module.
- Regression test route table hữu ích cho lỗi registration; route-level tests vẫn cần cho authorization và response behavior.

# Common mistakes

- Chỉ nhìn source thấy decorator rồi kết luận endpoint đang tồn tại ở runtime.
- Restart để hết 404 nhưng không kiểm tra toàn bộ methods của cùng resource.
- Viết test service mà bỏ qua seam HTTP/route registration.
- Dùng auto-reload như giải pháp production.

# Small example

```python
@router.get("/items")
async def get_items():
    return []

    @router.put("/items")  # Sai: nested, không đăng ký lúc import
    async def put_items():
        return {}
```

Decorator PUT phải ở module scope, cùng cấp với decorator GET.

# How to think about this next time

Khi UI nhận 404, kiểm tra theo thứ tự: request path frontend → proxy/rewrite → runtime OpenAPI route table → source route registration → version/process đang chạy. Luôn phân biệt “source có route” với “runtime đã đăng ký route”, và khóa lỗi bằng test tại seam route trước khi sửa.
