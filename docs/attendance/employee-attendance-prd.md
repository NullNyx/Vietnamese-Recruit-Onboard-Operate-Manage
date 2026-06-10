# PRD: Employee Self-Service Attendance UI

## Overview

Employee Self-Service (ESS) Attendance page lets active Employees check in/out for the current work date and view their own Attendance Records history. This is the first Employee write flow, per ADR-0010 (office-network-gated attendance) and ADR-0016 (phase-1 ESS).

**Route:** `/employee/attendance`

---

## ADR Alignment

| ADR | Relevance |
|---|---|
| ADR-0009 | Employee access is domain-gated; self-service is read-first baseline. Attendance is the first write exception. |
| ADR-0010 | Office-network-gated, idempotent check-in/check-out, no-overwrite. HR corrects with audit log. Timestamps UTC, work date from Org timezone. |
| ADR-0016 | Phase-1 ESS includes Attendance. Payslips and Assistant are phase-2. |

**ADR note:** ADR-0009 states self-service is "read-first." ADR-0010 explicitly carves attendance check-in/check-out as the first ESS write. This PRD stays within that exception: no edit or delete controls for Employees.

---

## Existing Backend Endpoints

| Method | Path | Purpose | Status |
|---|---|---|---|
| `GET` | `/api/attendance/me/today` | Get current day's Attendance Record | Wired in `main.py` |
| `POST` | `/api/attendance/me/check-in` | Check in (idempotent) | Wired in `main.py` |
| `POST` | `/api/attendance/me/check-out` | Check out (idempotent, requires check-in first) | Wired in `main.py` |
| `GET` | `/api/attendance/me/history` | Get recent Attendance Records (month range) | **Not yet wired — backend gap** |

**Error responses (JSON):**

```json
{
  "error_code": "OFFICE_NETWORK_REQUIRED",
  "detail": "Attendance check-in is only allowed from approved office network."
}
```

Other error codes: `ALREADY_CHECKED_IN`, `NOT_CHECKED_IN`.

---

## Frontend Structure

### Existing patterns to follow

- `frontend/src/app/(employee)/layout.tsx` — wraps all ESS pages with `<HeaderNavigation />`
- `frontend/src/lib/employee-navigation.ts` — array of `EmployeeNavItem` rendered in mobile nav
- `frontend/src/lib/ess-nav-config.ts` — header nav config for Employee role
- `frontend/src/app/(employee)/employee/profile/page.tsx` — reference for data fetching, loading, error, shadcn/ui patterns

---

## UI Specification

### Employee Navigation (update)

Add Attendance to both navigation surfaces:

**`employee-navigation.ts`** — add nav item:
```ts
{ href: "/employee/attendance", label: "Chấm công", icon: Clock }
```
Insert between "Hồ sơ" and "Tài liệu".

**`ess-nav-config.ts`** — add Attendance link in header groups:
```ts
{ href: "/employee/attendance", label: "Chấm công", icon: Clock }
```
Add to `activeRoutes`.

### Attendance Page (`/employee/attendance`)

Layout: max-width 900px, `space-y-6`.

#### Section 1: Today Card

**Header row:**
- Left: "Hôm nay" heading + current date (dd/mm/yyyy, localized via `vi-VN`)
- Right: status badge

**States:**

| State | Badge color | Badge text | Body content |
|---|---|---|---|
| Loading | skeleton | — | Skeleton pulse rows |
| Empty (no check-in) | muted | "Chưa điểm danh" | "Bạn chưa check-in hôm nay" |
| Checked-in (no check-out) | green | "Đã check-in" | Check-in time (HH:mm:ss) · IP · Source ("Web") |
| Completed (checked in + checked out) | blue | "Hoàn thành" | Check-in time → Check-out time · Source ("Web") |
| Error (OFFICE_NETWORK_REQUIRED) | destructive | "Lỗi mạng" | Exact backend `detail` message |

**Status badge component:** Use shadcn `<Badge>` with `variant` mapped to state.

**Actions (below badge row):**

| State | Action shown |
|---|---|
| Empty | `<Button onClick={handleCheckIn}>Check-in</Button>` |
| Checked-in (not yet checked out) | `<Button onClick={handleCheckOut}>Check-out</Button>` |
| Completed | `<Button disabled>Đã hoàn thành</Button>` |
| Error | `<Button onClick={handleCheckIn}>Thử lại</Button>` + error message in red |
| Loading | `<Button disabled>` with spinner |

Button states: loading shows `<Loader2 className="animate-spin" />`.

#### Section 2: History List

**Header:** "Lịch sử chấm công" + current month/year.

**Controls:**
- Month selector: `<Select>` with previous/next months (last 3 months + current).
- Default: current month.

**Table columns:**

| Header | Cell content | Alignment |
|---|---|---|
| Ngày | dd/mm/yyyy | left |
| Check-in | HH:mm:ss or "—" | left |
| Check-out | HH:mm:ss or "—" | left |
| Nguồn | "Web" or source value | left |
| Trạng thái | Badge: "Đã check-in" (green) / "Hoàn thành" (blue) / "—" (muted) | left |

