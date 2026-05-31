# 0008 Schedule Interviews Synchronously on the HR's Google Calendar

Date: 2026-05-31

## Status

Accepted

## Context

`CandidateService.schedule_interview` currently only flips the Candidate status
to `interview_scheduled`, emits an `interview_scheduled` domain event (which has
no consumer), and writes an audit entry — it never touches Google Calendar.
The OAuth flow already requests the `calendar.events` scope, but no code uses
it. The Backbone Flow (ADR-0002) names "interview scheduling" as a step, so the
real integration is the missing piece.

The onboarding link (the other event consumer in the backbone) was built
**async + atomic** via ARQ. For interview scheduling the team deliberately chose
a different shape, because the trade-offs differ: HR is interactively waiting on
the request and must know immediately whether the calendar invite went out, and
a failed Calendar call must not leave a Candidate marked `interview_scheduled`
with no actual meeting.

## Decision

Create the Google Calendar event **synchronously inside the
`schedule_interview` request**, on the calendar of the HR user performing the
action (their OAuth token, `calendar.events` scope).

- **Atomic**: if event creation fails, the Candidate does NOT transition to
  `interview_scheduled` (the whole operation rolls back). No orphan status.
- **One interview per Candidate**: store `calendar_event_id` plus the scheduled
  start/timezone on the `Candidate` entity. No new `Interview` entity and no new
  glossary term.
- **Reschedule** patches the existing Calendar event (Meet link preserved).
- **Reject/archive** of a scheduled Candidate cancels its Calendar event and
  audits the cancellation.
- **Missing Calendar grant** (`calendar_grant_valid = false`) blocks scheduling
  with a clear error and forces re-consent.
- **Google Meet** conferencing link is generated per interview.
- **Interviewer without an email** blocks scheduling (cannot be invited).
- The time contract changes to `start` (datetime) + `duration_minutes`, with the
  timezone taken from the Organization. This is a breaking change to the
  existing `ScheduleInterviewRequest` and its frontend caller.

## Alternatives Considered

1. **Async via the existing `interview_scheduled` event (mirror onboarding).**
   Rejected: HR would not learn of a Calendar failure during their request, and
   the loose string `date`/`time` payload is unsafe for a real calendar.
2. **A dedicated `Interview` entity supporting multiple rounds.** Deferred: adds
   a table and a new canonical term for a multi-round case the team does not need
   now; one-interview-per-candidate fits the current Backbone Flow.

## Consequences

Positive:

- HR gets immediate, truthful feedback; no orphaned `interview_scheduled`
  Candidates; no stale events left on the calendar after reschedule/reject.
- Reuses the existing per-user Google OAuth token, like Gmail send.

Tradeoffs:

- The `schedule_interview` request now depends on Google Calendar latency and
  availability.
- The `interview_scheduled` domain event remains without a consumer (kept for
  potential future use, not relied upon here).
- Breaking change to the schedule-interview API contract and its frontend.
- Multi-round interviews would require revisiting this decision.
