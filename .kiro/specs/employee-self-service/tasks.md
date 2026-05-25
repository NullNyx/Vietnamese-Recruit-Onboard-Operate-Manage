# Implementation Plan: Employee Self-Service Portal

## Overview

This plan implements the Employee Self-Service (ESS) Portal by creating a new `self_service` backend module with ownership-guarded endpoints, extending the identity module for User-Employee linking via JWT claims, and building a dedicated `(employee)` frontend route group. Tasks are ordered to establish foundations first (auth linking, dependencies), then core services, then frontend, and finally integration wiring.

## Tasks

- [x] 1. Extend Identity Module for User-Employee Linking
  - [x] 1.1 Modify TokenService to include employee_id in JWT claims
    - Update `create_access_token` to accept optional `employee_id: UUID | None` parameter
    - Include `employee_id` in JWT payload when provided
    - Update `TokenPayload` model to include optional `employee_id` field
    - Update `verify_access_token` to extract `employee_id` from token
    - _Requirements: 1.3_

  - [x] 1.2 Modify OAuth callback to resolve User-Employee link at login
    - After user is authenticated, query `employees` table by matching `users.email = employees.email`
    - Only link if the employee record has `is_active = True`
    - Pass resolved `employee_id` (or None) to `create_access_token`
    - _Requirements: 1.1, 1.2_

  - [ ]\* 1.3 Write property test for User-Employee link resolution
    - **Property 1: User-Employee Link Resolution**
    - **Validates: Requirements 1.1, 1.3**

- [x] 2. Create Self-Service Module Foundation
  - [x] 2.1 Create module directory structure and boilerplate
    - Create `src/modules/self_service/` with `__init__.py`, `container.py`
    - Create `api/` subdirectory with `__init__.py`, `router.py`, `dependencies.py`, `schemas.py`
    - Create `application/` subdirectory with `__init__.py`
    - _Requirements: 12.1_

  - [x] 2.2 Implement `get_current_employee` dependency
    - Extract JWT from `access_token` cookie
    - Verify token via existing TokenService
    - Extract `employee_id` from token claims
    - Return 401 if no token or invalid token
    - Return 403 with `NO_EMPLOYEE_LINK` code if no `employee_id` in claims
    - _Requirements: 1.4, 12.1, 12.5_

  - [x] 2.3 Implement rate limiting middleware for ESS endpoints
    - Use Redis sliding window (sorted set) with key `rate_limit:ess:{employee_id}`
    - Limit to 60 requests per minute per employee
    - Return 429 with `Retry-After` header when exceeded
    - _Requirements: 12.3_

  - [ ]\* 2.4 Write property test for ownership enforcement
    - **Property 2: Ownership Enforcement**
    - **Validates: Requirements 1.4, 4.1, 4.5, 6.4, 7.3, 8.4, 9.1, 9.3, 12.1, 12.2**

- [x] 3. Implement Pydantic Schemas and Utility Functions
  - [x] 3.1 Define all ESS Pydantic request/response schemas
    - `ESSProfileResponse`, `ESSProfileUpdateRequest`
    - `ESSAttendanceRecordResponse`, `ESSAttendanceSummaryResponse`
    - `ESSLeaveRequestCreate`, `ESSLeaveRequestResponse`, `ESSLeaveBalanceResponse`
    - `ESSOvertimeRequestCreate`, `ESSOvertimeRequestResponse`
    - `ESSDocumentResponse`, `ESSScheduleResponse`
    - `ESSDashboardResponse` with `AttendanceStatusEnum`
    - _Requirements: 2.1, 3.1, 3.2, 4.3, 4.4, 6.1, 8.1, 8.2, 9.1, 11.1_

  - [x] 3.2 Implement sensitive field masking utility
    - Create masking function: for strings of length N ≥ 4, replace first (N-4) chars with `*`, preserve last 4
    - For strings shorter than 4 characters, mask entirely
    - Apply to `id_number` and `tax_code` in profile response
    - _Requirements: 2.2_

  - [ ]\* 3.3 Write property test for sensitive field masking
    - **Property 3: Sensitive Field Masking**
    - **Validates: Requirements 2.2**

  - [ ]\* 3.4 Write property test for Vietnamese phone number validation
    - **Property 6: Vietnamese Phone Number Validation**
    - **Validates: Requirements 3.2**

  - [ ]\* 3.5 Write property test for planned hours range validation
    - **Property 16: Planned Hours Range Validation**
    - **Validates: Requirements 8.2**

