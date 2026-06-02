# Backend Onboarding Module — Analysis

## Overview

The onboarding module is part of the **Backbone Flow**: Email → Gmail → Recruitment → Candidate accepted → **Onboarding** → Employee active. It's a self-hosted HRM system (one deployment = one company).

## Architecture

```
backend/src/modules/onboarding/
├── api/
│   ├── router.py              ← 3 endpoints (list, detail, patch task)
│   ├── schemas.py             ← Pydantic response/request models
│   └── error_handler.py       ← FastAPI exception handler
├── application/
│   ├── onboarding_service.py  ← Core logic (create, complete_task, list, detail)
│   ├── active_employee_query.py ← Guard for employee access
│   └── validators.py          ← Event payload validation
├── domain/
│   ├── entities.py            ← SQLModel tables (Process, Task, AuditLog)
│   ├── enums.py               ← Status + CHECKLIST_TEMPLATE (4 tasks)
│   └── exceptions.py          ← Error hierarchy
├── infrastructure/
│   ├── process_repository.py  ← CRUD for OnboardingProcess
│   ├── task_repository.py     ← CRUD for OnboardingTask
│   ├── audit_repository.py    ← Audit log append-only
│   └── config.py              ← Settings from env
├── container.py               ← DI wiring + ARQ consumer
└── worker.py                  ← ARQ worker config
```

## Data Model

### Tables

| Table | Purpose |
|-------|---------|
| `onboarding_processes` | One row per candidate. Links to Employee. Status: `in_progress` / `complete` |
| `onboarding_tasks` | 4 fixed tasks per process. Status: `pending` / `done` |
| `onboarding_audit_logs` | Append-only. Records every state change |

### CHECKLIST_TEMPLATE (4 tasks, fixed order)

| # | Key | Display Name |
|---|-----|--------------|
| 0 | `sign_contract` | Sign Contract |
| 1 | `submit_documents` | Submit Documents |
| 2 | `assign_department_position_manager` | Assign Department Position Manager |
| 3 | `set_start_date` | Set Start Date |

### Employee Creation

When a process is created, an `Employee` record is also created with:
- `is_active = False` (inactive, onboarding in progress)
- Auto-generated `employee_code` (NV-XXX format)
- `candidate_id` linked back to the source Candidate

When all 4 tasks are `done`:
- Process status → `complete`
- Employee `is_active = True`
- Employee becomes visible in Employee module

## API Endpoints

### 1. GET /api/onboarding/processes
- **Auth**: Admin only (`require_admin`)
- **Query params**: `status` (in_progress|complete), `page`, `page_size` (max 50)
- **Response**: Paginated list with `completed_count / total_count` progress
- **Missing**: `employee_full_name`, `employee_email` in response

### 2. GET /api/onboarding/processes/{process_id}
- **Auth**: Admin only
- **Response**: Process detail + ordered task checklist
- **Missing**: `employee_full_name`, `employee_email` in response

### 3. PATCH /api/onboarding/tasks/{task_id}
- **Auth**: Any authenticated user, but service checks `admin` role (403 if not)
- **Body**: `{ "status": "done" }` or `{ "status": "pending" }`
- **Behavior**: When last pending task → done, auto-completes process + activates employee
- **Missing**: Nothing critical, works correctly

## Event Flow (Backbone Flow segment)

```
1. Candidate accepted in Recruitment module
2. Recruitment emits "candidate_accepted" event via ArqDomainEventPublisher
3. ARQ job "process_candidate_accepted" enqueued
4. Onboarding worker consumes job:
   a. Validate event payload (candidate_id, name, email)
   b. Reject malformed events → audit log
   c. Call OnboardingService.start_from_event()
      - Create Employee (is_active=False)
      - Create OnboardingProcess
      - Create 4 CHECKLIST_TEMPLATE tasks
      - Write creation audit log
   d. Commit all in single transaction
   e. Idempotent: duplicate candidate_id → return existing process
```

## Issues / Missing for Frontend UI

### Critical (blocker)

| Issue | Impact | Fix |
|-------|--------|-----|
| Response lacks `employee_full_name` | UI shows UUID instead of name | Add to `ProcessListItem` + `ProcessDetail` read models |
| Response lacks `employee_email` | UI can't show contact info | Same as above |
| Response lacks `employee_code` | UI can't show NV-XXX code | Same as above |

### Required backend patch (minimal, allowed per spec)

The spec explicitly allows: "Patch nhỏ được phép: bổ sung `employee_full_name`, `employee_email`, `employee_code` vào response — chỉ là read response enrichment, không đổi domain flow."

**What needs to change:**

1. **Read models** in `onboarding_service.py`:
   - `ProcessListItem` → add `employee_full_name`, `employee_email`, `employee_code`
   - `ProcessDetail` → add same fields
   - Service needs to JOIN or fetch Employee data

2. **Schemas** in `schemas.py`:
   - `OnboardingProcessListItem` → add new fields
   - `OnboardingProcessDetailResponse` → add new fields

3. **Router** in `router.py`:
   - Map new fields from service read-model to response schema

### Not blockers but needed for full E2E

| Issue | Impact |
|-------|--------|
| CORS: frontend calls `http://localhost:8000` directly | Must use Next.js proxy (`/api/...` relative) or add CORS to backend |
| No `GET /api/onboarding/processes?employee_id=X` filter | Can't filter by specific employee |
| No task description field | Tasks only have `name`, no `description` |

## Self-hosted constraints

- One deployment = one company
- `tenant_id` is legacy, effectively constant
- No multi-tenancy
- Auth via Google OAuth → cookie-based JWT
- Admin role required for onboarding operations
- All admin actions write audit logs

## Summary

Backend onboarding module is **functionally complete** for the core flow. The only gap for frontend UI is the missing employee identity fields (`full_name`, `email`, `employee_code`) in list/detail responses. This is a read-only enrichment patch — no domain logic changes needed.
