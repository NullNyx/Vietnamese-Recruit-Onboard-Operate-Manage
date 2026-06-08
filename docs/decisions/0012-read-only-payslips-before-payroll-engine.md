# 0012 Read-Only Payslips Before Payroll Engine

Date: 2026-06-08

## Status

Accepted

## Context

ADR-0002 shelved payroll because full payroll calculation would pull in
attendance, overtime, leave, tax, insurance, and approval rules. Employee
Self-Service still benefits from a payroll-facing demo surface, but financial
calculation correctness is too risky for the next slice.

## Decision

Implement payroll first as read-only **Payslip** access. HR manually creates and
publishes Payslips with explicit payroll amounts; Employees can view only their
own published Payslips. Payroll runs, automatic calculation from attendance or
overtime, Excel import, dispute workflows, and employee edits remain out of
scope for this slice.

## Consequences

- Employees get a useful payroll surface without committing to a payroll engine.
- Saved payroll values are explicit and auditable rather than implied by partial
  calculations.
- Integrating attendance, overtime, Vietnamese tax, and insurance can be handled
  later as a deliberate Payroll Run decision.