**Empty state:** "Chưa có bản ghi chấm công trong tháng này."

**No edit/delete controls:** table cells are read-only text, no action column.

---

## Data Fetching

### Today record

```ts
GET /api/attendance/me/today
// Returns: AttendanceRecordResponse | null
```

- Poll interval: none (manual refresh via button).
- On mount: fetch, show loading skeleton → render state.

### Check-in / Check-out

```ts
POST /api/attendance/me/check-in
POST /api/attendance/me/check-out
```

- Both return `{ message, record }`.
- On success: re-fetch today record, show `toast.success(message)`.
- On `403 OFFICE_NETWORK_REQUIRED`: show error state with exact `detail` text.
- On `409 ALREADY_CHECKED_IN` / `400 NOT_CHECKED_IN`: re-fetch today record (idempotent, resolve silently).
- On other errors: show `toast.error("Không thể thực hiện thao tác")`.

### History (requires new backend endpoint)

**Needed endpoint:**
```
GET /api/attendance/me/history?month=YYYY-MM
```

Returns: `{ records: AttendanceRecordResponse[] }`.

**Backend gap:** Repository method `get_by_employee_and_date_range` exists but is not exposed via router. This endpoint needs to be added to `router.py` before the frontend history section works.

---

## Error Handling

| HTTP | Backend `error_code` | Frontend display |
|---|---|---|
| 403 | `OFFICE_NETWORK_REQUIRED` | Exact `detail` string in card body + destructive badge |
| 409 | `ALREADY_CHECKED_IN` | Silent: re-fetch today record |
| 400 | `NOT_CHECKED_IN` | Silent: re-fetch today record |
| Other | — | `toast.error` generic message |

**Blocked network error is shown verbatim** — no wrapping or translation.

---

## Responsive Layout

**Desktop (≥640px):** Two-column grid for today card details (label/value pairs side by side). History table full-width with horizontal scroll if needed, but columns fit at 900px max-width.

**Mobile (<640px):** Single column. Today card stacks vertically. Table scrolls horizontally with `overflow-x-auto` wrapper. No text overlap: truncation or wrapping on long values.

**Test constraint:** No horizontal scroll on the page body (only within the history table if necessary). No text overlap at any breakpoint.

---

## Acceptance Criteria

| # | Criterion | Verified by |
|---|---|---|
| 1 | Employee can navigate to `/employee/attendance` via header nav and mobile nav | Manual + snapshot |
| 2 | Today card shows loading skeleton before fetch completes | Unit test (mock delay) |
| 3 | Today card shows "Chưa điểm danh" when no record exists | Unit test |
| 4 | Today card shows check-in time when checked in (not yet checked out) | Unit test |
| 5 | Today card shows check-in + check-out times when completed | Unit test |
| 6 | Check-in button triggers `POST /api/attendance/me/check-in` | Unit test (mock fetch) |
| 7 | Check-out button triggers `POST /api/attendance/me/check-out` | Unit test (mock fetch) |
| 8 | Blocked network shows exact backend `detail` message in destructive state | Unit test |
| 9 | History list shows current employee's records only (no other employee data visible) | Integration: API returns scoped records |
| 10 | No edit or delete controls exist on attendance page | Manual audit |
| 11 | Desktop and mobile layouts have no text overlap or horizontal scroll (except table) | Visual check + Playwright |
| 12 | Badge states match spec: loading/empty/checked-in/completed/error | Unit test |

---

## Implementation Sequence

### Backend (prerequisite)

1. Add `GET /api/attendance/me/history` endpoint to `router.py` with `month` query param.
2. Add `HistoryResponse` schema to `schemas.py`.
3. Wire into existing `attendance_router`.

### Frontend

1. Add `Clock` import to `employee-navigation.ts` and `ess-nav-config.ts`.
2. Create `frontend/src/app/(employee)/employee/attendance/page.tsx`.
3. Create `frontend/src/hooks/use-attendance.ts` (today record + history data fetching hook).
4. Implement Today Card component with all states.
5. Implement History Table component.
6. Add Vitest tests for state rendering and action calls.
7. Visual test: desktop and mobile.

---

## Not In Scope

- HR correction flow (ADR-0010: HR can correct with audit log — separate feature)
- GPS/device tracking
- Shift scheduling
- Overtime calculation
- Payslips (phase-2 per ADR-0016)
- Employee Assistant integration (phase-2)
- Real-time polling (manual refresh only)

---

## Files to Modify/Create

| File | Action |
|---|---|
| `frontend/src/lib/employee-navigation.ts` | Add Attendance nav item |
| `frontend/src/lib/ess-nav-config.ts` | Add Attendance link + activeRoute |
| `frontend/src/app/(employee)/employee/attendance/page.tsx` | Create |
| `frontend/src/hooks/use-attendance.ts` | Create (optional, can inline) |
| `backend/src/modules/attendance/api/router.py` | Add `/me/history` endpoint |
| `backend/src/modules/attendance/api/schemas.py` | Add `HistoryResponse` |
