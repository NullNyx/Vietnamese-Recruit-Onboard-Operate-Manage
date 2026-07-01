# 0017 HR Ops Scope: Employee-Record-Centric, HR-Only

Date: 2026-06-30

## Status

Accepted

## Context

The original scoping decision (ADR-0002) narrowed the project to a single
recruit-to-onboard backbone flow. Design docs and thesis reviews consistently
pushed toward a broader product: not just recruitment, but a platform that helps
HR reduce manual work across all employee-related operations.

The earlier Employee Self-Service and Employee Assistant decisions
(ADR-0009–0016) assumed an employee-facing actor that is no longer in scope.

## Decision

- Employee Record is the root entity of the product.
- HR/Admin is the sole actor. No employee-facing actor, no employee login, no
  self-service surface.
- All HR operations (contracts, documents, attendance, leave, payroll,
  employment events) orbit the Employee Record.
- Recruitment + Onboarding is vertical slice 1, not the product boundary.
- Employee-facing features (self-service, portal, employee assistant) are out
  of scope for the foreseeable future. Any future employee-facing surface
  requires a new ADR.

## Consequences

Positive:

- One consistent actor model across all features.
- Employee Record becomes the shared foundation for every future vertical
  slice — field changes, audit, document tracking, contract lifecycle,
  attendance, payroll, offboarding.
- Clarity: the system helps HR do HR work, not replace employee tools.

Tradeoffs:

- Employee-provided data (leave requests, profile updates) must be entered or
  imported by HR, adding manual steps that a self-service portal could avoid.
- Future re-introduction of employee-facing surfaces would require rework.

## Supersedes

- ADR-0002 (Scope recruit-to-onboard backbone only)
- ADR-0009 (Employee access domain-gated)
- ADR-0010 (Office-network attendance records)
- ADR-0011 (Employee requests for leave and overtime)
- ADR-0012 (Read-only payslips before payroll engine)
- ADR-0013 (Employee assistant scoped and draft-only)
- ADR-0016 (Employee self-service read-first and phase-split)

## References

- ADR-0015 (Onboarding HR-only) remains active — onboarding still does not
  create Employee records.
- docs/design-docs/employee-record-contracts-slice.md