- [x] 4. Implement Profile Service and Router
  - [x] 4.1 Implement `ess_profile_service.py`
    - `get_profile(employee_id)`: fetch employee with department/position joins, mask sensitive fields
    - `update_profile(employee_id, data)`: validate allowlist {phone, address, emergency_contact}, reject restricted fields with 403
    - Record `updated_at` timestamp on update
    - _Requirements: 2.1, 2.2, 3.1, 3.3, 3.4_

  - [x] 4.2 Implement `profile_router.py` with GET and PATCH endpoints
    - `GET /api/v1/ess/profile` → return masked profile
    - `PATCH /api/v1/ess/profile` → update allowed fields only
    - Wire `get_current_employee` dependency
    - _Requirements: 2.1, 2.3, 3.1_

  - [ ]\* 4.3 Write property tests for profile
    - **Property 4: Response Field Completeness (profile portion)**
    - **Property 5: Profile Update Allowlist Enforcement**
    - **Validates: Requirements 2.1, 3.1, 3.3**

- [x] 5. Implement Attendance Service and Router
  - [x] 5.1 Implement `ess_attendance_service.py`
    - `get_today_status(employee_id)`: return today's attendance record or None
    - `check_in(employee_id)`: create record with server timestamp, reject if already checked in (409)
    - `check_out(employee_id)`: update record with check-out time, calculate work_hours, reject if not checked in (409)
    - `get_history(employee_id, month, year)`: return filtered records with monthly summary
    - Calculate work_hours = (check_out - check_in) - break_minutes, minimum 0
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 Implement `attendance_router.py` with all attendance endpoints
    - `GET /api/v1/ess/attendance/today`
    - `POST /api/v1/ess/attendance/check-in`
    - `POST /api/v1/ess/attendance/check-out`
    - `GET /api/v1/ess/attendance/history?month=&year=`
    - Wire ownership guard via `get_current_employee`
    - _Requirements: 4.1, 4.2, 4.5, 5.1, 5.5_

  - [ ]\* 5.3 Write property tests for attendance
    - **Property 7: Attendance Date Filter Consistency**
    - **Property 8: Monthly Summary Consistency**
    - **Property 9: Check-in Idempotence**
    - **Property 10: Work Hours Calculation**
    - **Validates: Requirements 4.2, 4.4, 5.2, 5.3, 11.3**

- [x] 6. Checkpoint - Backend core services
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Leave Service and Router
  - [x] 7.1 Implement `ess_leave_service.py`
    - `get_balances(employee_id)`: return all leave type balances for current year
    - `get_requests(employee_id)`: return all leave requests for employee
    - `create_request(employee_id, data)`: validate balance, validate dates (no past start_date, end_date >= start_date), create with status "pending"
    - `cancel_request(employee_id, request_id)`: verify ownership, verify status is "pending", update to "cancelled"
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.1, 7.2_

  - [x] 7.2 Implement `leave_router.py` with all leave endpoints
    - `GET /api/v1/ess/leave/balances`
    - `GET /api/v1/ess/leave/requests`
    - `POST /api/v1/ess/leave/requests`
    - `POST /api/v1/ess/leave/requests/{id}/cancel`
    - _Requirements: 6.1, 6.4, 6.5, 7.1, 7.3_

  - [ ]\* 7.3 Write property tests for leave
    - **Property 11: New Request Status Invariant (leave)**
    - **Property 12: Leave Balance Enforcement**
    - **Property 13: Cancellation State Machine (leave)**
    - **Property 14: Date Validation (No Past Dates, leave)**
    - **Property 15: Leave Balance Arithmetic Invariant**
    - **Validates: Requirements 6.1, 6.3, 6.5, 6.6, 6.7, 7.1**

