# 04 — Human Flow Docs

## Mục tiêu

Bóc tách các luồng hoạt động hiện tại của sản phẩm thành bộ docs dễ đọc cho con người, để:

- review nhanh một feature đang hoạt động thế nào
- chỉnh sửa / refactor theo docs trước khi đụng code
- đồng bộ ngôn ngữ sản phẩm giữa team người và AI Agent
- giảm phụ thuộc vào việc phải đọc code mới hiểu luồng

Bộ docs này không thay thế source code, nhưng là lớp giải thích có thể đọc và chỉnh sửa được.

## Foundation liên quan

- `docs/project/foundation/01-product-statement.md`
- `docs/project/foundation/02-target-user-personas.md`
- `docs/project/foundation/03-user-journey.md`
- `docs/project/foundation/04-core-requirements.md`
- `docs/project/foundation/05-system-architecture-principles.md`
- `docs/project/foundation/07-ux-design-tenets.md`
- `docs/project/foundation/09-data-model-backbone.md`
- `docs/project/changes/00-file-lifecycle.md`

## Trạng thái hiện tại

- Các luồng chính đã có trong code và có thể suy ra từ router/service.
- Team đang giao việc cho AI Agents Coding task, nên chỉ agent thường nắm rõ flow cụ thể khi đọc code.
- Chưa có bộ docs riêng mô tả từng flow theo ngôn ngữ human-review.
- Người review hiện phải ghép thông tin từ code, ADR, và spec rời rạc.

## Trạng thái mong muốn

- Mỗi feature flow quan trọng có một file doc riêng, viết bằng tiếng Việt, dễ scan, dễ review.
- Doc phải mô tả:
  - trigger
  - actor
  - input / output
  - state chuyển đổi
  - happy path
  - error / edge cases
  - data touched
  - boundary / permission
- Docs đủ rõ để member không cần đọc code vẫn hiểu flow ở mức nghiệp vụ và trạng thái.
- Docs đủ chuẩn để AI Agent dùng làm reference khi thực hiện task.

## Phạm vi ưu tiên

1. Auth / login / setup self-host
2. Recruitment backbone flow
3. Onboarding flow
4. Employee / ESS flow
5. Attendance / payroll / request flow nếu còn active hoặc cần review
6. Integration flow như Gmail, Calendar, AI automation

## Cấu trúc đề xuất cho mỗi flow doc

- **Mục tiêu**
- **Trigger**
- **Actor**
- **Input / Output**
- **Luồng chính**
- **Trạng thái / chuyển trạng thái**
- **Ràng buộc / permission**
- **Lỗi / edge cases**
- **Data model liên quan**
- **Ghi chú cho review / implementation**

## Các bước triển khai

1. Chốt danh sách flow cần viết trước.
2. Tạo mỗi flow thành một file riêng trong `docs/project/` hoặc một subfolder phù hợp.
3. Viết theo format chuẩn, ngắn nhưng đủ chi tiết để review.
4. Cross-link tới `CONTEXT.md`, ADR, foundation, và change docs liên quan.
5. Khi code đổi, cập nhật flow doc cùng lúc để tránh drift.

## Rủi ro / lưu ý

- Không biến flow doc thành spec mơ hồ, phải bám sát code thật.
- Không viết quá rộng một file cho nhiều flow khác nhau.
- Không dùng thuật ngữ mới nếu `CONTEXT.md` đã chốt thuật ngữ khác.
- Khi feature bị obsolete/superseded, flow doc phải được cập nhật lifecycle.
- Nên giữ docs theo dạng review-friendly, tránh văn xuôi dài khó scan.
