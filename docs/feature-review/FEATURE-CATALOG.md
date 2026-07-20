# Vroom HR — Feature Catalog & Review Checklist

> **Mục đích:** Danh mục tổng hợp toàn bộ chức năng hệ thống, phục vụ review → approve → đóng gói tick verify.
> **Snapshot:** 2026-07-16 | Commit tham chiếu: `b2a4814`
> **Quy trình:** Review từng nhóm → Approve nếu đạt → Đánh dấu ✅ Verified.

---

## Cấu trúc thư mục

```
docs/feature-review/
├── FEATURE-CATALOG.md          ← File index này
├── 01-identity/README.md       ← Identity & Xác thực (7)
├── 02-google/README.md         ← Google Integration (5)
├── 03-ai-automation/README.md  ← AI Automation (4)
├── 04-recruitment/README.md    ← Recruitment (7)
├── 05-interview-calendar/README.md ← Interview & Calendar (3)
├── 06-onboarding/README.md     ← Onboarding (3)
├── 07-employee/README.md       ← Employee (4)
├── 08-attendance/README.md     ← Attendance (3 + 1 đã gỡ)
├── 09-employee-request/README.md ← Employee Request (3)
├── 10-payslip/README.md        ← Payslip (2)
├── 11-payroll/README.md        ← Payroll — chưa triển khai (2)
├── 12-ai-assistant-hr/README.md ← AI Assistant HR (3)
├── 13-employee-assistant/README.md ← Employee Assistant (2)
├── 14-runtime-ops/README.md    ← Runtime & Operations (3)
└── 15-frontend-ui/README.md    ← Frontend UI (8)
```

---

## Tổng quan

| # | Nhóm | Số chức năng | Deployed | Pending Review | Chi tiết |
|---|------|-------------|----------|----------------|----------|
| 01 | Identity & Xác thực | 7 | 7 | 7 | [README](./01-identity/README.md) |
| 02 | Google Integration | 5 | 5 | 5 | [README](./02-google/README.md) |
| 03 | AI Automation | 4 | 4 | 4 | [README](./03-ai-automation/README.md) |
| 04 | Recruitment | 7 | 7 | 7 | [README](./04-recruitment/README.md) |
| 05 | Interview & Calendar | 3 | 3 | 3 | [README](./05-interview-calendar/README.md) |
| 06 | Onboarding | 3 | 3 | 3 | [README](./06-onboarding/README.md) |
| 07 | Employee | 4 | 4 | 4 | [README](./07-employee/README.md) |
| 08 | Attendance | 4 | 3 | 3 | [README](./08-attendance/README.md) |
| 09 | Employee Request | 3 | 3 | 3 | [README](./09-employee-request/README.md) |
| 10 | Payslip | 2 | 2 | 2 | [README](./10-payslip/README.md) |
| 11 | Payroll | 2 | 0 | — | [README](./11-payroll/README.md) |
| 12 | AI Assistant (HR) | 3 | 3 | 3 | [README](./12-ai-assistant-hr/README.md) |
| 13 | Employee Assistant | 2 | 2 | 2 | [README](./13-employee-assistant/README.md) |
| 14 | Runtime & Ops | 3 | 3 | 3 | [README](./14-runtime-ops/README.md) |
| 15 | Frontend UI | 8 | 8 | 8 | [README](./15-frontend-ui/README.md) |
| **Tổng** | | **60** | **57** | **57** | |

---

## Legend

| Ký hiệu | Ý nghĩa |
|----------|---------|
| ⬜ | Chưa review |
| 🔍 | Đang review |
| ✅ | Đã approve & verified |
| ❌ | Chưa triển khai / đã gỡ |
| ⚠️ | Cần xem xét thêm |

---

## Tiến độ Review

