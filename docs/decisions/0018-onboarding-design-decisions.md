# 0018 Onboarding Design Decisions

Date: 2026-07-01

## Status

Accepted

## Context

During the refinement of the Onboarding & Document Management slice, several design trade-offs emerged regarding scope, complexity, performance, and security. We needed to lock in decisions to keep the architecture clean and simple for the MVP while maintaining compatibility with future expansions.

## Decision

- **Task Scope:** `TaskTemplateItem` will only feature an `owner_label` (text label) instead of a complex assignee role or role-based access control (RBAC).
- **Draft Versioning:** `ContractDraft` changes will be tracked with a simple `revision` number. Full draft version history is out of scope for the MVP; major changes will be captured in the `AuditLog`.
- **Case Code Format:** `OnboardingCase.case_code` requires uniqueness only, with no fixed or restrictive formatting patterns enforced by default.
- **Document Extraction (AI):** Extraction will execute as an asynchronous background job. File uploads will remain non-blocking, and extraction progress will be tracked via states (`pending` → `processing` → `completed`/`failed`).
- **AI Draft Preview:** AI Draft tools will return structured JSON data as the source of truth, and the UI will handle rendering it to Markdown or HTML.
- **AI Summary Scope:** AI-generated summary reports will only display on the internal dashboard. Automatic email delivery is out of scope for the MVP.
- **AI Provider Configuration:** Configurable via both environment variables (for DevOps/deployment) and a settings UI (which encrypts credentials in the database for end-user convenience).
- **CSRF Protection:** Rely entirely on the framework's (FastAPI) built-in CSRF protection mechanisms instead of implementing a custom double-submit cookie pattern.

## Consequences

- **Minimalist Architecture:** Prevents scope creep by postponing complex RBAC, version-control UI, and workflow engines.
- **Better User Experience:** Non-blocking file uploads and visual extraction status tracking prevent HR from being blocked by slow AI processes.
- **Secure Configuration:** Provides flexibility for both production DevOps deployment and ease-of-use for less technical self-hosted administrators.
