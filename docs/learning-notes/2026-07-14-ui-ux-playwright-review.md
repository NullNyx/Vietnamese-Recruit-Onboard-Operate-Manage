# Task

Grill và chốt định hướng cải thiện UI/UX cho Vroom HR, đặc biệt là trải nghiệm người dùng, responsive, accessibility và tiêu chí tránh AI Slop. Phạm vi đợt đầu là các pattern dùng chung của nền tảng, không redesign toàn bộ sản phẩm.

# What I changed

Không sửa code sản phẩm trong phiên này. Đã chạy một phiên grilling tuần tự và thống nhất các quyết định sau:

- Chọn chất lượng nền tảng dùng chung thay vì tối ưu riêng một module.
- Dùng một UX quality bar: người dùng phải biết mình đang ở đâu, dữ liệu có ý nghĩa gì, hành động tiếp theo là gì và phải làm gì khi dữ liệu trống hoặc có lỗi.
- Coi accessibility là release gate.
- Coi mobile là một cấu trúc riêng; 390px là viewport kiểm thử tối thiểu.
- Chuẩn hóa bốn trạng thái: loading, error, empty data và empty filter.
- Chỉ hiển thị notification badge khi có dữ liệu chưa đọc thật.
- Tiếng Việt là ngôn ngữ mặc định; dùng đúng thuật ngữ domain trong `CONTEXT.md`.
- Không hiển thị AI như lời hứa trang trí. AI surface phải có nhiệm vụ cụ thể, dữ liệu đầu vào rõ, kết quả kiểm chứng được và bước xác nhận của con người.
- Loại bỏ khối AI Assistant placeholder khỏi Employee Self-Service cho tới khi có năng lực thật.
- Dùng tên hiển thị trong breadcrumb, không dùng UUID.
- Không thêm gradient, glassmorphism, glow, animation hoặc card decoration để che vấn đề hierarchy và usability.
- Nghiệm thu bằng Playwright ở 1280px và 390px, kèm accessibility snapshot, console, screenshot và các trạng thái dữ liệu phù hợp.

Thứ tự triển khai đã chốt:

1. Dialog search và accessibility baseline.
2. Mobile responsive hierarchy.
3. Breadcrumb tên hiển thị và accessible name cho icon button.
4. Loading/error/empty/filter-empty patterns.
5. Notification state trung thực.
6. Loại bỏ AI placeholder.
7. Chuẩn hóa Tiếng Việt và thuật ngữ domain.
8. Chạy lại Playwright; chỉ sau đó mới cân nhắc visual polish.

# The real problem

Các luồng chính hiện đã dùng được, nhưng hệ thống làm người dùng mất tin tưởng ở những điểm nhỏ và lặp lại: mobile làm vỡ hierarchy, UUID làm mất định hướng, dialog thiếu thông tin cho screen reader, badge không có phản hồi quan sát được, trạng thái rỗng chưa phân biệt nguyên nhân, copy trộn Việt/Anh và AI placeholder chiếm chỗ nhưng không tạo giá trị.

Đây không phải chủ yếu là vấn đề thiếu animation hay thiếu widget. Vấn đề là giao diện chưa luôn trả lời được bốn câu hỏi: “Tôi đang ở đâu?”, “Dữ liệu này nghĩa là gì?”, “Tôi nên làm gì tiếp theo?” và “Nếu không có dữ liệu hoặc có lỗi thì sao?”.

# Why this solution

Chất lượng nền tảng dùng chung có đòn bẩy lớn hơn việc làm đẹp một màn hình đơn lẻ. Nếu dialog, header mobile, breadcrumb, trạng thái dữ liệu và button semantics được chuẩn hóa, mọi module HR và Employee Self-Service đều hưởng lợi.

Accessibility được đặt làm release gate vì lỗi tên dialog, focus hoặc icon button có thể khiến một nhóm người dùng không thể hoàn thành task, dù giao diện nhìn đẹp. Mobile được coi là tái cấu trúc theo ngữ cảnh thay vì chỉ co layout desktop, vì header Tuyển dụng đã chứng minh rằng việc co kích thước có thể phá hierarchy.

AI được coi là một capability có trách nhiệm, không phải visual motif. Một AI surface chỉ đáng tồn tại khi nó hỗ trợ một task thật, cho thấy dữ liệu và giới hạn của nó, đồng thời giữ human-in-the-loop theo domain model hiện tại.

# Production shape

## UX quality bar

Mỗi màn hình hoàn thiện phải giúp người dùng:

- Xác định vị trí hiện tại bằng tên có nghĩa.
- Hiểu dữ liệu và trạng thái hiện tại.
- Nhận ra một hành động chính.
- Biết cách phục hồi khi loading, error, empty data hoặc empty filter.
- Hoàn thành task bằng keyboard và assistive technology ở các control quan trọng.
- Có cùng trải nghiệm cốt lõi ở desktop 1280px và mobile 390px.

## Shared patterns

- **Responsive:** ở mobile, header có thể thành cột; action có thể xuống hàng riêng; bảng có thể chuyển thành list/card hoặc cuộn có chủ đích.
- **Dialog:** có title, description, accessible name, focus trap đúng và Escape; title/description có thể dùng `VisuallyHidden` nếu không cần hiện trực quan.
- **Button:** icon-only button có `aria-label`, tooltip ngắn và vùng bấm tối thiểu 40–44px.
- **Breadcrumb:** dùng tên hiển thị; UUID chỉ ở metadata hoặc vùng debug.
- **Data states:** empty data khác empty filter; error phải có hành động thử lại hoặc hướng dẫn tiếp theo.
- **Notification:** badge chỉ xuất hiện khi unread count được xác nhận; click phải mở nội dung hoặc trạng thái rõ ràng.
- **Copy:** Tiếng Việt mặc định, dùng `Candidate`, `Employee`, `Employee Self-Service`, `AI Assistant` đúng theo glossary khi cần giữ thuật ngữ chuẩn.
- **AI:** không hiển thị placeholder kiểu “sẽ được tích hợp”; chỉ hiển thị capability có task và kết quả thực tế, với xác nhận của HR/Employee khi có write proposal.

