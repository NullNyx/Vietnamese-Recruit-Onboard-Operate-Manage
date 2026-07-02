# Nhãn Triage

Các skill nói bằng năm vai trò triage chuẩn. File này ánh xạ vai trò đó thành
chuỗi nhãn Jira thực tế dùng trong project `KAN`.

| Nhãn trong skill | Nhãn Jira | Ý nghĩa |
|---|---|---|
| `needs-triage` | `needs-triage` | Maintainer cần đánh giá issue này |
| `needs-info` | `needs-info` | Đang đợi reporter cung cấp thêm thông tin |
| `ready-for-agent` | `ready-for-agent` | Đã spec đầy đủ, sẵn sàng cho agent AFK |
| `ready-for-human` | `ready-for-human` | Cần con người thực hiện |
| `wontfix` | `wontfix` | Sẽ không xử lý |

Khi skill nhắc đến vai trò (ví dụ "gán nhãn AFK-ready"), áp dụng chuỗi nhãn Jira
tương ứng từ bảng này.

Sửa cột bên phải nếu từ vựng thực tế bạn dùng khác.
