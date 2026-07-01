# 0017 Self-Host Setup Flow

Date: 2026-07-01

## Status

Accepted

## Context

Vroom HR is self-hosted per company. When a new deployment is installed, the system must guide the first admin through Organization setup before normal login is allowed. The setup must be a one-time wizard that configures Organization basics, access control, and Google OAuth, then locks itself permanently.

## Decision

Implement a DB-backed setup flow with a wizard UI:

- **Detection**: `OrganizationSettings.setup_completed_at` is NULL → system not initialized → redirect to `/setup`.
- **Wizard steps**: Welcome → Organization Basics → Access Control → Identity Provider → Review → Lock.
- **Access control**: Use `allowed_domains` as primary gate. `WhitelistEntry` (exact email) becomes exception that overrides domain rules.
- **OAuth config**: Env vars remain primary (security); DB stores optional override values. If DB has values, they take precedence over env for runtime.
- **Lock**: After Review step, set `setup_completed_at = now()` and disable `/setup` route.
- **Bootstrap fallback**: `whitelist.txt` is only loaded on first-run if it exists and DB is empty. After first-run, DB is source of truth.

## Alternatives Considered

1. **Keep file-based whitelist as production source.** Rejected: file editing requires deployment/config reload; DB-backed is more manageable for HR.
2. **Store OAuth secrets in DB.** Rejected: secrets should not be stored plaintext; env vars are more secure for production.
3. **Skip wizard, use env vars for all config.** Rejected: violates "no manual config file editing" requirement.

## Consequences

Positive:

- Single admin can self-host without editing config files.
- Setup runs once and locks permanently.
- Access control is manageable at runtime via admin UI.

Tradeoffs:

- Must implement migration for existing file-based whitelist entries.
- Frontend wizard requires new UI routes and state management.
- Need to handle edge case: super admin email must be in allowed domains or whitelist.
