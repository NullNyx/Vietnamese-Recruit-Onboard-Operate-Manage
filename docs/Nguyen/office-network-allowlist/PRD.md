# PRD — Office Network Allowlist cho Attendance

## 1. Tổng quan dự án

- **Tên feature:** Office Network Allowlist
- **Module:** Attendance
- **Loại:** New feature + Integration
- **Người dùng mục tiêu:** HR/Admin (cấu hình), Employee (check-in/out)
- **Mục tiêu:** Nhân viên chỉ được chấm công khi kết nối mạng văn phòng (IP whitelist)

## 2. Bối cảnh

Theo ADR-0010, attendance được triển khai demo-thin với office-network gating:
- Employee check-in/out chỉ được thực hiện từ IP/CIDR được HR admin cấu hình
- Timestamp lưu UTC, work date tính theo Organization timezone
- Không có GPS, biometrics, mobile tracking, shift scheduling

## 3. User Stories

### HR/Admin
| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| HR-1 | Là HR, tôi muốn cấu hình danh sách IP/CIDR được phép để nhân viên chỉ chấm công từ mạng văn phòng | - Lưu được 1 hoặc nhiều CIDR<br>- CIDR format hợp lệ được chấp nhận<br>- CIDR sai format bị reject kèm message rõ |
| HR-2 | Là HR, tôi muốn xem danh sách IP/CIDR hiện tại | Hiển thị list các CIDR đã cấu hình |
| HR-3 | Là HR, tôi muốn thêm/bớt CIDR khỏi allowlist | Thao tác add/remove không ảnh hưởng entries khác |
| HR-4 | Là HR, tôi muốn thay đổi được cấu hình mạng | PUT request update toàn bộ list |

### Employee
| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| EMP-1 | Là Employee, tôi muốn check-in từ mạng văn phòng | - IP trong allowlist → check-in thành công<br>- IP ngoài allowlist → 403 + message "Cần kết nối mạng văn phòng" |
| EMP-2 | Là Employee, tôi muốn check-out từ mạng văn phòng | Tương tự EMP-1 |

### Non-admin
| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| NON-1 | Là Employee (non-HR), tôi không thể thay đổi cấu hình mạng | PUT/POST/DELETE → 403 Forbidden |

## 4. Functional Requirements

### 4.1 Data Model

**OrganizationSettings** — thêm field:
```python
attendance_allowed_networks: list[str] = Field(
    default_factory=list,
    sa_column=Column(ARRAY(String), nullable=False),
)
```

**Ràng buộc:**
- Tối đa 20 CIDR entries
- Không trùng lặp
- Empty list = allow all (không gate)

### 4.2 Value Objects

**CidrRange:**
- Validate format: `X.X.X.X/N` với X ∈ [0-255], N ∈ [0-32]
- Single IP = `/32`
- Raise `ValueError` nếu invalid

**AttendanceNetworkConfig:**
- Chứa `list[CidrRange]`
- Method `is_ip_allowed(ip: str) -> bool`
- Empty config → `is_ip_allowed()` returns `True`

### 4.3 API Endpoints

| Method | Path | Mô tả | Access |
|--------|------|-------|--------|
| GET | `/api/attendance/settings/network` | Lấy allowlist | HR+ |
| PUT | `/settings/network` | Thay thế toàn bộ | HR only |
| POST | `/settings/network/add` | Thêm CIDRs | HR only |
| DELETE | `/settings/network/{cidr}` | Xóa CIDR | HR only |

### 4.4 Validation Rules

| Input | Behavior |
|-------|----------|
| `[]` (empty) | Allow all, log warning |
| Valid CIDR | Accept |
| Invalid CIDR | 400 + "Invalid CIDR: X.X.X.X/N" |
| Duplicate | 400 + "Duplicate entry" |
| >20 entries | 400 + "Too many entries (max 20)" |
| Non-admin write | 403 Forbidden |

### 4.5 Attendance Service Integration

**CheckInCommand / CheckOutCommand:**
1. Load `AttendanceNetworkConfig` của org
2. Extract client IP từ request
3. Gọi `config.is_ip_allowed(client_ip)`
4. Nếu `False` → raise `OfficeNetworkRequiredError("Cần kết nối mạng văn phòng để chấm công")`

## 5. Non-Functional Requirements

- **Performance:** IP check phải < 1ms (dùng `ipaddress` module, không regex)
- **Security:** Config chỉ expose qua API, không log IP range ra ngoài
- **Audit:** Mọi thay đổi config phải ghi audit log (ai, khi nào, giá trị cũ/mới)

## 6. Out of Scope

- GPS, mobile device tracking, biometrics
- Shift scheduling, policy engine
- IPv6
- Entity: Tenant, Manager, Timesheet, Shift
- Employee tự xem/đề nghị allowlist

## 7. Technical Design

### 7.1 Module Structure

```
backend/src/modules/attendance/
├── domain/
│   ├── value_objects.py      # CidrRange, AttendanceNetworkConfig
│   └── exceptions.py         # OfficeNetworkRequiredError
├── infrastructure/
│   └── repositories.py       # attendance_allowed_networks field
├── application/
│   ├── commands.py           # UpdateAttendanceNetworkConfig
│   └── queries.py            # GetAttendanceNetworkConfig
├── api/
│   ├── schemas.py            # NetworkAllowlistRequest/Response
│   └── router.py             # /settings/network endpoints
└── container.py              # DI
```

### 7.2 Database Migration

```sql
ALTER TABLE organizations 
ADD COLUMN attendance_allowed_networks VARCHAR(255)[] DEFAULT '{}';
```

### 7.3 Error Responses

```python
class OfficeNetworkRequiredError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=403,
            detail="Cần kết nối mạng văn phòng để chấm công"
        )
```

## 8. Testing Strategy

| Test Case | Expected |
|-----------|----------|
| Admin PUT valid CIDRs | 200 + saved |
| Admin PUT invalid CIDR | 400 + error message |
| Employee PUT config | 403 |
| is_ip_allowed() với empty config | True |
| is_ip_allowed() với IP trong range | True |
| is_ip_allowed() với IP ngoài range | False |
| Check-in từ IP không được phép | 403 + message |
| Check-in từ IP được phép | 200 + success |

## 9. Timeline / Milestones

| Milestone | Mô tả |
|-----------|-------|
| M1 | Domain value objects + validation |
| M2 | Migration + Repository |
| M3 | API endpoints (HR-only) |
| M4 | Attendance service integration |
| M5 | Tests |
| M6 | Frontend (optional) |

## 10. Open Questions

- [ ] Frontend có cần làm ngay không, hay để sau?
- [ ] Có cần support IPv6 không? (xem xét sau)
- [ ] Audit log format như thế nào? (dùng existing AuditLog entity hay tạo mới?)
