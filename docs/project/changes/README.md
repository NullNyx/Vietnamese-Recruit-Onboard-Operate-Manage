# Changes — thư mục ghi nhận sửa đổi

## Mục đích

Thư mục này chứa các tài liệu về thay đổi cụ thể đang được thực hiện trên Vroom HR để align với foundation.

## Cấu trúc

Mỗi change nên ghi thành file riêng:

```
changes/
├── README.md                 → intro + hướng dẫn
├── 01-ux-redesign.md         → UX redesign plan
├── 02-onboarding-connection.md → kết nối backbone
└── ...
```

## Format mỗi file

Mỗi file change nên gồm:

- **Mục tiêu**: change này làm gì
- **Foundation liên quan**: file foundation nào làm base
- **Trạng thái hiện tại**: hiện tại code/vận hành thế nào
- **Trạng thái mong muốn**: cần đạt được gì
- **Các bước**: từng bước cụ thể
- **Rủi ro / Lưu ý**: cần chú ý gì khi làm

## Nguyên tắc

- Viết trước khi làm, đọc lại sau khi làm
- Nếu thay đổi tiến triển, cập nhật file thay vì tạo file mới
- Mỗi change là một hướng đi cụ thể, không phải brainstorm
