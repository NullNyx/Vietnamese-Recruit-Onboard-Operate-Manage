# Task
Gỡ các surface placeholder của Attendance và Payroll theo issue #217, chỉ quảng bá các capability đang hoạt động.

# What I changed
- Giữ lại `/attendance` cho danh sách Attendance Record và correction.
- Giữ lại `/admin/employee-requests`, `/payroll` và các view Employee Self-Service đang hoạt động.
- Gỡ các link placeholder khỏi admin navigation.
- Xóa page route placeholder để truy cập trực tiếp nhận 404 tự nhiên từ Next.js.
- Bổ sung regression test cho route đang giữ và route đã nghỉ.

# The real problem
Navigation đang tuyên bố nhiều capability chưa có implementation thật. Vì các page placeholder vẫn tồn tại, người dùng còn có thể truy cập trực tiếp dù đã không nên thấy chúng trên menu.

# Why this solution
Đồng bộ hai lớp: config navigation không còn quảng bá route placeholder, còn việc xóa `page.tsx` khiến route không tồn tại ở runtime. Các capability active không bị gom hoặc thay đổi nên giữ nguyên hành vi hiện có.

# Production shape
Deployment production chỉ expose các route Attendance và Payroll đã có page thật. Các URL placeholder trả 404 thay vì hiển thị thông báo “đang phát triển”.

# Other possible approaches
1. Giữ page và redirect placeholder về `/attendance` hoặc `/payroll`.
2. Giữ page nhưng render 404 thủ công bằng `notFound()`.

# Why I did not choose those alternatives
Redirect dễ che giấu URL cũ và tạo hành vi bất ngờ khi bookmark. `notFound()` vẫn để lại code placeholder và có nguy cơ route được quảng bá lại sau này. Xóa route là cách đơn giản nhất để thể hiện capability chưa thuộc production surface.

# Key concepts to learn
- Navigation config là product contract, không chỉ là UI decoration.
- Trong Next.js App Router, route tồn tại khi có `page.tsx`; xóa page sẽ loại route và cho phép framework trả 404.
- Regression test nên kiểm tra cả surface được giữ lại và surface bị loại bỏ.

# Common mistakes
- Chỉ xóa link menu nhưng quên route direct access.
- Xóa cả route active `/attendance` hoặc `/payroll` cùng thư mục placeholder.
- Test chỉ kiểm tra route mới có mặt mà không kiểm tra route cũ đã biến mất.

# Small example
```ts
const activeRoutes = ["/attendance", "/payroll"];
const retiredRoutes = ["/attendance/holidays", "/payroll/tax"];
```

# How to think about this next time
Bắt đầu từ acceptance criteria và lập bảng route: active hay placeholder, có trong navigation không, có page thật không. Sau đó thay đổi navigation và filesystem cùng một vertical slice, rồi test cả hai phía của quyết định.
