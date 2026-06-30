# 0014 Workflow-Agnostic HR Assistant, Not a Process Engine

Date: 2026-06-30

## Status

Accepted

## Context

During the documentation pass for Vroom HR, the team had to choose between two product directions:

1. Model and enforce a standardized onboarding workflow for every company.
2. Provide HR with tools that reduce manual work while letting each company keep its own onboarding process.

The project target is a self-hosted, single-company deployment for Vietnamese enterprises. In practice, onboarding differs across companies:

- HR / Manager / IT coordination differs.
- Document requirements differ.
- Contract review and signing steps differ.
- Probation and review practices differ.
- Some companies want more reminders, others more manual control.

Hard-coding one workflow would make the system feel like a process engine and would force companies to adapt to the product instead of the product adapting to them.

## Decision

Vroom HR is a workflow-agnostic HR Assistant, not an HR Process Engine.

The system provides tools for:

- tracking
- reminding
- summarizing
- drafting
- checklist management
- template management

The system does not hard-code company-specific business workflows or approval logic.

Concretely:

- Onboarding is represented as an Onboarding Case, but completion is confirmed by HR according to company policy.
- Document requirements are template-driven, not globally fixed.
- Task categories are company-defined labels, not a universal process model.
- Deadlines and reminders are treated as tracking aids, not as enforcement of a universal workflow.
- Review / probation / performance steps are only modeled as reminders or tasks if a company wants them.

## Alternatives Considered

1. **Standardize onboarding as a process engine.** Rejected: too opinionated for a self-hosted per-company product and would force each company into a single workflow.
2. **Hard-code review / probation / risk rules.** Rejected: these rules vary too much by company and would create false assumptions in the product.
3. **Keep onboarding flow-free and only store files.** Rejected: would remove the core productivity value of the assistant.

## Consequences

Positive:

- Each company can keep its own onboarding policy and manual approval style.
- Product scope stays centered on HR productivity rather than workflow enforcement.
- Documents, tasks, and reminders can evolve without breaking core business logic.
- Lower risk of over-engineering state machines that do not fit all companies.

Tradeoffs:

- The system does not provide a single "golden path" onboarding workflow.
- Some operations remain HR-confirmed rather than automated.
- Reporting and completion rules are less standardized across deployments.

## Follow-Up

- Keep Flow Docs, Data Model, and Acceptance Criteria aligned to this principle.
- Avoid adding hard-coded business rules for company-specific onboarding steps unless a future ADR explicitly justifies it.
- If a future feature starts to enforce company workflow, write a new ADR first.
