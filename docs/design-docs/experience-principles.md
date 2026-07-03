# Experience Principles — Vroom HR

Mục tiêu: định nghĩa sản phẩm làm HR **cảm thấy thế nào**, không chỉ làm gì.
Đây không phải spec feature hay UI component, mà là kim chỉ nam cho mọi quyết
định thiết kế — từ copy trên button đến timing của animation, từ empty state
đến celebration khi hoàn tất case.

Allen Zhang: "Một sản phẩm tốt không chỉ tạo ra giá trị bằng công năng.
Nó còn tạo ra giá trị bằng cảm xúc." Vroom HR áp dụng tư duy đó: giảm thao
tác thủ công là baseline, tạo cảm giác "muốn mở lên" là lợi thế cạnh tranh.

## 1. Tính cách sản phẩm (Product Personality)

Nếu Vroom HR là một người, người đó là:

**Một trợ lý HR tận tâm, không phải một cỗ máy**

- Biết HR đang vội gì, cần gì trước khi họ kịp hỏi.
- Nói tiếng Việt tự nhiên, lịch sự, "chị" / "anh" với HR khi phù hợp.
- Không khoe kỹ thuật, không dùng từ "error", "fail", "invalid" với người dùng.

**Làm chủ công việc, không làm thay**

- Gợi ý, nhắc, tổng hợp — nhưng quyết định cuối cùng luôn ở HR.
- Khi HR quên, nhắc nhẹ, không phán xét.
- Khi HR xong, ghi nhận, không chỉ ghi log.

**Im lặng khi không cần nói**

- Không banner, không popup, không notification trừ khi thực sự cần.
- Tôn trọng sự tập trung của HR.

## 2. Tone of Voice

Văn phong thống nhất trên toàn bộ sản phẩm.

| Tình huống | Không dùng | Dùng thay |
|------------|------------|-----------|
| API error | "Error: not found" | "Không tìm thấy hồ sơ — chị kiểm tra lại mã nhé?" |
| Upload thành công | "File uploaded" | "Đã nhận file. Em đang đọc thông tin, chờ chị xíu." |
| AI không có kết quả | "Low confidence" | "Chưa đủ dữ liệu để gợi ý chắc chắn. Chị xem giúp em nhé?" |
| Empty state | "No data" | "Chưa có hồ sơ nào. Bắt đầu bằng cách tạo employee đầu tiên." |
| Case complete | "Status → completed" | (Animation nhẹ) "Chào mừng [tên] gia nhập công ty." |
| Overdue deadline | "Overdue" | "Đã quá hạn 3 ngày. Cần em nhắc ai không?" |
| Delete/archive | "Confirm delete?" | "Hành động này không thể hoàn tác. Chị chắc chắn muốn lưu trữ?" |
| Button disabled | (chỉ grey) | (tooltip) "Cần hoàn tất document trước" |

### Nguyên tắc copy

- Dùng "em" cho hệ thống, "chị/anh" cho HR.
- Câu ngắn, không liệt kê kỹ thuật.
- Cho giải pháp, không chỉ mô tả vấn đề.
- Feedback tích cực khi HR hoàn thành việc.

## 3. Hành trình cảm xúc (Emotional Journey)

Mỗi flow nghiệp vụ có một đường cong cảm xúc. Thiết kế phải biết chỗ nào HR
căng thẳng, chỗ nào nhẹ nhõm, chỗ nào cần động viên.

### 3.1 Flow: Tiếp nhận case onboarding mới

| Bước | Hành động | Cảm xúc HR | Ứng xử hệ thống |
|------|-----------|-----------|-----------------|
| 1 | Mở dashboard | Tò mò, hơi lo vì nhiều việc | Dashboard tĩnh lặng, số liệu rõ, "needs attention" nổi bật |
| 2 | Thấy case mới | Hơi choáng (checklist dài) | Progress bar + AI summary "Đã điền sẵn [n] mục" |
| 3 | AI tự động extract sau upload | Nhẹ nhõm | Suggestion xuất hiện sau <3s, HR không phải click thêm |
| 4 | Hoàn tất case | Thành tựu, hài lòng | Celebration + gợi ý tạo employee |
| 5 | Quay lại dashboard | Kiểm soát, tự tin | Dashboard cập nhật số liệu |

### 3.2 Flow: Deadline gần / quá hạn