- [x] 8. Implement Overtime Service and Router
  - [x] 8.1 Implement `ess_overtime_service.py`
    - `get_requests(employee_id)`: return all overtime requests for employee
    - `create_request(employee_id, data)`: validate planned_hours [0.5, 4.0], validate work_date not in past, create with status "pending"
    - `cancel_request(employee_id, request_id)`: verify ownership, verify status is "pending", update to "cancelled"
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 8.2 Implement `overtime_router.py` with all overtime endpoints
    - `GET /api/v1/ess/overtime/requests`
    - `POST /api/v1/ess/overtime/requests`
    - `POST /api/v1/ess/overtime/requests/{id}/cancel`
    - _Requirements: 8.1, 8.4, 8.5_

  - [ ]\* 8.3 Write property tests for overtime
    - **Property 11: New Request Status Invariant (overtime)**
    - **Property 13: Cancellation State Machine (overtime)**
    - **Property 14: Date Validation (No Past Dates, overtime)**
    - **Validates: Requirements 8.1, 8.3, 8.5, 8.6**

- [x] 9. Implement Document and Schedule Services and Routers
  - [x] 9.1 Implement `document_router.py` with document endpoints
    - `GET /api/v1/ess/documents?document_type=` → list own documents with ownership guard
    - `GET /api/v1/ess/documents/{id}/download` → generate MinIO pre-signed URL (15-min expiry), verify ownership
    - Delegate to existing EmployeeService/document repository
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 9.2 Implement `schedule_router.py` with schedule endpoint
    - `GET /api/v1/ess/schedule` → return active work schedule for employee
    - Include upcoming holidays from holidays table
    - Return message if no schedule assigned
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ]\* 9.3 Write property test for document type filter
    - **Property 17: Document Type Filter Consistency**
    - **Validates: Requirements 9.4**

- [x] 10. Implement Dashboard Service and Router
  - [x] 10.1 Implement `ess_dashboard_service.py`
    - Aggregate: today's attendance status, pending leave/overtime counts, monthly summary, annual leave remaining
    - Map attendance status: no record → "not_checked_in", check_in only → "checked_in", both → "checked_out"
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 10.2 Implement `dashboard_router.py`
    - `GET /api/v1/ess/dashboard` → return aggregated dashboard data
    - _Requirements: 11.1, 11.5_

  - [ ]\* 10.3 Write property tests for dashboard
    - **Property 18: Dashboard Attendance Status Mapping**
    - **Property 19: Dashboard Pending Request Counts**
    - **Validates: Requirements 11.1, 11.2**

- [x] 11. Wire ESS Module into Application
  - [x] 11.1 Create main ESS router aggregating all sub-routers
    - Import and include all sub-routers (profile, attendance, leave, overtime, document, schedule, dashboard)
    - Apply rate limiting dependency to all routes
    - Set prefix `/api/v1/ess`
    - _Requirements: 12.1, 12.3_

  - [x] 11.2 Register ESS router in FastAPI application (`main.py`)
    - Import ESS router and include in app
    - Add audit logging middleware for ESS endpoints
    - _Requirements: 12.4_

  - [x] 11.3 Set up DI container for self_service module
    - Wire ESS services with existing service dependencies (EmployeeService, AttendanceService, LeaveService, OvertimeService)
    - Configure Redis client for rate limiter
    - _Requirements: 12.1_

- [x] 12. Checkpoint - Backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement Frontend Employee Layout and Middleware
  - [x] 13.1 Create `(employee)` route group layout
    - Create `frontend/src/app/(employee)/layout.tsx` with employee sidebar navigation
    - Include links: Dashboard, Profile, Attendance, Leave, Overtime, Documents, Schedule
    - Add employee name/avatar display from token
    - Create `frontend/src/app/(employee)/page.tsx` redirecting to `/employee/dashboard`
    - _Requirements: 1.2_

  - [x] 13.2 Enhance Next.js middleware for employee route protection
    - Check `access_token` cookie presence for `/employee/*` routes
    - Redirect to login if no token
    - Allow API 403 responses to handle employee_id validation
    - _Requirements: 12.1, 12.5_

