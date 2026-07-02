# 0019 Onboarding Becomes Ready for Completion Before HR Confirms Activation

Date: 2026-07-02

## Status

Accepted

## Context

Onboarding needs a clean boundary between checklist readiness and business
completion. If the system marks Onboarding Case completed the moment the last
task becomes done, the state machine starts to act on behalf of HR. The product
needs a workflow container that can say "ready to complete" without forcing the
final transition.

## Decision

When all Onboarding Task items are done, the Onboarding Case becomes
ready for completion. HR must explicitly confirm completion before the case is
marked completed and the linked Employee record is created or activated.

## Consequences

- Checklist progress and business completion stay separate.
- HR keeps the final business decision.
- The system can surface readiness without auto-closing the case.
