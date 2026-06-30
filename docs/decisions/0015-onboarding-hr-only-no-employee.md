# 0015 Onboarding Is HR-Only; Employee Is Out of Scope

Date: 2026-06-30

## Status

Accepted

## Context

During the design-documentation cycle, the team reviewed how Vroom HR models onboarding. Two patterns were considered:

1. **Candidate → Employee → Onboarding active**: A Candidate is converted into an Employee record when accepted. Onboarding tracks the Employee through state transitions. This was the earlier approach, reflected in existing docs and partial backend work.

2. **Candidate → Onboarding Case → HR processes → Complete**: Onboarding stays in its own domain. An Onboarding Case wraps all activities. No Employee record is created during onboarding. The case stays in Onboarding domain until HR marks it done.

The shift was driven by the project's HR-only scope. The thesis báo cáo and ChatGPT reviews consistently pushed toward:

- HR is the only actor.
- The system helps HR do onboarding work faster.
- Employee lifecycle (self-service, portal, payroll) is not part of scope.
- Modeling Employee state during onboarding would pull employee-facing features into scope without justification.

## Decision

Onboarding is HR-only. No Employee record is created during onboarding.

Specifically:

- Onboarding Case is the root entity for the onboarding process.
- Candidate stays a Candidate until HR closes the case.
- No Employee creation or lifecycle logic is triggered during onboarding.
- Employee self-service / portal / lifecycle are out of scope for MVP.
- Future expansion to employee-assisted flows (if any) would require a new ADR.

## Alternatives Considered

1. **Create Employee immediately and track onboarding on Employee.** Rejected: drags employee lifecycle concerns into onboarding. The thesis scope is specifically HR operations, not employee management.
2. **Use Employee as actor for some onboarding steps (IT provision, manager welcome).** Rejected: the system does not have real employee login. The workflow labels exist only as task labels for HR to coordinate.

## Consequences

Positive:

- Clean domain boundary. Onboarding stays decoupled from employee lifecycle.
- Simpler data model: no Employee entity dependency during onboarding.
- Aligned with thesis scope: HR-only HR tool, not an HRM suite.
- Easier to explain in defense: "system helps HR onboard employees" vs "system manages employee lifecycle".

Tradeoffs:

- If a future phase adds employee-facing features (self-service, portal), the model needs rework.
- No reusable employee lifecycle infrastructure from onboarding — future employee features are a new vertical.
- The backend module `employee/` remains unused in onboarding flow, and its scope may need revisiting separately.

## Follow-Up

- Keep Flow Docs, Data Model, UX, and Acceptance Criteria consistent: no Employee creation during onboarding.
- The existing `employee/` backend module should be reviewed for consistency with this ADR.
- If any doc or code still refers to "Employee active" during onboarding, update to use Onboarding Case completion instead.
