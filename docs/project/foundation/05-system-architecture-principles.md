# System Architecture Principles

## Mục tiêu

Tài liệu này chốt các nguyên tắc kiến trúc nền tảng để Vroom HR giữ được backbone rõ, module boundaries rõ, và dễ mở rộng mà không mất kiểm soát.

---

## 1. Domain-first, không UI-first

- Hệ thống phải phản ánh domain thật
- UI chỉ là lớp hiển thị của domain
- Nếu model domain sai, UI đẹp đến đâu cũng sai

Ví dụ:

- Candidate → Employee là một domain transition, không phải đổi tên record
- accepted là state trigger cho onboarding, không phải chỉ status string

---

## 2. Module boundaries rõ

Mỗi module phải có trách nhiệm riêng:

- Identity / auth
- Recruitment
- Onboarding
- Employee
- ESS
- Attendance
- Payroll
- Assistant

Nguyên tắc:

- module không tự ý “chạm” vào business logic của module khác
- giao tiếp qua service / event / contract rõ ràng
- assistant chỉ orchestration, không chứa business logic lõi

---

## 3. Async-first backend

- DB operations dùng AsyncSession
- background job dùng queue / worker
- request path phải rõ ràng giữa sync và async
- thao tác nặng không chặn user flow

---

## 4. Source of truth là database + domain layer

- trạng thái thật luôn nằm trong DB
- AI không giữ state nghiệp vụ
- cache chỉ là cache
- event chỉ là signal, không phải source of truth

---

## 5. State transition phải atomic

Những bước quan trọng trong backbone phải atomic:

- interview scheduling
- accept → onboarding trigger
- onboarding complete → employee active

Nếu một phần fail, hệ thống phải rollback hoặc không đổi state.

---

## 6. Cross-module communication bằng event + contract

Khi một module cần báo cho module khác:

- dùng domain event
- consumer rõ ràng
- payload rõ ràng
- không coupling qua state ngầm

Ví dụ:

- accepted event → onboarding consumer

---

## 7. Audit by design

- mọi change quan trọng đều có audit log
- audit không phải plugin phụ
- audit phải đi cùng write path

---

## 8. Security boundary phải nằm ở hạ tầng và domain

- auth bằng cookie httpOnly
- domain gating cho employee access
- permission rõ ở backend
- AI không bypass permission

---

## 9. Read paths phải rẻ, write paths phải rõ

- read screen cho HR / Employee phải nhanh và dễ hiểu
- write action phải có confirmation rõ
- screen nào nhiều trạng thái thì phải ưu tiên queue / timeline / next action

---

## 10. Extensibility không được phá backbone

Nếu thêm feature mới:

- phải gắn với backbone
- phải dùng contract/domain có sẵn nếu hợp lý
- không tạo ra một subsystem song song vô nghĩa

---

## 11. Deployment-aware architecture

- self-host là first-class
- Docker / Kubernetes phải được nghĩ từ đầu
- cần chạy tốt trong môi trường một company / một instance
- không thiết kế theo multi-tenant mặc định

---

## 12. Open-source friendly architecture

- code dễ đọc, dễ test, dễ audit
- module tách rõ để cộng đồng hiểu
- docs phải phản ánh structure thật
- tránh magic quá nhiều

---

## Điều cần tránh

- monolith lộn xộn không boundary
- logic nghiệp vụ rải trong router
- AI tự viết DB
- coupling chéo giữa module
- event không có consumer
- state transition không atomic

---

## Một câu nhớ nhanh

**Kiến trúc của Vroom HR phải làm cho backbone chạy chắc, module tách rõ, audit đúng, và mở rộng được mà không mất câu chuyện sản phẩm.**
