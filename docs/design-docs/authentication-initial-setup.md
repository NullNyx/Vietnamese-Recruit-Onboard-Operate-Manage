# Xác thực & Thiết lập Ban đầu

## Mục tiêu

Hệ thống được thiết kế cho **triển khai self-hosted**. Đây là **nền tảng HR nội bộ**,
không phải ứng dụng SaaS công khai.

Chỉ **HR/Admin** truy cập hệ thống. **Employee không có tài khoản và không thể đăng nhập.**

## Xác thực

### Thiết lập ban đầu

Khi hệ thống chạy lần đầu và chưa có administrator nào:

* Chuyển hướng mọi request tới **Initial Setup Wizard**.
* Cho phép tạo **tài khoản administrator đầu tiên**.
* Tài khoản đầu tiên được gán role `SUPER_ADMIN`.
* Sau khi thiết lập hoàn tất, endpoint setup bị vô hiệu hóa vĩnh viễn trừ khi
  chủ sở hữu hệ thống reset rõ ràng.

### Đăng nhập

Sau khi khởi tạo:

* Xác thực chỉ khả dụng qua trang **Login**.
* Người dùng xác thực bằng **username/email + mật khẩu**.
* Đăng ký công khai **không được hỗ trợ**.

### Quản lý người dùng

Chỉ `SUPER_ADMIN` mới tạo được system user bổ sung.

Các role đề xuất:

* `SUPER_ADMIN`
* `HR_ADMIN`
* `HR_STAFF`
* `READ_ONLY` (tùy chọn cho mở rộng sau này)

## Initial Setup Wizard

Luồng thiết lập đề xuất:

1. Tạo tài khoản administrator đầu tiên
2. Cấu hình thông tin công ty
3. Cấu hình AI provider (OpenAI, Gemini, endpoint tương thích OpenAI, Local LLM, hoặc Disabled)
4. Cấu hình mẫu hợp đồng mặc định (tùy chọn)
5. Import hoặc tạo employee records ban đầu (tùy chọn)
6. Kết thúc thiết lập và vào dashboard

## Quy tắc thiết kế

* Không đăng ký công khai.
* Không có tài khoản cho employee.
* HR/Admin là system actor duy nhất.
* Mỗi người dùng bổ sung phải do administrator tạo.
* Cấu hình AI provider là tùy chọn và có thể sửa sau.
* Hệ thống phải dùng được ngay cả khi chưa cấu hình AI provider.
