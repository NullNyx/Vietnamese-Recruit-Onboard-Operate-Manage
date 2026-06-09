# Attendance Check-in/Check-out Office Network

## Overview
Employee-owned Attendance Record check-in/check-out gated by Organization office network allowlist. Per ADR-0010, timestamps stored in UTC; work date derived from Organization timezone.

## Requirements

### Check-in/Check-out Flow
- Employee can check in and check out for current work date only
- Request IP must match approved office network (from Organization settings)
- Employee writes are idempotent and no-overwrite

### Data Storage
| Field | Type | Notes |
|-------|------|-------|
| `check_in_at` | datetime UTC | Timestamp of check-in |
| `check_out_at` | datetime UTC | Timestamp of check-out |
| `check_in_ip` | string | Client IP at check-in |
| `check_out_ip` | string | Client IP at check-out |
| `check_in_user_agent` | string | HTTP User-Agent at check-in |
| `check_out_user_agent` | string | HTTP User-Agent at check-out |
| `source` | string | Always "web" for MVP |
| `work_date` | date | Derived from Organization timezone |

### API Endpoints (Employee-owned)
```
POST /api/attendance/me/check-in   → Creates Attendance Record for today if none exists
GET  /api/attendance/me/today      → Get today's attendance record  
POST /api/attendance/me/check-out  → Requires existing check_in_at, idempotent
```

### IP Validation
- Disallowed IP returns HTTP 403: "Attendance check-in is only allowed from approved office network."
- IP check happens before any DB write

### Acceptance Criteria
1. POST /api/attendance/me/check-in creates current-day Attendance Record when none exists
2. Repeated check-in returns existing record without overwriting check_in_at
3. POST /api/attendance/me/check-out requires existing check_in_at
4. Repeated check-out returns existing record without overwriting check_out_at
5. Employee cannot check in/out for another Employee (Employee endpoints free of employee_id path params)
6. Disallowed IP rejected before any Attendance Record write

### Tests Coverage
- Allowed IP → 200 OK with created record
- Blocked IP → 403 with error message
- Ownership check → Employee cannot check-in for another Employee
- Idempotency → Repeated calls return same record without overwrite
- Timezone work_date → UTC timestamp correctly mapped to Organization timezone date

## Out of Scope
- Shift scheduling
- Late penalties  
- Payroll integration
- Policy engine coupling
- GPS/device tracking
