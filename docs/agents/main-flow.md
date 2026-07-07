# Main flow

Luồng vận hành chuẩn cho agent trong repo này.
Mọi nội dung điều phối, task, PRD, issue, review, và comment viết bằng tiếng Việt,
trừ thuật ngữ kỹ thuật tiếng Anh đã là canonical term.

## Mục tiêu

Đi theo nguyên lý:

`idea -> grill -> decide prototype? -> PRD -> issues -> implement -> review -> ship`

## Luồng chính

1. Có ý tưởng hoặc slice mới:
   - dùng `grill-with-docs` nếu có codebase.
   - dùng `grill-me` nếu chưa có codebase.
2. Nếu câu hỏi cần đáp án chạy được:
   - đi qua `handoff` ra session mới.
   - dùng `prototype` để kiểm thử giả thuyết.
   - `handoff` ngược lại với kết quả.
3. Nếu work sẽ đi nhiều session:
   - trước khi mở PRD hoặc issue mới, kiểm xem ADR đó đã có downstream artifact chưa
     (docs/design, PRD, issue, implement).
   - nếu artifact đã đủ và ADR đã được chốt, **không tạo task mới** chỉ để lặp lại
     việc đã xong; đánh dấu task liên quan là done/closed nếu task đó đang theo dõi
     cùng scope.
   - `to-prd` để chốt PRD.
   - `to-issues` để tách PRD thành Jira Tasks độc lập trên `KAN`.
   - `implement` từng issue trong session mới.
4. Nếu work đủ nhỏ:
   - vào thẳng `implement` trong cùng context.
5. `implement` phải:
   - đi test-first qua `tdd`.
   - kết thúc bằng `code-review`.
6. Sau khi PR mở:
   - self-review lại diff.
   - đối chiếu Jira task và ADR.
   - sửa theo review feedback.
   - chỉ merge khi review pass và AC khớp.

## On-ramp

- Bug / regression / flaky path -> `diagnosing-bugs`.
- Issue thô từ ngoài vào -> `triage` rồi publish Jira Task nếu cần.
- Việc giữ codebase tốt hơn -> `improve-codebase-architecture`.

## Context hygiene

- Giữ một context không đứt từ `grill-with-docs` đến `to-issues`.
- Không compact giữa chừng nếu còn đang chốt thinking.
- Sau `to-issues`, mỗi issue dùng session mới.
- Dùng `handoff` khi cần tách session nhưng vẫn giữ paper trail.

## Quy tắc dùng skill

- `domain-modeling`: khi tên gọi domain mơ hồ hoặc trùng nghĩa.
- `codebase-design`: khi cần thiết kế shape module / seam / interface.
- `research`: khi cần đọc nguồn chính rồi quay lại flow chính.
- `prototype`: chỉ để trả lời một câu hỏi thiết kế cụ thể, không để ship.
- `code-review`: khi cần review branch/PR theo Standards + Spec.
