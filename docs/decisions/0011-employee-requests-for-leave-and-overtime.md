# 0011 Employee Requests for Leave and Overtime

Date: 2026-06-08

## Status

Accepted

## Context

ADR-0002 shelved leave, overtime, and approval workflows, but Employee
Self-Service now needs a demo-thin request flow. Leave and overtime have
different fields, but they share ownership, submission, review, cancellation,
and audit behavior.

## Decision

Model leave and overtime as two types of **Employee Request** with one shared
lifecycle: submitted, approved, rejected, and cancelled. Employees can submit
and cancel only their own submitted requests; HR reviews submitted requests and
approves or rejects them with audit logging. Manager approval, leave balances,
half-day leave, overtime pay calculation, and policy-engine enforcement remain
out of this slice.

## Consequences

- The request and approval surface stays small while supporting both leave and
  overtime demos.
- HR-only approval avoids introducing a Manager role before the domain needs it.
- Payroll and policy calculations remain separate future work rather than hidden
  dependencies of the request flow.
