# Task

Sửa hierarchy responsive và copy trung thực cho màn Tuyển dụng và Employee Self-Service theo issue #222.

# What I changed

- Chuyển header Tuyển dụng và Hộp thư tuyển dụng thành layout dọc trên màn hình nhỏ, sau đó mới chuyển ngang từ breakpoint `sm`.
- Cho nhóm action và nút Làm mới rộng toàn bộ trên mobile để không bị ép hoặc chồng lên heading.
- Cho bộ lọc Hộp thư tuyển dụng xếp dọc và dùng toàn bộ chiều rộng trên mobile.
- Chuẩn hóa các nhãn `Hộp thư`, `Xem xét`, `Hộp thư tuyển dụng` và subtitle sang tiếng Việt rõ nghĩa hơn.
- Xóa thẻ quảng bá AI Assistant chưa có trên dashboard Employee Self-Service; cập nhật test để khóa hành vi này.

# The real problem

Header đang giả định đủ chiều ngang cho heading, subtitle và action group. Ở rộng 390px, giả định đó làm hierarchy bị nén. Dashboard Employee Self-Service cũng hiển thị một capability chỉ ở trạng thái hứa hẹn, khiến giao diện nói nhiều hơn khả năng thật.

# Why this solution

Dùng các breakpoint và flex direction có sẵn của Tailwind: mobile là trạng thái mặc định, `sm` mới đặt lại hàng ngang. Đây là thay đổi cục bộ, giữ nguyên flow dữ liệu và không thêm hiệu ứng để che lỗi bố cục. Capability chưa sẵn sàng được bỏ hẳn thay vì giữ một placeholder gây hiểu nhầm.

# Production shape

Ở viewport nhỏ, heading nằm trên action group; mỗi action là một nút dễ chạm trên một hàng riêng. Bộ lọc cũng xếp theo cột. Ở viewport lớn, các thành phần trở lại hàng ngang như trước. Dashboard không còn claim AI chưa hoạt động.

# Other possible approaches

1. Dùng CSS container query hoặc một component `PageHeader` dùng chung cho mọi màn hình. Phù hợp khi nhiều page có cùng lỗi và cần một contract layout thống nhất.
2. Giữ action group nằm ngang nhưng cho phép wrap bằng `flex-wrap`. Phù hợp khi muốn giữ chiều cao header thấp và các action ngắn, độc lập.
3. Giữ placeholder AI nhưng đổi thành nhãn “Sắp ra mắt”. Phù hợp với roadmap cần truyền thông rõ ràng, nhưng không phù hợp khi acceptance yêu cầu không quảng bá capability chưa có.

# Why I did not choose those alternatives

Container query tạo phạm vi thay đổi lớn hơn issue và chưa cần thiết cho hai header này. `flex-wrap` vẫn có thể tạo các dòng khó đoán, làm hierarchy thay đổi tùy độ dài copy. Placeholder “Sắp ra mắt” vẫn là quảng bá capability chưa hoạt động, trái với yêu cầu về tính trung thực.

# Key concepts to learn

- Mobile-first responsive layout.
- Flex direction và breakpoint trong Tailwind.
- Action reachability và touch target trên mobile.
- UI copy phải phản ánh capability production thực tế.

# Common mistakes

- Chỉ thu nhỏ font để chữa một header bị thiếu không gian.
- Dùng `truncate` cho heading hoặc nút rồi làm mất ngữ nghĩa.
- Để nhiều action có độ dài khác nhau trong một hàng cố định ở 390px.
- Giữ placeholder AI sau khi backend hoặc flow thật chưa sẵn sàng.

# Small example

```tsx
<div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
  <div className="min-w-0">...</div>
  <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
    <Button className="w-full sm:w-auto">Hộp thư</Button>
  </div>
</div>
```

# How to think about this next time

Bắt đầu bằng viewport nhỏ nhất và kiểm tra hierarchy trước khi thêm style. Tách rõ heading, action group và filter group; sau đó quyết định breakpoint dựa trên lúc các nhóm thực sự đủ chỗ. Với copy, hỏi capability có hoạt động end-to-end chưa; nếu chưa, bỏ claim khỏi surface chính thay vì dùng mỹ từ để che trạng thái thiếu.
