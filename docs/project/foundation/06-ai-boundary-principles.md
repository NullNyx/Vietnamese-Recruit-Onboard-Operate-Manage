# AI Boundary Principles

## Mục tiêu

Tài liệu này chốt ranh giới của AI trong Vroom HR. AI có vai trò hỗ trợ vận hành, nhưng không được trở thành nguồn quyết định hay nơi ghi dữ liệu nghiệp vụ.

---

## Nguyên tắc lõi

### 1. AI chỉ đọc và đề xuất, không tự ghi

- AI được phép đọc dữ liệu live qua Read-Tool
- AI được phép tạo Draft Action qua Draft-Tool
- AI không được phép viết vào database trực tiếp
- Không có write tool cho LLM

### 2. Source of truth là domain model, không phải AI

- Mọi trạng thái nghiệp vụ phải nằm trong database và domain layer
- AI chỉ làm lớp orchestration và hỗ trợ ra quyết định
- Nếu AI trả lời sai, hệ thống vẫn phải giữ trạng thái đúng

### 3. AI phải có context thật

AI chỉ hữu ích khi nó đọc được context thực từ hệ thống:

- candidate pipeline state
- onboarding progress
- employee data cá nhân
- interview queue
- review queue

Không dùng AI kiểu generic chatbot không hiểu workspace.

### 4. Draft Action phải review bởi con người

- Draft Tool chỉ sinh ra đề xuất có cấu trúc
- HR hoặc user phải confirm trước khi thực thi
- Confirm step gọi endpoint thật, không gọi LLM

### 5. AI không được phá audit

- Mọi action thật vẫn phải đi qua audit log
- AI không được tạo đường ghi tắt không audit
- Nếu Draft Action được confirm, action cuối cùng phải có trace

---

## Phân loại AI trong Vroom HR

### A. HR Assistant

Dành cho HR / admin.

Có thể:

- đọc candidate data
- tóm tắt CV
- tóm tắt review queue
- draft email interview / congratulations
- draft action cho HR confirm

Không được:

- accept candidate tự động
- gửi email tự động không confirm
- sửa dữ liệu nhân sự trực tiếp

### B. Employee Assistant

Dành cho Employee active.

Có thể:

- đọc data cá nhân
- tóm tắt trạng thái request
- hỗ trợ hỏi đáp về thông tin cá nhân

Không được:

- nhìn dữ liệu người khác
- tạo write action không confirm
- vượt boundary role

### C. Future autonomous agent

Hiện tại **out of scope**.

Nếu tương lai có autonomous agent, nó phải là một decision mới, có bảo vệ riêng, không được suy diễn từ assistant hiện tại.

---

## Read-Tool / Draft-Tool contract

### Read-Tool

- thực thi read thật
- trả dữ liệu live
- an toàn để gọi rộng
- có thể dùng cho count, get, list, summarize

### Draft-Tool

- không thực thi write
- chỉ trả proposal
- output phải có action type, parameters, preview
- không được chứa side effect

---

## Những điều cấm

- AI tự động accept / reject candidate
- AI tự động send email không qua confirm
- AI tự sửa employee data
- AI lưu state nghiệp vụ thay database
- AI thấy dữ liệu vượt role
- AI dùng RAG / embedding để thay cho source of truth trong core workflow

---

## Những điều nên làm

- dùng AI để giảm thời gian đọc hiểu
- dùng AI để draft các thao tác lặp lại
- dùng AI để tóm tắt state hiện tại
- dùng AI để hỗ trợ người dùng ra quyết định nhanh hơn

---

## Khi nào cần thêm tool mới

Chỉ thêm tool mới khi nó đáp ứng đủ:

1. Có dữ liệu live cần đọc
2. Có giá trị rõ trong workflow thật
3. Không phá boundary write
4. Có thể audit được
5. Không làm assistant thành autonomous agent ngầm

---

## Tóm tắt một câu

**AI trong Vroom HR là lớp hỗ trợ có context thật, có đề xuất thật, nhưng không có quyền hành động thay con người.**
