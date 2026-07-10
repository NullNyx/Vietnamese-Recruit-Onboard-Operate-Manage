# Thiết kế lại Thiết lập lần đầu — Logic & UI/UX

## Mục tiêu

Giúp một deployment mới có thể sử dụng được qua một flow hướng dẫn duy nhất: xác định danh tính của Organization và tạo tài khoản HR đầu tiên. Flow phải ngắn gọn, an toàn khi thử lại và nhất quán với Heritage.

## Flow chuẩn

```text
GET /api/auth/setup-status
  ├─ setup_complete = true  → /login
  ├─ setup_complete = false → wizard bước 1
  └─ request thất bại       → trạng thái không khả dụng + thử lại

Bước 1: Tổ chức
  └─ organization_name (bắt buộc)

Bước 2: Tài khoản HR
  └─ name, email, password, password_confirmation

Xem lại / gửi
  └─ POST /api/auth/setup
       ├─ thành công → session đã xác thực → trạng thái thành công → dashboard HR
       ├─ đã thiết lập → /login + thông báo
       ├─ lỗi validation → lỗi theo field/form, giữ lại dữ liệu không nhạy cảm
       └─ lỗi tạm thời → thử lại, giữ lại name/email
```

Trình duyệt có thể hiển thị thành hai bước, nhưng request cuối cùng phải là một transaction ở backend. Việc tạo Organization và tài khoản HR đầu tiên phải cùng commit hoặc cùng rollback.

## Phạm vi

Thông tin bắt buộc trong Thiết lập lần đầu:

- Tên Organization
- Họ tên HR
- Email HR
- Mật khẩu HR và xác nhận mật khẩu

Giá trị mặc định/cấu hình sau:

- Timezone: `Asia/Ho_Chi_Minh`
- Mã số thuế, ngày nghỉ, allowed email domains: cấu hình sau trong Settings

Ngoài phạm vi:

- Cấu hình recruitment
- Checklist onboarding Employee
- Tích hợp email/calendar
- Thiết kế lại login ngoài các redirect cần tương thích

## Contract backend

`POST /api/auth/setup`

```json
{
  "organization_name": "Công ty ABC",
  "name": "Nguyễn Văn A",
  "email": "hr@abc.vn",
  "password": "••••••••••••",
  "password_confirmation": "••••••••••••"
}
```

Service phải:

1. Kiểm tra setup vẫn chưa hoàn tất.
2. Validate và chuẩn hóa tên Organization cùng email HR.
3. Enforce mật khẩu tối thiểu 12 ký tự ở server.
4. Tạo Organization singleton với timezone mặc định.
5. Tạo tài khoản HR đầu tiên.
6. Commit cả hai record một cách nguyên tử.
7. Chỉ cấp authenticated session sau khi commit thành công.

Khi có nhiều request setup đồng thời, chỉ một request được thành công. Các request còn lại nhận lỗi ổn định `setup already completed` và không được tạo thêm record.

`GET /api/auth/setup-status` phải tiếp tục cho phép gọi anonymous và chỉ trả về trạng thái setup đã hoàn tất hay chưa.

## Bố cục UI

### Desktop

Bố cục hai cột trên nền limestone ấm:

- Panel trái: logo Vroom HR, thông điệp ngắn, “Thiết lập lần đầu”, ba lợi ích ngắn; không có CTA cạnh tranh.
- Panel phải: card wizard, stepper, form và CTA chính.

### Mobile

Một cột. Thu gọn phần giới thiệu thành header nhỏ; giữ stepper và form hiển thị đầy đủ, không cần cuộn ngang.

### Quy tắc visual

- Dùng Fraunces cho heading trang/bước; Public Sans cho nội dung và control; Space Grotesk cho label.
- Chỉ dùng terracotta cho CTA chính và trạng thái bước hiện tại.
- Không dùng gradient; sử dụng limestone, ink, surface trắng và border nhẹ.
- Dùng các primitive shadcn và Tailwind hiện có; hỗ trợ cả light mode và dark mode.
- Nhãn CTA chính: “Tiếp tục” → “Xem lại thiết lập” → “Hoàn tất thiết lập”.

## Chi tiết tương tác

- CTA ở bước 1 bị disabled cho đến khi tên Organization, sau khi trim, không rỗng.
- Quay lại bước trước không xóa các giá trị không nhạy cảm đã nhập.
- Refresh sẽ reset wizard; tuyệt đối không persist mật khẩu hoặc xác nhận mật khẩu.
- Ô mật khẩu hiển thị “Ít nhất 12 ký tự” và gợi ý độ mạnh; ô xác nhận báo lỗi ngay khi không khớp.
- Submit hiển thị trạng thái pending và ngăn gửi trùng request.
- Khi submit thất bại, giữ lại tên Organization, họ tên HR và email; không xóa hai ô mật khẩu trừ khi policy yêu cầu.
- Khi thành công, hiển thị trạng thái thành công với tên Organization và một CTA duy nhất “Mở dashboard”. Không bắt đăng nhập lần hai.
- Nếu không kiểm tra được setup status, hiển thị trạng thái không khả dụng với nút “Thử lại”; không hiển thị form submit.

## Accessibility và responsive

- Mỗi input có label hiển thị rõ ràng và thông báo lỗi liên kết với input.
- Người dùng keyboard có thể chuyển bước và submit mà không cần pointer.
- Focus chuyển đến field lỗi đầu tiên sau validation thất bại và đến heading success sau khi hoàn tất.
- Loading và error state được thông báo qua live region phù hợp.
- Contrast dễ đọc ở cả hai theme; không dùng màu sắc làm tín hiệu duy nhất.

## Kịch bản kiểm thử

1. Deployment mới mở bước 1.
2. Deployment đã hoàn tất chuyển từ setup sang login.
3. Backend status thất bại hiển thị trạng thái retry.
4. Chuyển bước giữ lại dữ liệu không nhạy cảm.
5. Mật khẩu dưới 12 ký tự bị từ chối ở cả client và server.
6. Xác nhận mật khẩu không khớp sẽ chặn submit.
7. Submit thành công tạo đúng một Organization, một tài khoản HR và trả về session.
8. Hai submit đồng thời tạo một request thành công và một lỗi đã hoàn tất.
9. Transaction thất bại không để lại Organization hoặc tài khoản HR dở dang.
10. Success state đi đến dashboard mà không cần login lại.