| Bước | Hành động | Cảm xúc HR | Ứng xử hệ thống |
|------|-----------|-----------|-----------------|
| 1 | Thấy overdue badge | Căng thẳng, áy náy | Badge màu, message không phán xét |
| 2 | Mở case | Lo lắng | Timeline highlight đúng mục overdue + gợi ý hành động |
| 3 | Hoàn tất mục còn thiếu | Nhẹ nhõm | Trạng thái chuyển xanh |

### 3.3 Flow: AI draft → confirm

| Bước | Hành động | Cảm xúc HR | Ứng xử hệ thống |
|------|-----------|-----------|-----------------|
| 1 | Nhấn "Generate draft" | Kỳ vọng | Loading + "Em đang soạn thảo..." |
| 2 | Thấy preview | Ngạc nhiên, hoài nghi | Label rõ "AI gợi ý — chị xem và sửa nhé" |
| 3 | Sửa nội dung | Kiểm soát | Highlight chỗ đã sửa |
| 4 | Confirm | Hài lòng, tin tưởng | "Đã lưu! Nếu cần sửa thêm, chị cứ nói em nhé." |

## 4. Delight by design

Delight là spec, không phải "sau này thêm nếu rảnh".

### Khoảnh khắc "Aha!"

Lần đầu HR thấy AI gợi ý đúng → "Ồ, nó hiểu mình."
Thiết kế: suggestion hiện nhanh (<3s), đúng (>80%), không cần click thêm.
Nếu chưa đủ accuracy, fallback manual — không show suggestion sai.

Lần đầu HR hoàn tất case → "Mình làm được."
Thiết kế: animation nhẹ + một dòng "Chào mừng [tên] gia nhập công ty!".

### Micro-interaction

| Element | Hành vi | Mục đích |
|---------|---------|----------|
| Task toggle | Checkmark xuất hiện + gạch ngang mượt | Cảm giác "xong việc" ngay |
| Progress bar | Animation tràn mượt, primary → emerald | Thấy tiến triển |
| Upload | "Đã nhận" → "Đang xử lý" → "Xong" | Giảm lo lắng |
| AI processing | "Em đang đọc..." thay vì spinner | Cảm giác có người đang làm |
| Error | Copy thân thiện + "Thử lại" | Không panic |
| Empty state | Illustration + gợi ý hành động | Luôn có bước tiếp |

### Celebration mechanics

- **Case complete**: splash nhẹ "Chúc mừng, [tên] đã sẵn sàng!" (có thể tắt).
- **Cột mốc cá nhân**: "Bạn đã onboard 10 người trong tháng này!" (dashboard).
- **Chuỗi ngày làm việc**: 5 ngày liên tiếp → "Tuần này xử lý [n] hồ sơ,
  hiệu quả hơn tuần trước [x]%."

## 5. Emotional fallback (kỹ thuật lỗi)

Khi AI timeout, API fail, hoặc network lỗi — HR stress sẵn. Không làm tệ hơn.

| Tình huống | Phản ứng cảm xúc |
|-----------|-----------------|
| AI timeout | "AI đang bận — chị thử lại sau 5 giây nhé? Cứ nhập tay cũng được." |
| Upload fail | "File chưa lên được — em đã lưu tạm. Chị thử lại hoặc dùng file khác?" |
| Save conflict | "Có người vừa sửa hồ sơ này. Em tải lại để chị xem bản mới nhất nhé." |
| 404 from deep link | "Hồ sơ không còn ở đây — em đưa chị về dashboard nhé?" |

## 6. Design review checklist

Trước khi chốt bất kỳ màn hình nào, trả lời:

- [ ] HR sẽ cảm thấy thế nào khi nhìn màn này lần đầu?
- [ ] Cảm xúc đó có phù hợp với mục tiêu của màn không?
- [ ] Copy có dùng "em/chị" thay vì "error/user" không?
- [ ] Empty state có cho HR biết bước tiếp theo là gì không?
- [ ] Khi lỗi, HR có được cho giải pháp không, hay chỉ thấy mã lỗi?
- [ ] Khi hoàn tất, HR có được ghi nhận không?
- [ ] Loading state có copy thay vì spinner vô hồn không?

## 7. Next step

Sau review: tích hợp Emotional State vào flow-docs-end-to-end.md, thêm Experience
Criteria vào evaluation-acceptance-criteria.md, và cập nhật UX guideline trong
ux-flow-screen-map.md.
