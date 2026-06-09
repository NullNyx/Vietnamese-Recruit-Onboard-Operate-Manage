# 0016 Employee Self-Service Is Read-First and Phase-Split

Date: 2026-06-09

## Status

Accepted

## Context

Employee Self-Service now needs a usable first surface without reopening payroll or a full autonomy model. The product already has a clear read boundary for active Employees, office-network-gated Attendance Records, and a separate draft-only Employee Assistant surface.

## Decision

Ship Employee Self-Service in two phases: phase 1 covers Home, Profile, Documents, Attendance, and Employee Requests; phase 2 adds Payslips and the Employee Assistant. The Home screen prioritizes quick actions and lightweight status cards over a dense summary view so the surface stays read-first and fast to scan.

## Consequences

- The first ESS release stays small enough to finish and verify.
- Payslips and assistant behavior remain separate from the core read-and-check-in flow.
- Future changes can extend the surface without redesigning the whole Employee area.