- [x] 14. Implement Frontend Pages - Dashboard and Profile
  - [x] 14.1 Implement Dashboard page
    - Create `frontend/src/app/(employee)/dashboard/page.tsx`
    - Display today's attendance status with check-in/out action buttons
    - Show pending leave and overtime request counts
    - Show monthly attendance summary
    - Show annual leave remaining
    - Fetch from `GET /api/v1/ess/dashboard`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 14.2 Implement Profile page
    - Create `frontend/src/app/(employee)/profile/page.tsx`
    - Display all profile fields with masked sensitive data
    - Editable form for phone, address, emergency_contact
    - Vietnamese phone validation on client side
    - Fetch from `GET /api/v1/ess/profile`, submit to `PATCH /api/v1/ess/profile`
    - _Requirements: 2.1, 2.2, 3.1, 3.2_

- [x] 15. Implement Frontend Pages - Attendance
  - [x] 15.1 Implement Attendance page
    - Create `frontend/src/app/(employee)/attendance/page.tsx`
    - Check-in / Check-out buttons with status display
    - Monthly attendance history table with month/year filter
    - Monthly summary section (total days, hours, overtime, late, early)
    - Fetch from attendance ESS endpoints
    - _Requirements: 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_

- [x] 16. Implement Frontend Pages - Leave Management
  - [x] 16.1 Implement Leave requests list page
    - Create `frontend/src/app/(employee)/leave/page.tsx`
    - Display leave requests with status badges
    - Cancel button for pending requests
    - Show leave balances summary
    - _Requirements: 6.2, 6.4, 6.5, 7.1, 7.2_

  - [x] 16.2 Implement New Leave Request page
    - Create `frontend/src/app/(employee)/leave/new/page.tsx`
    - Form with leave type selector, date range picker, reason field
    - Show available balance for selected type
    - Client-side date validation (no past dates, end >= start)
    - _Requirements: 6.1, 6.3, 6.7_

- [x] 17. Implement Frontend Pages - Overtime and Documents
  - [x] 17.1 Implement Overtime requests list page
    - Create `frontend/src/app/(employee)/overtime/page.tsx`
    - Display overtime requests with status badges
    - Cancel button for pending requests
    - _Requirements: 8.4, 8.5_

  - [x] 17.2 Implement New Overtime Request page
    - Create `frontend/src/app/(employee)/overtime/new/page.tsx`
    - Form with work_date picker, planned_hours input (0.5-4.0), reason field
    - Client-side validation for date and hours range
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 17.3 Implement Documents page
    - Create `frontend/src/app/(employee)/documents/page.tsx`
    - List documents with file name, type, size, upload date
    - Filter by document_type
    - Download button generating pre-signed URL
    - _Requirements: 9.1, 9.2, 9.4_

- [x] 18. Implement Frontend Pages - Schedule
  - [x] 18.1 Implement Schedule page
    - Create `frontend/src/app/(employee)/schedule/page.tsx`
    - Display work schedule (shift times, working days)
    - Show upcoming holidays
    - Handle "no schedule assigned" state
    - _Requirements: 10.1, 10.2, 10.3_

- [-] 19. Final Checkpoint - Full integration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis (Python)
- Backend uses Python (FastAPI, SQLAlchemy, Pydantic), frontend uses TypeScript (Next.js, Tailwind, shadcn/ui)
- All ESS endpoints reuse existing service layer with ownership guards — no new database tables required
- Rate limiting uses Redis sliding window at 60 req/min/employee
- The `get_current_employee` dependency is the single enforcement point for authentication and employee linking

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1"] },
    { "id": 1, "tasks": ["1.2", "2.2", "3.2"] },
    { "id": 2, "tasks": ["1.3", "2.3", "3.3", "3.4", "3.5"] },
    { "id": 3, "tasks": ["2.4", "4.1", "5.1", "7.1", "8.1"] },
    {
      "id": 4,
      "tasks": ["4.2", "4.3", "5.2", "5.3", "7.2", "7.3", "8.2", "8.3"]
    },
    { "id": 5, "tasks": ["9.1", "9.2", "9.3", "10.1"] },
    { "id": 6, "tasks": ["10.2", "10.3", "11.1"] },
    { "id": 7, "tasks": ["11.2", "11.3"] },
    { "id": 8, "tasks": ["13.1", "13.2"] },
    { "id": 9, "tasks": ["14.1", "14.2", "15.1"] },
    { "id": 10, "tasks": ["16.1", "16.2", "17.1", "17.2", "17.3"] },
    { "id": 11, "tasks": ["18.1"] }
  ]
}
```
