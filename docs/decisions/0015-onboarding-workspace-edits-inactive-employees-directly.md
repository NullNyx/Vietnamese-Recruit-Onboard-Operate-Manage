# 0015 Onboarding Workspace Edits Inactive Employees Directly

Date: 2026-06-09

## Status

Accepted

## Context

The project already models Onboarding as the process that turns an accepted Candidate into an active Employee, and the live backend/frontend already expose an Onboarding process list/detail workspace. The team wants to deepen that surface without turning Onboarding into a separate document system or a second Employee editor.

## Decision

Keep Onboarding as a process-first workspace that starts only after Candidate acceptance. The workspace edits the inactive Employee record directly for the core setup fields (`department`, `position`, `manager`, `start_date`), while OnboardingProcess remains the progress record that tracks checklist completion and activation readiness. `Manager` is a reporting relationship between Employees, not a system role. When all onboarding tasks are done and the required setup data is present, the process completes and activates the Employee in the same step; after that, the workspace becomes read-only.

## Alternatives Considered

1. **Store onboarding setup in a staging object on OnboardingProcess.** Rejected: duplicates Employee state and adds sync complexity.
2. **Make Onboarding Workspace read-only and push edits to the Employee screen.** Rejected: weakens the workspace and splits the onboarding flow across surfaces.
3. **Make Sign Contract / Submit Documents file-driven in the first slice.** Rejected: would pull document management into Onboarding and blur the boundary with the existing employee document surface.

## Consequences

- The workspace stays centered on process progress and completion, not on document vault management.
- Partial setup changes persist immediately on the inactive Employee; the process remains in progress until complete.
- Candidate context in the workspace is read-only and minimal.
