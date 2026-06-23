# Foundation — lớp nền móng cho sản phẩm

## Vị trí

Đây là thư mục gốc chứa những nguyên tắc, quyết định nền tảng của Vroom HR.
Mọi chi tiết triển khai, feature, module, UI, UX đều bám vào foundation này.

## Nội dung thư mục (đánh số theo thứ tự)

| File | Mô tả |
|------|-------|
| `overview.md` | intro + cấu trúc của foundation |
| `01-product-statement.md` | câu chuyện sản phẩm, backbone, giá trị lõi |
| `02-target-user-personas.md` | 3 nhóm người dùng: HR / Employee / Owner |
| `03-user-journey.md` | hành trình chính: HR path, Employee path, Owner path |
| `04-core-requirements.md` | functional + non-functional, out of scope |
| `05-system-architecture-principles.md` | domain-first, module boundaries, audit, security |
| `06-ai-boundary-principles.md` | read-tool / draft-tool, không tự ghi |
| `07-ux-design-tenets.md` | status first, next action, queue, trust visible |
| `08-deployment-trust-security-principles.md` | self-host, one company, control, security |

## Định nghĩa "lớp nền móng"

Foundation là **những thứ không thay đổi theo sprint**:

- tại sao sản phẩm tồn tại
- ai sử dụng
- câu chuyện chính là gì
- nguyên tắc thiết kế hệ thống
- nguyên tắc AI
- nguyên tắc trải nghiệm người dùng
- open-source stance
- deployment model
- data ownership

Nếu một quyết định mới mâu thuẫn với foundation, cần quay lại hỏi:

- foundation có sai không
- hay quyết định mới cần điều chỉnh

## Cách dùng

Khi làm bất kỳ thứ gì (viết code, thiết kế UI, viết docs, bàn feature), kiểm tra với foundation trước:

- có khớp backbone không
- có đi đúng user journey không
- có vi phạm AI boundary không
- có add audit không
- có giữ open-source direction không

## Nguyên tắc ghi chép ở đây

- chỉ ghi khi quyết định đã chín
- không ghi spec đang bàn dở
- nếu cần sửa foundation, ghi rõ lý do và timestamp
