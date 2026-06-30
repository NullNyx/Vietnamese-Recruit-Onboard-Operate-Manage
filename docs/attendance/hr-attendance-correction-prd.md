# PRD: HR Attendance List & Correction Flow

## Overview

HR admins can list Attendance Records across all records with filters, and
correct individual records with required reason and audit logging. This keeps
the Attendance module in HR admin domain.

**Routes:** `/attendance` (list) · `/attendance/:id/correct` (correction modal)

---

## ADR Alignment

| ADR | Relevance |
|---|---|
| ADR-0010 | HR can correct records with a required correction reason; every correction writes an audit log. |
| Domain invariant | Every admin action must write an audit log (AttendanceRecord correction is an admin action). |
| ADR-0009 | HR accesses via admin role; non-admin cannot call correction endpoint. |

---

## Backend Analysis

### Existing Endpoints

| Method | Path | Purpose | Role |
|---|---|---|---|
| `GET` | `/api/attendance/settings/network` | View network allowlist | Any auth |
| `PUT` | `/api/attendance/settings/network` | Replace allowlist | HR/Admin |
| `POST` | `/api/attendance/settings/network/add` | Add CIDRs | HR/Admin |
| `DELETE` | `/api/attendance/settings/network` | Remove CIDR | HR/Admin |
| `GET` | `/api/attendance/me/today` | Get own today record | Staff |
| `POST` | `/api/attendance/me/check-in` | Check in | Staff |
| `POST` | `/api/attendance/me/check-out` | Check out | Staff |
| `GET` | `/api/attendance/me/history` | Get own month history | Staff |

### New Endpoints Needed

| Method | Path | Purpose | Role |
|---|---|---|---|
| `GET` | `/api/attendance/records` | List all records with filters | HR/Admin |
| `PUT` | `/api/attendance/records/:id/correct` | Correct a record | HR/Admin |

### Schema Changes

#### `AttendanceRecord` entity — add correction fields

```python
# New columns on attendance_records table
corrected_by_user_id: UUID | None  # FK → users.id
corrected_at: datetime | None       # UTC timestamp of correction
correction_reason: str | None       # Required non-empty string
previous_check_in_at: datetime | None  # Snapshot before correction
previous_check_out_at: datetime | None  # Snapshot before correction
```

#### `AttendanceRecordResponse` — extend for HR view

```python
class AttendanceRecordResponse(BaseModel):
    # ... existing fields ...
    employee_name: str          # Joined from employees.full_name
    employee_code: str          # Joined from employees.employee_code
    corrected_by_user_id: UUID | None = None
    corrected_at: datetime | None = None
    correction_reason: str | None = None
```

#### New schemas

```python
class AttendanceListRequest(BaseModel):
    start_date: date           # Required
    end_date: date             # Required
    employee_id: UUID | None   # Optional filter
    status: str | None         # "checked_in" | "completed" | None (all)

class AttendanceListResponse(BaseModel):
    records: list[AttendanceRecordResponse]
    total: int
    page: int
    page_size: int

class CorrectionRequest(BaseModel):
    check_in_at: datetime | None  # New value (null to clear)
    check_out_at: datetime | None # New value (null to clear)
    correction_reason: str        # Required, non-empty

class CorrectionResponse(BaseModel):
    message: str
    record: AttendanceRecordResponse
```

### Service Layer

#### `AttendanceService.get_all_records()`

New method for HR to query records across employees.

- Accept filters: date range, employee_id, status
- Join with employees table for name/code
- Return paginated results

#### `AttendanceService.correct_record()`

New method for HR correction.

1. Fetch existing record by ID
2. Snapshot `check_in_at` and `check_out_at` as `previous_*`
3. Update with new values
4. Set `corrected_by_user_id`, `corrected_at`, `correction_reason`
5. Persist and return

#### Audit logging in router

```python
await audit_service.log_action(
    admin=user,
    action_type=AuditActionType.ATTENDANCE_CORRECTION,
    details={
        "record_id": str(record.id),
        "employee_id": str(record.employee_id),
        "previous_check_in_at": previous_check_in_at.isoformat() if previous_check_in_at else None,
        "previous_check_out_at": previous_check_out_at.isoformat() if previous_check_out_at else None,
        "new_check_in_at": record.check_in_at.isoformat() if record.check_in_at else None,
        "new_check_out_at": record.check_out_at.isoformat() if record.check_out_at else None,
        "correction_reason": correction_reason,
    },
)
```

