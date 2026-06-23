# Trạng thái project hiện tại

## Mục tiêu của bộ docs này

Đây là vùng docs dành cho con người đọc, viết bằng tiếng Việt, nhưng giữ nguyên các thuật ngữ chuyên ngành tiếng Anh khi đó là từ khóa domain hoặc tên kỹ thuật đã ổn định. Mục tiêu là ghi lại:

- **status** hiện tại của project
- **plan** đang bàn
- **next steps** cần làm tiếp theo

## Project đang được định nghĩa là gì

Vroom HR là một hệ thống HR self-hosted cho một company duy nhất trên mỗi deployment. Ý tưởng trung tâm không phải là một HR suite đầy đủ từ đầu, mà là một **Backbone Flow** rất rõ:

**incoming email → AI classify → CV parse → Candidate → HR review → interview scheduling → accept → congratulations email → onboarding → Employee**

Theo ADR hiện tại, project được thiết kế quanh dòng chảy này. Các phần khác như attendance, payroll, self-service có tồn tại trong codebase, nhưng mức độ ưu tiên và phạm vi phải bám theo backbone này.

## Project hiện đang có gì

### 1. Identity / Auth

Đã có module đăng nhập và phân quyền:

- Google OAuth2
- JWT bằng cookie httpOnly
- role system cho HR
- whitelist / allowed domain logic
- audit log cho action quan trọng

Đây là nền tảng cho toàn bộ các module khác.

### 2. Employee

Đã có module quản lý Employee:

- departments
- positions
- employees
- employee documents

Trong domain, **Employee** là record nhân sự sau khi Candidate được accept và onboarding hoàn tất.

### 3. Gmail

Đã có tích hợp Gmail để phục vụ luồng recruit:

- xử lý email đầu vào
- gửi email đầu ra
- hỗ trợ các bước liên quan tới recruitment workflow

### 4. Recruitment

Đây là phần core nhất của project hiện tại và là nơi Backbone Flow đã được hiện thực khá nhiều:

- email intent classification
- CV parsing
- auto tạo Candidate từ CV
- candidate pipeline state machine
- HR review queue
- schedule interview
- job opening
- metrics
- runtime support

Theo ADR, đây là phần đã tiến gần nhất với mục tiêu sản phẩm.

### 5. Onboarding

Đã có module onboarding, nhưng theo ADR đây vẫn là **missing link** quan trọng trong backbone:

- khi Candidate được accept thì cần consumer của event đó
- onboarding phải chuyển Candidate thành Employee active
- checklist task là phần trung tâm của onboarding

### 6. Attendance

Attendance đã có trong codebase và hiện được định nghĩa lại theo hướng hẹp hơn:

- attendance record
- office-network gating
- check-in / check-out
- HR correction

Nó không còn là Policy Engine cũ, mà là một slice demo-thin phục vụ self-service và payroll liên quan.

### 7. Payroll

Payroll đã có các thành phần nền:

- salary configs
- payslips
- tax / insurance logic
- employee-facing payslip view

### 8. Self-Service / ESS

Đã có employee-facing surface:

- read-first
- dùng cho active Employee
- tách biệt với HR admin side

### 9. Employee Request

Có luồng request do Employee gửi lên và HR review:

- leave request
- overtime request
- review queue
- audit

### 10. AI Assistant

Đã có AI Assistant cho HR, theo thiết kế là:

- tool-calling, không dùng RAG ở giai đoạn này
- chỉ có Read-Tool và Draft-Tool
- human-in-the-loop, không tự write vào DB
- tách thành standalone module

### 11. Employee Assistant

Có conversational assistant cho Employee, nhưng vẫn theo boundary an toàn và không tự ý ghi dữ liệu.

## Những quyết định kiến trúc lớn đã chốt

### Backbone Flow là trung tâm

Project không đi theo hướng HR suite phình to. Nó được khóa vào recruit-to-onboard backbone. Điều này giúp codebase có một câu chuyện thống nhất.

### Policy Engine đã bị loại bỏ

Policy Engine và các spec liên quan đã được quyết định remove. Đây là phần không còn phù hợp với backbone hiện tại.

### AI Assistant là tool-calling

Assistant đọc dữ liệu live và draft hành động, nhưng không tự write. Đây là boundary an toàn quan trọng.

### Interview scheduling là synchronous

Khi HR schedule interview, hệ thống phải tạo Google Calendar event ngay trong request. Nếu fail thì không được để Candidate ở trạng thái sai.

### Employee access là domain-gated

Employee login phải đi qua allowed email domains của Organization. Self-service là read-first ở giai đoạn này.

### Attendance dùng office-network gating

Attendance chỉ mở theo office IP/CIDR, tránh mở rộng sang GPS, biometrics, mobile tracking hay policy engine.

## Tình trạng tổng quát

### Shipped khá chắc

- Identity/Auth
- Recruitment core
- Gmail integration
- Employee module nền
- AI Assistant module
- Employee Assistant
- Attendance slice
- Payroll slice
- ESS read surfaces

### Còn thiếu / cần nối lại

- Onboarding consumer thực sự cho accepted Candidate
- Làm rõ ranh giới dữ liệu giữa Candidate → Employee → ESS
- Củng cố các flow confirm/draft của Assistant
- Rà lại toàn bộ docs để thống nhất ngôn ngữ cho human

### Đã bị shelved / removed

- Policy Engine
- spec cũ xoay quanh multi-tenant / policy-heavy direction

## Hướng phát triển hợp lý tiếp theo

### Ngắn hạn

1. Chuẩn hóa docs tiếng Việt cho human.
2. Ghi rõ current status, plan, next steps.
3. Làm rõ onboarding flow là missing link nào.
4. Giữ backbone nhỏ, không mở rộng phạm vi lung tung.

### Trung hạn

1. Hoàn thiện onboarding end-to-end.
2. Củng cố HR review, interview scheduling, candidate lifecycle.
3. Làm rõ cách ESS đọc dữ liệu Employee an toàn.
4. Chuẩn hóa docs theo từng mảng nếu cần.

### Nguyên tắc khi viết docs sau này

- Viết bằng tiếng Việt.
- Giữ nguyên tên kỹ thuật tiếng Anh nếu đó là domain term ổn định.
- Mỗi lần trao đổi xong phải có ghi nhận lại trong docs.
- Không trộn docs cho human với docs dành cho agents.

## Next steps đề xuất

- Tạo thêm `docs/project/plan.md` để ghi kế hoạch đang bàn.
- Tạo thêm `docs/project/next-steps.md` nếu cần tách riêng task ngắn hạn.
- Sau mỗi cuộc trao đổi, cập nhật `status.md` hoặc file liên quan để không mất ngữ cảnh.
