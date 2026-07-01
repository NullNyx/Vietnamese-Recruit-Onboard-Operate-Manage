# 0017 HR Operations Assistant, HR/Admin Only

Date: 2026-06-30

## Status

Accepted

## Context

The working docs shifted the product away from a single recruit-to-onboard
backbone and toward a broader HR operations assistant. The user-facing
employee side is out of scope. All product value comes from helping HR/Admin
manage HR tasks faster with lower error rates and better traceability.

## Decision

Treat HR/Admin as the only actor in the product. Do not build employee-facing
login, portal, or self-service flows. All write actions are owned by HR/Admin.
If employee-provided data exists in reality, HR/Admin receives it and enters or
syncs it into the system.

## Consequences

- The product stays focused on HR operations instead of splitting attention
  across two audiences.
- Product slices can grow by HR task family without introducing a second actor.
- Any future employee-facing surface would require a new decision.

## Supersedes

- 0009 Employee Access Is Domain-Gated and Self-Service Is Read-First
- 0010 Office-Network Attendance Records
- 0011 Employee Requests for Leave and Overtime
- 0012 Read-Only Payslips Before Payroll Engine
- 0013 Employee Assistant Is Scoped and Draft-Only
- 0015 Onboarding Is HR-Only; Employee Is Out of Scope
- 0016 Employee Self-Service Is Read-First and Phase-Split
