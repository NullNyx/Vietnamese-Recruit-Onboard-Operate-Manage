# Task

Sửa các vấn đề phát hiện khi dùng Playwright verify Issue #211: route Payroll placeholder bị dynamic route `[id]` bắt nhầm, phát sinh request API `400`, thiếu favicon gây `404` trong console, và còn sót thuật ngữ tiếng Anh trên giao diện.

# What I changed

- Thêm static routes cho `/payroll/config`, `/payroll/allowances` và `/payroll/tax`.
- Các route này gọi `notFound()` ngay trên server, không chạy Payslip detail page và không gọi API Payslip.
- Thêm favicon SVG và khai báo trong metadata của root layout.
- Việt hóa các nhãn giao diện: `Gross` thành `Lương gộp`, `Net` thành `Lương thực nhận`, `Draft` thành `Bản nháp`, `publish` thành `phát hành`, và breadcrumb `payroll/tax` thành `Bảng lương/Thuế`.

# The real problem

Next.js ưu tiên dynamic route `/payroll/[id]` cho các URL placeholder chưa có page tĩnh. Vì vậy `config`, `allowances` và `tax` bị coi như Payslip ID. Client page gọi `fetchPayslip(id)`, backend trả lỗi `400`, sau đó mới redirect về `/payroll`.

Ngoài lỗi routing, tên trường dữ liệu kỹ thuật bị đưa thẳng vào UI. Điều này làm giao diện trộn tiếng Anh và tiếng Việt, không phù hợp với glossary và người dùng HR Việt Nam.

# Why this solution

Static route là boundary rõ ràng cho các URL đã retired. `notFound()` dừng flow trước khi mount client component, nên không có request API sai và người dùng nhận diện được route không tồn tại.

Các thuật ngữ kỹ thuật vẫn giữ nguyên trong biến, API và enum; chỉ lớp trình bày được dịch. Cách này không làm thay đổi contract backend nhưng thống nhất ngôn ngữ hiển thị.

# Production shape

- Route active `/payroll` vẫn phục vụ danh sách và CRUD Payslip.
- Route retired trả trang 404.
- `/attendance` và Employee Request/Payslip không bị thay đổi.
- Không có request `400` tới các API placeholder khi truy cập trực tiếp.
- Người dùng nhìn thấy thuật ngữ tiếng Việt nhất quán trên danh sách, form, chi tiết và breadcrumb.

# Other possible approaches

1. Redirect các route placeholder về `/payroll` bằng `redirect()`.
2. Thêm guard trong `/payroll/[id]` để từ chối các ID thuộc danh sách reserved words.
3. Dịch cả tên biến, enum và API field từ `gross_salary`, `net_salary`, `published` sang tiếng Việt.
4. Chỉ sửa navigation, không xử lý direct access hoặc thuật ngữ trong form/chi tiết.

# Why I did not choose those alternatives

- Redirect che giấu việc capability không tồn tại và vẫn trả response thành công trong một số thời điểm.
- Guard trong dynamic page dễ quên khi thêm placeholder mới và vẫn mount client boundary phức tạp hơn cần thiết.
- Đổi tên biến, enum và API field tạo breaking change không cần thiết; domain kỹ thuật có thể tiếng Anh còn presentation nên tiếng Việt.
- Chỉ sửa navigation không đáp ứng yêu cầu direct access và bỏ sót các nhãn trong form, bảng và chi tiết.

# Key concepts to learn

- Static route precedence so với dynamic route trong Next.js App Router.
- `notFound()` là server-side control flow, khác với redirect phía client.
- Navigation cleanup và direct URL access là hai acceptance criteria riêng.
- Presentation labels nên tách khỏi API vocabulary.

# Common mistakes

- Kiểm tra chỉ URL cuối cùng sau redirect mà bỏ qua request API trung gian.
- Dùng dynamic route cho domain có reserved path names.
- Đổi tên API enum chỉ để dịch UI.
- Dịch danh sách nhưng quên form, trang chi tiết hoặc breadcrumb.
- Xem mọi `404` là lỗi; route retired chủ động trả `404` là hành vi đúng.

# Small example

```tsx
const labelMap = {
  payroll: "Bảng lương",
  tax: "Thuế",
};

import { notFound } from "next/navigation";

export default function RetiredPage(): never {
  notFound();
}
```

# How to think about this next time

Khi một feature bị retire, kiểm tra đồng thời navigation, server route và client data-loading. Với mỗi URL cũ, xác định rõ nó phải trả `404`, redirect có chủ đích, hay vẫn giữ compatibility; không để dynamic route quyết định thay cho domain policy.

Khi sản phẩm dùng tiếng Việt, lập bảng ánh xạ thuật ngữ ở lớp UI ngay từ đầu. Giữ API vocabulary ổn định, nhưng không để các tên kỹ thuật như `Gross`, `Net`, `Draft` hay `publish` lọt vào giao diện người dùng.
