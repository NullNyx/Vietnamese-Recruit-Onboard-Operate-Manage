# Data Model Backbone

## Mục tiêu

Tài liệu này chốt các entity cốt lõi hỗ trợ backbone flow và các mối quan hệ chính giữa chúng. Không phải schema đầy đủ — chỉ backbone data model mà mọi module khác đều phải bám vào.

---

## Core entities (backbone)

```
Organization
    │
    ├── User (auth account, role: admin / employee)
    │
    ├── Employee (is_active: false → true)
    │     ├── Department
    │     ├── Position
    │     ├── EmployeeDocument
    │     └── AttendanceRecord / Leave / Overtime / Payslip
    │
    ├── JobOpening → Candidate
    │                ├── CandidateNote
    │                ├── CandidateStatus (new → reviewing → interview_scheduled
    │                │                      → accepted / rejected / archived)
    │                └── attachment CV file (MinIO)
    │
    ├── OnboardingProcess → OnboardingTask
    │
    └── AuditLog
```

---

## Entity lifecycle (backbone flow)

### Candidate

```text
new → reviewing → interview_scheduled → accepted → [onboarding]
                                    → rejected
                                    → archived
```

- accept là trigger cho OnboardingProcess
- interview_scheduled đi cùng calendar_event_id

### OnboardingProcess

```text
created (candidate accepted)
  → tasks pending
  → tasks done
  → employee active
```

- hoàn thành tất cả OnboardingTask → Employee.is_active = true

### Employee

```text
created (candidate accepted + onboarding started)
  → is_active = false (onboarding in progress)
  → is_active = true (onboarding done)
  → is_active = false (offboard)
```

- active → ESS usage
- inactive → không thể login vào ESS

---

## Quan hệ data chính

### Organization → Employee

- Organization là singleton
- Employee thuộc Organization

### Candidate → Employee

- Candidate accept → Employee được tạo
- Employee.active = false trong giai đoạn onboarding
- khi OnboardingProcess hoàn tất → Employee.active = true

### Candidate → JobOpening

- Một Candidate thuộc tối đa một JobOpening
- Hoặc không gắn JobOpening (pipeline tự do)

### Employee → Department / Position

- Department và Position độc lập
- Employee tham chiếu department_id, position_id

### Employee → AttendanceRecord

- AttendanceRecord theo employee + work_date
- check-in / check-out

### Employee → LeaveBalance / LeaveRequest

- LeaveBalance theo employee + leave_type
- LeaveRequest HR review → balance update

### Employee → Payslip

- Payslip theo employee + payroll_period
- Chỉ đọc

### Employee → EmployeeRequest

- Employee tạo request (leave / overtime)
- HR review → accept / reject

---

## State transition rules

| Transition | Điều kiện | Hành động kèm theo |
|------------|-----------|---------------------|
| Candidate → accepted | Không thể undo | Tạo OnboardingProcess, gửi email |
| Onboarding done | Tất cả task done, bởi HR | Employee.active = true |
| Employee → inactive | HR set | Mất quyền ESS |
| Interview scheduled | Phải có calendar_event_id | Atomic với Google Calendar |
| Attendance correction | Có lý do | Audit log |

---

## Audit

- AuditLog là entity bắt buộc
- Mỗi state transition / write action tạo audit record
- AuditLog gồm: user, action, target_type, target_id, old, new, timestamp
- Không thể xóa

---

## Data ownership theo module

| Module | Entity chính | Actor ghi | Actor đọc |
|--------|-------------|-----------|-----------|
| identity | User, AuditLog | Auth flow, admin | auth middleware |
| employee | Employee, Department, Position | HR | HR, ESS (self) |
| recruitment | Candidate, JobOpening, Note | HR, pipeline | HR |
| onboarding | OnboardingProcess, Task | HR | HR, Employee (self) |
| attendance | AttendanceRecord, Leave, OT | Employee (check-in), HR (correction) | HR, Employee (self) |
| payroll | SalaryConfig, Payslip | HR (config) | HR, Employee (self, payslip) |
| ess | (read HR entities) | Employee (request) | Employee (self) |
| assistant | DraftAction | Không ghi | HR (read-tool) |

---

## Một câu nhớ nhanh

**Data model của Vroom HR phải phản ánh lifecycle thật của Candidate → Employee, giữ được lịch sử qua audit, và phân quyền đọc / ghi rõ cho từng module.**

