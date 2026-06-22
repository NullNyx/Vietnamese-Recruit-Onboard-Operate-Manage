# UX Design Tenets

## Mục tiêu

Tài liệu này chốt nguyên tắc trải nghiệm người dùng cho Vroom HR. Mục tiêu không phải “đẹp” theo cảm tính, mà là làm cho user hiểu nhanh, làm việc nhanh, ít sai, và tin hệ thống.

---

## 1. Status first

Mỗi màn hình phải trả lời ngay:

- tôi đang ở đâu
- trạng thái hiện tại là gì
- cái gì đang chờ tôi

UX tốt trong Vroom HR là UX cho user thấy state trước, rồi mới cho họ thao tác.

---

## 2. Next action first

Sau khi biết state, user phải biết:

- bước tiếp theo là gì
- ai là người chịu trách nhiệm
- action nào an toàn để làm ngay

Không để user tự suy luận quá nhiều.

---

## 3. Queue over clutter

Thay vì nhồi mọi thứ lên một trang:

- ưu tiên review queue
- ưu tiên timeline
- ưu tiên pending items
- ưu tiên action cards

Người dùng HR cần thấy việc cần xử lý, không phải một đống danh sách vô định.

---

## 4. Context-rich detail view

Khi mở một record (Candidate, Employee, Request):

- thấy summary trước
- thấy state timeline
- thấy notes / audit / related objects
- thấy action được phép làm

Detail view phải trả lời câu hỏi: “Người này đang ở đâu trong journey?”

---

## 5. HR UX và Employee UX phải khác nhau

### HR UX

- nhiều thông tin hơn
- nhiều action hơn
- tập trung vào review / approve / schedule / audit

### Employee UX

- đơn giản hơn
- ít dữ liệu hơn
- ưu tiên self-service và clarity

Không copy nguyên một UI cho cả hai.

---

## 6. Read before write

Trong ESS và cả HR:

- đọc thông tin trước
- sau đó mới tạo action
- confirm rõ trước khi write

Điều này giảm sai và tăng trust.

---

## 7. Reduce cognitive load

- câu chữ ngắn
- trạng thái rõ
- tránh thuật ngữ nội bộ quá sâu ở mặt ngoài
- không bắt user hiểu kiến trúc

Nếu user phải nhớ quá nhiều, UI đang thất bại.

---

## 8. One task, one focus

Một màn hình nên có một mục đích chính.

Ví dụ:

- Candidate detail: review và decide
- Onboarding detail: complete checklist
- ESS page: xem và request

Không nên biến một màn hình thành mọi thứ cùng lúc.

---

## 9. Make trust visible

- audit visible
- trạng thái visible
- ai làm gì visible
- nguồn dữ liệu rõ
- action nguy hiểm phải có confirm

Trust không chỉ nằm ở backend. UI phải phản ánh trust.

---

## 10. State transitions should feel natural

UI phải cho user cảm giác chuyển trạng thái là hợp lý:

- candidate accepted → onboarding mở ra
- onboarding complete → employee active
- request approved → status đổi ngay và rõ

Không làm user cảm thấy “tôi bấm rồi nhưng không biết chuyện gì xảy ra”.

---

## 11. Small surface, strong hierarchy

- không card-in-card không cần thiết
- không nhồi quá nhiều decoration
- typography và spacing phải tạo hierarchy rõ
- primary action phải nổi bật nhưng không phô

---

## 12. Error states phải hữu ích

Lỗi không chỉ là “failed”.
Nó phải nói rõ:

- vấn đề là gì
- user cần làm gì tiếp theo
- ai xử lý lỗi này

---

## 13. AI should feel assistive, not invasive

AI trong UI phải:

- giúp tóm tắt
- giúp draft
- giúp gợi ý bước tiếp theo

Không nên:

- làm náo loạn UI
- chiếm quá nhiều không gian
- giả vờ biết tất cả

---

## 14. Vietnamese-first, English terms preserved

- giao diện dùng tiếng Việt
- thuật ngữ domain tiếng Anh giữ nguyên khi là canonical term
- text phải tự nhiên với người dùng Việt Nam

---

## Những điều cần tránh

- dashboard đầy icon nhưng thiếu state
- form dài không cần thiết
- hide important actions trong menu sâu
- AI bubble quá lố
- UX giống admin tool nội bộ thiếu chiều sâu

---

## Một câu nhớ nhanh

**UX của Vroom HR phải làm user thấy rõ trạng thái, biết bước tiếp theo, và tin rằng hệ thống đang hiểu đúng journey của họ.**
