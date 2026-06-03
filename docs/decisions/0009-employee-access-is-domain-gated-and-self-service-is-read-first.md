# 0009 Employee Access Is Domain-Gated and Self-Service Is Read-First

Date: 2026-06-03

## Status

Accepted

## Context

Vroom HR is self-hosted per Organization, but each deployment still needs a clear
boundary between HR admin access and Employee access. The product must support
employee sign-in for active staff while preventing unrelated personal accounts
from entering the system. The team also needs a clean model for employee lifecycle
management: HR creates and manages Employee records, then activates or inactivates
those records as staff join or leave.

The agreed domain model is:

- Authentication uses Google OAuth.
- The authenticated email domain must be allowed by the Organization.
- HR provisions Employee access; login is not a public sign-up flow.
- Employee is a domain record; User is the auth-account concept.
- Active Employees use the self-service side of the system.
- Self-service is read-first for the current scope.

## Decision

Use Organization-level allowed email domains to gate Google OAuth sign-in for
Employees. HR manages the allowed domain list in Organization settings, and the
identity layer rejects logins whose email domain is not on that allowlist.

Keep Employee lifecycle and auth-account lifecycle separate:

- HR owns Employee activation and inactivation.
- Google OAuth establishes identity, but it does not create an Employee by
  itself.
- Employee self-service is a separate employee-facing surface from HR admin.
- The initial Employee self-service scope is read-first: personal information,
  internal documents, and employee-visible HR data such as attendance views.

## Alternatives Considered

1. **Open self-sign-up for any Google account.** Rejected: incompatible with a
   self-hosted corporate deployment and too permissive for enterprise use.
2. **Conflate User and Employee into one object.** Rejected: auth and HR are
   different domains and need different lifecycle rules.
3. **Make Employee self-service write-heavy from day one.** Rejected: increases
   scope and cross-module coupling before the access boundary is stable.

## Consequences

Positive:

- Access control matches the self-hosted company model.
- HR can onboard/offboard employees by changing active state without redesigning
  auth.
- HR and Employee surfaces stay separated, which keeps module boundaries clean.

Tradeoffs:

- Organization settings now own an extra access-control concern.
- Employee access depends on proper HR provisioning and domain setup.
- Self-service write flows remain deferred until the read boundary is stable.

## Follow-Up

- Implement Organization allowed-domain management in the admin/identity area.
- Implement OAuth domain gating in the auth flow.
- Define the first Employee self-service screens as read-only surfaces.
