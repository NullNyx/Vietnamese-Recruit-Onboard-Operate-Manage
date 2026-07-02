# Quyết định

Các bản ghi quyết định giải thích tại sao các lựa chọn sản phẩm hoặc kiến trúc
quan trọng được đưa ra.

## Nguồn chân lý

- `docs/design-docs/` chứa hướng đi dạng nháp, khoảng trống, và tài liệu xem xét.
  Scope HR-only ở đó thắng từ ngữ cũ về employee trong working docs.
- `docs/decisions/` chỉ chứa lựa chọn đã chốt có tác động lâu dài.
- `CONTEXT.md` chứa thuật ngữ glossary chuẩn.

## Khi nào thêm ADR

Dùng format ADR từ `grill-with-docs` khi lựa chọn trở nên thực tế và khó đảo
ngược: tiêu đề ngắn, cộng 1–3 câu: bối cảnh, quyết định, lý do. Đánh số file
tuần tự (`0008-slug.md`, ...).

Thêm quyết định khi:

- Lựa chọn kỹ thuật đã chốt thay đổi.
- Quy tắc sản phẩm thay đổi có ý nghĩa.
- Yêu cầu validation được thêm, bỏ, hoặc giảm nhẹ.
- Feature có rủi ro cao chọn thiết kế này thay vì thiết kế kia.
- Hệ thống phân cấp nguồn chân lý thay đổi.

## Nguyên tắc

Nếu ghi chú còn đang tranh luận, giữ trong design docs. Nếu team phải code theo
nó trong tương lai gần, viết ADR.