## Nghiệm thu bằng chứng

Mỗi thay đổi phải được kiểm tra lại bằng Playwright theo flow trước/sau, ở cả 1280px và 390px. Cần lưu hoặc ghi nhận screenshot cho vấn đề thị giác, đọc accessibility snapshot, kiểm tra keyboard/focus/Escape, và xem console để bảo đảm không tạo warning/error mới. Các màn hình có dữ liệu phải được kiểm tra cùng trạng thái loading, error và empty phù hợp.

# Other possible approaches

1. **Sửa tối thiểu theo từng lỗi:** chỉ sửa flex/grid ở mobile, thêm title cho dialog và đổi vài nhãn. Phù hợp khi cần phát hành nhanh với rủi ro thấp.
2. **Xây design system và pattern library trước:** tạo component/pattern dùng chung cho dialog, state, breadcrumb, button và responsive header rồi migrate từng module. Phù hợp khi sản phẩm sắp mở rộng nhiều module và muốn giảm nợ UX dài hạn.
3. **Redesign toàn bộ theo từng vai trò:** thiết kế lại IA riêng cho HR và Employee Self-Service, gom action theo task và làm lại visual language. Phù hợp khi cấu trúc navigation hiện tại không còn đáp ứng nhiều nhóm người dùng.
4. **Visual polish trước:** thêm animation, gradient, skeleton và motion để tăng cảm giác hiện đại. Chỉ phù hợp sau khi hierarchy, semantics, copy và states đã đúng.

# Why I did not choose those alternatives

Không chọn visual polish trước vì hiệu ứng không thể sửa heading bị bó hẹp, UUID trong breadcrumb, dialog thiếu title hay badge không có nội dung. Không chọn redesign toàn bộ ngay vì các P0/P1 có thể sửa bằng shared patterns với phạm vi nhỏ hơn và cần được đo lại trước khi thay đổi IA.

Không giới hạn ở các bản vá riêng lẻ vì cùng một lỗi sẽ lặp lại ở nhiều module. Tuy nhiên, cách triển khai thực tế vẫn nên bắt đầu từ các lỗi P0/P1 và dần trích xuất chúng thành pattern dùng chung; chưa cần dựng một design system lớn trước khi có bằng chứng từ các flow thật.

# Key concepts to learn

- **Responsive hierarchy:** mobile có thể cần cấu trúc khác desktop, không chỉ kích thước khác.
- **Accessible dialog:** tên, mô tả, focus management và Escape là một phần chức năng.
- **Semantic data states:** empty data và empty filter dẫn tới hành động tiếp theo khác nhau.
- **Progressive disclosure:** chỉ hiển thị capability người dùng có thể dùng ngay.
- **Human-in-the-loop:** AI Assistant hiện tại draft, không tự ghi dữ liệu.
- **Ubiquitous language:** Candidate, Employee, Employee Self-Service và AI Assistant không được dùng lẫn nghĩa.
- **Utility-first visual design:** hierarchy, typography và trạng thái quan trọng hơn trang trí.

# Common mistakes

- Co nguyên layout desktop xuống 390px thay vì đổi cấu trúc.
- Để UUID hoặc internal ID lọt vào breadcrumb.
- Dùng badge thông báo khi click không mở được nội dung.
- Gọi empty filter là “chưa có dữ liệu”.
- Dùng icon-only button không có accessible name.
- Đưa AI placeholder lên dashboard để lấp khoảng trống.
- Dịch rời rạc làm lẫn tiếng Việt và tiếng Anh trong cùng một flow.
- Thêm animation hoặc gradient trước khi kiểm tra hierarchy, keyboard và states.
- Chỉ kiểm tra giao diện bằng mắt ở desktop mà không đọc accessibility tree.

# Small example

Thay vì:

```text
Trang chủ / Nhân viên / abd76375-8303-4fad-a69f-89b2ffe9d63c
```

nên dùng:

```text
Trang chủ / Nhân viên / Employee QA Issue 199
```

Ở mobile, thay vì ép tất cả vào một hàng:

```text
[Tuyển dụng + subtitle + Inbox + Review]
```

nên tách hierarchy:

```text
Tuyển dụng
Quản lý ứng viên từ quy trình tuyển dụng
[Inbox] [Review]
```

Với danh sách không khớp bộ lọc:

```text
Không tìm thấy ứng viên phù hợp với bộ lọc hiện tại.
[Xóa bộ lọc]
```

# How to think about this next time

Bắt đầu từ task người dùng cần hoàn thành, không bắt đầu từ component hoặc hiệu ứng. Kiểm tra bốn câu hỏi về vị trí, ý nghĩa dữ liệu, hành động tiếp theo và phục hồi khi không có dữ liệu/lỗi. Sau đó kiểm tra cùng task ở desktop và mobile, đọc accessibility tree và console, rồi mới đánh giá màu sắc hoặc animation.

Khi thấy một AI surface, hỏi: capability đã hoạt động chưa, input là gì, output kiểm chứng thế nào, ai xác nhận và nếu AI sai thì người dùng phục hồi ra sao? Nếu chưa trả lời được, surface đó chưa nên xuất hiện trong production UI.
