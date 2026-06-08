# 0010 Office-Network Attendance Records

Date: 2026-06-08

## Status

Accepted

## Context

ADR-0002 shelved attendance to keep the Backbone Flow small, but the Employee
Self-Service roadmap now needs a demo-thin attendance slice without reopening the
full Operate/Manage policy scope. The product needs a credible timekeeping flow
while avoiding GPS, mobile device tracking, biometrics, shift scheduling, and
policy-engine coupling.

## Decision

Implement attendance as an Employee-owned **Attendance Record** flow gated by the
Organization's approved office network. Employees can check in and check out only
for the current work date from an allowed office IP/CIDR range; timestamps are
stored in UTC, while the work date is derived from the Organization timezone.

Employee check-in/check-out is idempotent and no-overwrite. HR can correct
records with a required correction reason, and every correction writes an audit
log. Payroll, overtime calculation, GPS/device tracking, shift scheduling, and
automatic policy enforcement remain out of this attendance slice.

## Consequences

- Attendance is intentionally demo-thin and does not revive the shelved Policy
  Engine scope.
- Office-network gating gives a simple enterprise boundary, but remote work and
  mobile attendance require later decisions.
- Attendance records become an Employee Self-Service write flow, while HR keeps
  correction authority and audit responsibility.
