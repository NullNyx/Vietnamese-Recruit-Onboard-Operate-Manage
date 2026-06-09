# 0014 Job Openings Are Optional Recruitment Planning Around Candidates

Date: 2026-06-09

## Status

Accepted

## Context

The project's Backbone Flow already creates Candidates directly from Gmail/CV parsing, and those Candidates can proceed through review, interview scheduling, acceptance, and onboarding without any prior planning object. The team wants a recruitment-planning surface large enough to parallelize work, but making Candidate creation depend on a planning entity would disrupt the existing backbone and add avoidable intake friction.

## Decision

Model recruitment planning as a `Job Opening` inside the recruitment module, not as a new top-level module and not as a required parent of Candidate. A Job Opening is an optional planning object for one Position; Candidates may remain unassigned or be assigned to exactly one open Job Opening, and accepted Candidates count against that Job Opening's headcount. Job Openings support draft/open/closed/cancelled lifecycle management, manual HR assignment, and reporting/grouping around the existing Candidate pipeline, but they do not replace or alter the Backbone Flow.

## Alternatives Considered

1. **Require every Candidate to belong to a Job Opening.** Rejected: conflicts with the existing Gmail/CV-driven intake flow and would make Job Opening a hard gate in the backbone.
2. **Create a separate recruitment-planning module.** Rejected for now: adds another boundary before the concept has enough weight to justify one, while the main behavior still centers on Candidate.
3. **Store Job Opening in the employee module because it references Position.** Rejected: the concept is about recruiting Candidates, not managing Employees.

## Consequences

- Recruitment planning can be built in parallel without destabilizing current Candidate intake.
- HR can use Job Openings for headcount tracking and candidate grouping while preserving the current Candidate status machine.
- Assignment history relies on audit logs in the first slice rather than a dedicated history model.