### New `AuditActionType`

```python
ATTENDANCE_CORRECTION = "attendance_correction"
```

---

## Frontend

### Admin Navigation

Already exists in `admin-nav-config.ts`:

```ts
{
  id: 'cham-cong',
  label: 'Chấm công',
  links: [
    { href: '/attendance/checkin', label: 'Check-in', icon: Clock },
    { href: '/attendance/schedules', label: 'Lịch làm', icon: Calendar },
    ...
  ],
}
```

**Action:** Replace `/attendance/checkin` with `/attendance` (list view).

### HR Attendance List Page (`/attendance`)

**Header:** "Quản lý chấm công"

**Filters row:**
- Date range picker (start_date, end_date) — default: current month
- Staff dropdown (all staff, or specific)
- Status dropdown: Tất cả / Đã check-in / Hoàn thành
- "Tìm kiếm" button

**Table columns:**

| Header | Cell | Alignment |
|---|---|---|
| Mã NV | employee_code | left |
| Họ tên | full_name | left |
| Ngày | work_date (dd/mm/yyyy) | left |
| Check-in | check_in_at (HH:mm:ss) or "—" | left |
| Check-out | check_out_at (HH:mm:ss) or "—" | left |
| Nguồn | source | left |
| Trạng thái | Badge: "Đã check-in" / "Hoàn thành" / "—" | left |
| Đã sửa | Badge "Đã sửa" if corrected_at exists, else "—" | left |
| Thao tác | "Sửa" button (opens correction modal) | right |

**Empty state:** "Không có bản ghi chấm công phù hợp."

**Pagination:** page numbers at bottom (if >20 records).

### Correction Modal

Triggered by clicking "Sửa" on any row.

**Modal content:**
- Title: "Sửa bản ghi chấm công"
- Staff info (read-only): name, code, work_date
- **Current values** (read-only): check_in_at, check_out_at
- **New values** (editable inputs):
  - Check-in time (datetime picker)
  - Check-out time (datetime picker)
- **Lý do sửa** (textarea, required, min 1 character)
- "Hủy" button + "Xác nhận sửa" button

**Validation:**
- correction_reason cannot be empty
- At least one value must differ from current

**On submit:**
- `PUT /api/attendance/records/:id/correct`
- On success: close modal, refresh table, show `toast.success("Đã cập nhật bản ghi")`
- On error: show `toast.error(detail)`

**Staff visibility:** Staff sees corrected record and `correction_reason` in history, but NOT `corrected_by_user_id` or `corrected_at` (internal audit only).

---

## Permission Invariant

| Actor | Can list all records? | Can correct? | Can see audit metadata? |
|---|---|---|---|
| HR/Admin | ✅ | ✅ | ✅ |
| Staff | ❌ (own only via `/me/history`) | ❌ | ❌ (sees reason only) |

Correction endpoint MUST require HR/Admin role. non-admin calls → 403.

---

## Not In Scope

- Bulk correction (one record at a time)
- Staff self-correction requests
- Approval workflow for corrections
- Payroll integration with corrected records
- Attendance report/export

---

## Files to Modify/Create

| File | Action |
|---|---|
| `backend/src/modules/attendance/domain/entities.py` | Add correction columns |
| `backend/src/modules/attendance/api/schemas.py` | Add list/correction schemas |
| `backend/src/modules/attendance/api/router.py` | Add list + correction endpoints |
| `backend/src/modules/attendance/application/attendance_service.py` | Add list + correction methods |
| `backend/src/modules/identity/domain/entities.py` | Add `ATTENDANCE_CORRECTION` to AuditActionType |
| `frontend/src/app/(dashboard)/attendance/page.tsx` | Create HR list page |
| `frontend/src/lib/admin-nav-config.ts` | Update attendance nav link |
| `docs/attendance/hr-attendance-correction-prd.md` | This file |
