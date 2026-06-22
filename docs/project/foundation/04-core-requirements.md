# Core Requirements

## Giới thiệu

Tài liệu này định nghĩa yêu cầu chức năng (functional) và phi chức năng (non-functional) cốt lõi của Vroom HR. Không phải danh sách tính năng đầy đủ — chỉ những yêu cầu nền tảng mà mọi module khác đều phải thỏa mãn.

---

## Phần A — Yêu cầu chức năng (Functional Requirements)

### A1. Backbone Flow (recruit → onboard → employee)

Hệ thống phải đi qua được một chuỗi liên tục:

1. **Email classification**: AI xác định email tuyển dụng (cv / partner / event / internal / other)
2. **CV parsing**: OCR + LLM → Candidate với confidence score
3. **Candidate pipeline**: HR review (new → reviewing → interview_scheduled → accepted / rejected / archived)
4. **Interview scheduling**: Google Calendar event + Meet link, synchronous, atomic
5. **Accept event → Onboarding**: accepted Candidate kích hoạt onboarding process
6. **Onboarding checklist**: tasks (pending → done), có HR kiểm soát
7. **Onboarding complete → Employee active**: khi tất cả tasks done, Candidate thành Employee active
8. **Congratulations email**: gửi tự động sau accept

Yêu cầu bắt buộc: không được đứt flow giữa các bước.

### A2. Authentication & Authorization

- Google OAuth2 với httpOnly cookie
- Phân quyền: admin (HR) / employee (ESS)
- Domain gating: chỉ email thuộc Organization allowed domain mới login được
- Super admin bootstrap khi deploy
- Employee không thấy HR surface

### A3. Employee Management

- Quản lý department / position / employee
- Soft-delete qua is_active flag
- Upload / download tài liệu nhân sự qua MinIO
- Employee lifecycle: candidate → inactive (onboarding) → active (ESS)

### A4. Audit

- Mỗi action ghi dữ liệu phải có audit log
- Audit bao gồm: ai làm, lúc nào, action gì, dữ liệu thay đổi gì
- Audit không thể tắt hoặc xóa

### A5. AI Assistant

- HR-facing assistant: tool-calling, đọc context thật
- Read-Tool: gọi service thật, trả data live
- Draft-Tool: không ghi, trả draft action để HR confirm
- LLM không bao giờ có write tool
- Employee assistant: chỉ đọc data cá nhân

### A6. Attendance

- Check-in / check-out trong ngày
- Gating bằng office IP/CIDR
- HR correction có lý do, có audit
- Leave request / overtime request có HR review

### A7. Payroll

- Salary config theo position / department
- Tính lương theo bảng Việt Nam: 26 ngày công
- Insurance: BHXH 8% + BHYT 1.5% + BHTN 1% (employee)
- Tax: 7 bậc progressive
- Personal deduction: 11M/tháng; dependent: 4.4M/người
- Payslip chỉ đọc, không sửa

### A8. Employee Self-Service (ESS)

- Read-first: profile, payslip, leave balance
- Write có kiểm soát: gửi leave / overtime request
- Mỗi employee chỉ thấy dữ liệu của mình

### A9. Audit & Compliance

- Audit log không thể tắt
- Mỗi thay đổi trạng thái quan trọng đều ghi log
- AI assistant không tự ghi DB → audit rõ

---

## Phần B — Yêu cầu phi chức năng (Non-Functional Requirements)

### B1. Self-host / Deployment

- Docker Compose cho development
- Có thể deploy production với PostgreSQL + Redis + MinIO
- Single-company, single-deployment
- Không có multi-tenant trong một instance

### B2. Security

- JWT trong httpOnly cookie
- OAuth tokens mã hóa AES-256-GCM
- Employee domain gating
- AI không có quyền ghi
- Audit log bắt buộc

### B3. Performance

- async-first ở backend
- Redis cho cache và rate limit
- ARQ cho background tasks
- Database indexing cho query candidate pipeline

### B4. Data Integrity

- Database transactions bảo vệ state transitions
- Candidate accept / interview scheduling là atomic
- Soft-delete cho employee
- AI Draft không ghi DB — không có rủi ro data corruption từ LLM

### B5. Observability

- Health check endpoint
- Audit log by design
- Error tracking qua domain exceptions → HTTP mapping

### B6. Localization (Vietnamese)

- Giao diện tiếng Việt
- Luật lao động Việt Nam (tax, insurance, leave)
- Calendar timezone theo Organization
- Ngày lễ Việt Nam trong holiday module

### B7. Extensibility

- Module boundaries rõ
- Assistant dùng service từ module khác, không chứa business logic
- Events cho cross-module communication (accepted → onboarding)
- Open-source license (AGPL)

---

## Phần C — Yêu cầu bị loại trừ (Out of Scope)

Những điều này đã được quyết định không làm (theo ADR đã có):

| Yêu cầu | Lý do |
|----------|-------|
| Policy Engine | Đã remove (ADR-0005) |
| Multi-tenant | Mỗi deployment một company duy nhất (ADR-0001) |
| GPS / Biometric attendance | Out of scope (ADR-0010) |
| RAG cho AI Assistant | Deferred (ADR-0003) |
| AI autonomous write | Cấm kiến trúc (ADR-0006) |
| Mobile app | Chưa có trong scope hiện tại |
| Mở sign-up cho employee | Domain gating bắt buộc (ADR-0009) |

---

## Phần D — Ma trận ưu tiên (theo backbone)

| Yêu cầu | Backbone | Mức độ ưu tiên |
|----------|----------|----------------|
| A1 — Backbone Flow | ✅ Core | P0 — phải chạy |
| A2 — Auth + Authorization | Hỗ trợ | P0 |
| A3 — Employee Management | Hỗ trợ | P0 |
| A4 — Audit | Hỗ trợ | P0 |
| A5 — AI Assistant | Hỗ trợ | P1 |
| A6 — Attendance | Ngoài backbone | P2 |
| A7 — Payroll | Ngoài backbone | P2 |
| A8 — ESS | Ngoài backbone | P2 |
| A9 — Audit & Compliance | Hỗ trợ | P0 |
| B1 — Self-host | Deployment | P0 |
| B2 — Security | Toàn hệ thống | P0 |
| B3 — Performance | Toàn hệ thống | P1 |

