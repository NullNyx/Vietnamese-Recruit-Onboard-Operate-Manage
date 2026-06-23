# File Lifecycle Policy

## Vấn đề

Theo thời gian, docs cũ có thể:

- hết giá trị
- bị thay thế bởi file khác
- chứa thông tin lỗi thời
- gây nhiễu context nếu không xử lý

Cần một quy tắc rõ để xử lý.

---

## Trạng thái file

Mỗi file trong thư mục docs/project/ hoặc docs/project/changes/ có thể ở một trong các trạng thái sau:

### 1. Active

- File đang có giá trị hiện tại
- Được tham chiếu trong quyết định
- Có thể cập nhật nếu cần

### 2. Superseded

- File đã bị thay thế bởi file khác
- Nội dung vẫn còn tham khảo nhưng không còn dùng làm căn cứ
- Ghi chú superseded ở đầu file + link đến file mới

### 3. Obsolete

- File hết giá trị
- Không còn đúng với hệ thống hiện tại
- Đánh dấu OBSOLETE ở đầu file, không xóa ngay

### 4. Removed

- File đã xóa khỏi thư mục
- Chỉ xóa khi chắc chắn không ai tham chiếu

---

## Quy tắc xử lý

### Khi một file hết giá trị

1. Kiểm tra xem có file nào đang thay thế không
2. Nếu có → gắn trạng thái **superseded** + link
3. Nếu không → gắn trạng thái **obsolete**
4. Không xóa file ngay (trừ khi chắc chắn 100%)

### Khi có file mới thay thế một file cũ

- Gắn **superseded** vào file cũ
- File mới ghi rõ "This document supersedes [file cũ]"

### Khi dọn dẹp định kỳ

- Rà các file superseded và obsolete
- Nếu không ai tham chiếu trong 30 ngày, có thể remove
- Remove thì ghi vào git commit message để trace

---

## Áp dụng cho file gap analysis hiện tại

File `docs/project/05-gap-analysis.md` là **active**.

- Nếu sau này gap được xử lý hết, file này chuyển sang **obsolete**
- Nếu có gap analysis mới chi tiết hơn thay thế, file này chuyển sang **superseded**
- Nếu vừa xử lý xong một số gap nhưng còn gap khác, cập nhật nội dung file, không đổi trạng thái

---

## Format header cho file superseded / obsolete

### Superseded

```
<!-- FILE STATUS: SUPERSEDED -->
<!-- Superseded by: docs/project/05-gap-analysis-v2.md -->
<!-- Date: 2026-06-22 -->
```

### Obsolete

```
<!-- FILE STATUS: OBSOLETE -->
<!-- Reason: All gaps in this analysis have been resolved as of 2026-06-22 -->
```

---

## Tóm tắt

| Trạng thái | Ý nghĩa | Giữ file? | Có thể dùng? |
|------------|---------|-----------|--------------|
| Active | Đang giá trị | ✅ | ✅ |
| Superseded | Có file thay thế | ✅ | ⚠️ (tham khảo) |
| Obsolete | Hết giá trị | ✅ | ❌ |
| Removed | Đã xóa | ❌ | ❌ |
