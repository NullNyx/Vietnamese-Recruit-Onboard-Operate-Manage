# 0009 — Attendance & Payroll Default Decisions

## Status

Accepted

## Context

The attendance/payroll docs list 7 open questions. Since this is a self-hosted
platform, HR can configure everything at runtime — so most answers become
**sensible defaults** that HR can override through Settings. No question
requires a code-level fork.

## Decisions

### 1. MVP scope: Fixed hours, no shifts

MVP uses **Fixed** work model only. Shift and Flexible are Phase 2+.
Rationale: ~80% of Vietnamese office companies use fixed 08:00–17:00.
Shifts add significant complexity (assignment, rotation, per-shift OT rates)
that can wait.

### 2. Check-in methods: Web + QR in MVP, Device optional Phase 4

Web + QR Check-in ship in MVP. Device integration (fingerprint / face) is
Phase 4 (optional) — it requires hardware procurement that varies wildly per
company and is not needed for the core flow. HR decides if they need device.

### 3. Forgot check-in: HR edits directly

When an employee forgets to check in, HR edits the record directly via
Attendance → Records → Edit. No approval request flow is needed.
Rationale: small Vietnamese companies trust HR to fix this; an approval
workflow adds UI/API surface for negligible benefit.

### 4. Overtime: auto-calculated, no pre-registration

OT is calculated automatically from checkout time minus scheduled end.
Pre-registration is optional (HR can toggle it on in Settings if needed).
Rationale: most companies discover OT after the fact; forcing pre-registration
causes friction and data gaps.

### 5. Default payroll input: Gross

Default payroll mode is **Gross** (HR enters gross salary, system calculates
net). HR can switch to **Net** mode in Settings (system reverse-calculates
gross). This covers both conventions without code changes.

### 6. Pay cycle: once per month

Default pay cycle is **1 time / month**. HR can switch to **2 times / month**
(15th + month-end) in Settings. The payroll calculation engine is cycle-
agnostic; the setting controls which dates trigger the "chốt lương" workflow.

### 7. Allowances: fixed per month by default

Allowances default to **fixed monthly amount**. Per-day and percent-of-gross
are available options. HR defines each allowance with its own calculation
type — no hard-coded list.


### 8. Late/Early tolerance defaults

Default: **10 minutes** for both late arrival and early leave.
HR can configure per-company in Settings → Attendance → Hours.

### 9. Weekly off day

Default: **Saturday** (standard Vietnamese work week).
HR can change to Sunday or custom in Settings → Attendance → Days.

### 10. Device integration is optional

Device check-in (fingerprint/face) is NOT part of MVP. It ships in Phase 4
as an optional module — only companies with hardware devices need it.
Most companies will use Web + QR only.

## Consequences

- The 7 questions are removed from both docs and replaced with a "Defaults"
  table that HR can configure at runtime.
- ADR 0009 becomes the single source of truth for these choices.
- Any HR who disagrees with a default changes it in Settings — no code
  change required.