| Nhóm | Tiến độ |
|------|---------|
| 01 — Identity | 7/7 ✅ |
| 02 — Google | 5/5 ✅ |
| 03 — AI Automation | 4/4 ✅ |
| 04 — Recruitment | 0/7 |
| 05 — Interview & Calendar | 0/3 |
| 06 — Onboarding | 0/3 |
| 07 — Employee | 0/4 |
| 08 — Attendance | 0/3 |
| 09 — Employee Request | 0/3 |
| 10 — Payslip | 0/2 |
| 11 — Payroll | — (chưa triển khai) |
| 12 — AI Assistant (HR) | 0/3 |
| 13 — Employee Assistant | 0/2 |
| 14 — Runtime & Ops | 0/3 |
| 15 — Frontend UI | 0/8 |
| **Tổng** | **16/57** |

---

## 🔴 Chuẩn toàn project: 100% Tiếng Việt cho người dùng HR

**Hệ thống này dành cho doanh nghiệp Việt Nam. Người dùng là HR người Việt.**

**TUYỆT ĐỐI KHÔNG có tiếng Anh trong bất kỳ thành phần UI nào mà người dùng nhìn thấy:**

| Thành phần UI | Yêu cầu | Ví dụ ĐÚNG | Ví dụ SAI |
|--------------|---------|------------|-----------|
| Tiêu đề trang / section | Tiếng Việt | "Nhà cung cấp AI" | "Provider & Model" |
| Label form | Tiếng Việt | "Tên mô hình" | "Model" |
| Placeholder input | Tiếng Việt | "Ví dụ: openai, cline" | "openai / gemini / ..." |
| Nút bấm | Tiếng Việt | "Kiểm tra kết nối" | "Test connection" |
| Trạng thái | Tiếng Việt | "Đã kết nối", "Đang hoạt động" | "Connected", "Enabled" |
| Thông báo lỗi | Tiếng Việt | "Không thể bật: chưa đồng ý chính sách dữ liệu" | "Cannot enable: data policy..." |
| Thông báo thành công | Tiếng Việt | "Đã lưu cấu hình" | "Configuration saved" |
| Empty state | Tiếng Việt | "Chưa có dữ liệu" | "No data" |
| Audit log | Tiếng Việt | "Cập nhật tên miền: thêm gmail.com" | "Domain update: add gmail.com" |
| Data policy | Tiếng Việt | "Phân loại email", "Trích xuất CV" | "email_intent_classification" |
| Role label | Tiếng Việt | "Quản trị (HR)", "Nhân viên" | "admin (HR)", "user (Employee)" |
| Tab name | Tiếng Việt | "Nhật ký hoạt động" | "Audit logs" |

**Khi thêm code mới hoặc sửa code cũ: kiểm tra TỪNG CHỮ một.** Nếu thấy tiếng Anh → sửa ngay.

**Khi viết test:** assert message tiếng Việt chính xác, không dùng regex mơ hồ.

> **Nguyên tắc:** Đặt mình vào vị trí HR người Việt, không rành công nghệ. Họ cần đọc hiểu mọi thứ bằng tiếng mẹ đẻ.

**Tất cả message hiển thị cho người dùng (lỗi, thông báo, label, audit log) phải là tiếng Việt dễ hiểu.**

| Phạm vi | Yêu cầu | Ví dụ |
|---------|---------|-------|
| Exception `message` | Tiếng Việt, dễ hiểu cho người dùng cuối | `"Phiên đăng nhập không hợp lệ hoặc đã hết hạn"` |
| Test assertion | Khớp chính xác message tiếng Việt trong code | `assert err.message == "Phiên đăng nhập..."` |
| API error response | `error.message` trả về tiếng Việt | `{"error": {"code": "...", "message": "..."}}` |
| UI label / placeholder | Tiếng Việt | `"Nhập mật khẩu..."` |
| Audit log entry | Tiếng Việt, có ngữ cảnh hành động | `"Cập nhật domain: action: remove"` |

**Khi review các nhóm sau, kiểm tra:** test assertion có khớp message tiếng Việt trong code không. Đây là nguyên nhân gây ra 18 test fail oan ở nhóm 01.

---

*Mỗi nhóm có README riêng với danh sách chức năng, tiêu chí review, và kết quả review từng chức năng.*

