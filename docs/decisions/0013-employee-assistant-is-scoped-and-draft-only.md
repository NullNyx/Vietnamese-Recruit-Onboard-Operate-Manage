# 0013 Employee Assistant Is Scoped and Draft-Only

Date: 2026-06-08

## Status

Superseded by HR-only assistant scope in newer design docs

## Context

The glossary originally defined the AI Assistant as an HR-facing capability and
deferred employee-side assistance with attendance and leave. Employee
Self-Service is now expanding with attendance, Employee Requests, and Payslips,
but autonomous employee actions would blur the existing human-in-the-loop safety
boundary.

## Decision

Implement the Employee Assistant as a scoped surface in the shared assistant
module. It can use only Employee-owned Read-Tools and Draft-Tools, such as
reading the active Employee's profile, documents, Attendance Records, Employee
Requests, and Payslips, or drafting leave and overtime Employee Requests. It
cannot submit requests, check in or out, edit profile data, download documents,
approve or reject requests, publish Payslips, or write to the database on its
own.

## Consequences

- HR and Employee assistant surfaces share architecture while keeping tool sets
  and authorization guards separate.
- Draft Actions stay human-in-the-loop: the Employee reviews a prefilled normal
  UI form before any write occurs.
- Employee-side AI remains a productivity surface, not an autonomous AI Agent.
