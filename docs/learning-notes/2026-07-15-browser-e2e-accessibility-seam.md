# Task

Triển khai issue #221: chuẩn hóa seam kiểm thử hành vi browser cho HR và Employee Account, đồng thời sửa search dialog, breadcrumb và icon-only controls.

# What I changed

- Search dialog có title và description semantics bằng nội dung visually hidden.
- Search input có accessible label, nhận focus khi mở và trả focus về control đã mở khi đóng bằng Escape.
- Breadcrumb nhận display name cho dynamic segment và không hiển thị UUID/internal identifier; fallback là “Chi tiết”.
- Bổ sung visible focus cho mobile menu, dialog close và breadcrumb links; icon decorative được đánh dấu `aria-hidden`.
- Mobile hamburger và các control dùng vùng bấm tối thiểu 40px.
- Thêm test hành vi cho dialog và breadcrumb, không kiểm tra private component implementation.
- Thêm Playwright config và role-based browser seam với project HR/Employee ở desktop/mobile; auth dùng storage state qua environment variables.

# The real problem

Dialog trước đó hoạt động bằng mắt nhưng không tự mô tả đầy đủ cho assistive technology và không có focus contract rõ ràng. Breadcrumb lấy trực tiếp pathname nên có thể làm lộ UUID. Một số control dựa vào icon hoặc kích thước nhỏ, khiến keyboard và touch navigation kém tin cậy.

# Why this solution

Dùng Radix dialog hiện có làm seam nền tảng, chỉ bổ sung semantics và focus lifecycle ở command bar. Breadcrumb vẫn là component dùng chung nhưng cho phép page cung cấp display name, trong khi fallback an toàn chặn internal identifier lọt ra UI. Đây là thay đổi nhỏ, giữ nguyên routing và navigation API.

# Production shape

Browser-facing behavior được cấu hình trong `frontend/playwright.config.ts` với bốn project HR/Employee × desktop/mobile. Chạy bằng `E2E_BASE_URL`, `E2E_HR_STORAGE_STATE` và `E2E_EMPLOYEE_STORAGE_STATE`; device profiles tương ứng desktop và mobile khoảng 390px. Flow kiểm tra search bằng nút/Ctrl-K, dialog name/description, focus input, Escape/focus return và named controls; screenshot/trace/console error được giữ làm evidence khi fail.

Focused Vitest đã chạy thành công. TypeScript hiện còn hai lỗi có sẵn trong `job-application-actions.test.tsx` do fixture thiếu `intent` và `has_cv`, không thuộc thay đổi này.

# Other possible approaches

1. Dùng `aria-labelledby`/`aria-describedby` thủ công trên từng dialog. Phù hợp khi dialog không dùng Radix hoặc cần kiểm soát ID đặc biệt.
2. Fetch display name trực tiếp trong `Breadcrumbs` theo từng route. Phù hợp khi có API read contract chung; hiện tại sẽ làm component navigation phụ thuộc nhiều service và tạo request lặp.
3. Dựng design-system wrapper cho mọi icon button và dialog. Phù hợp khi nhiều module mới cùng lúc cần migration; issue này chỉ cần sửa shared seams hiện có.

# Why I did not choose those alternatives

Giữ title/description trong Radix tree giúp focus trap và Escape tiếp tục do primitive quản lý. Không fetch trong breadcrumb vì layout không nên biết API detail của Employee, Candidate hay Payslip; caller có thể truyền display name khi đã có dữ liệu. Chưa dựng wrapper lớn vì sẽ mở rộng blast radius và không cần thiết để đạt acceptance criteria hiện tại.

# Key concepts to learn

- Accessible dialog cần name, description, focus entry, focus trap và focus return.
- Accessible name của icon-only control đến từ label, không phải hình dạng icon.
- Display name và internal identifier là hai lớp dữ liệu khác nhau.
- Touch target và visible focus là behavior contract, không chỉ là CSS polish.
- Test external behavior bền hơn test class name hoặc component internals.

# Common mistakes

- Thêm title nhìn thấy nhưng quên liên kết semantic với dialog.
- Tin rằng Radix luôn trả focus đúng khi dialog được điều khiển từ state bên ngoài.
- Hiển thị UUID vì “đó là giá trị có sẵn”.
- Dùng `aria-label` trên icon nhưng quên `aria-hidden` cho icon decorative.
- Chỉ test desktop hoặc chỉ test render, không test Escape/focus.

# Small example

```tsx
<DialogTitle className="sr-only">Tìm kiếm trang</DialogTitle>
<DialogDescription className="sr-only">
  Tìm và mở nhanh các trang mà bạn có quyền truy cập.
</DialogDescription>
<CommandInput aria-label="Tìm kiếm trang" />
```

# How to think about this next time

Bắt đầu từ flow người dùng: họ mở control nào, focus đi đâu, đọc được gì, thoát bằng cách nào và sau đó quay lại đâu. Với navigation, luôn phân biệt route identity với display identity. Sau đó mới chọn primitive hoặc class CSS và kiểm tra cùng behavior ở desktop/mobile.
