# 03 — Build InterviewSchedulerService + Migrate interview callers

**What to build:** Create InterviewSchedulerService responsible for interview lifecycle + Google Calendar integration + conflict detection. Migrate all interview callers (candidate_router, conflict_router) from CandidateService to InterviewSchedulerService. CandidateService interview methods become dead code.

**Blocked by:** 01 — Prefactor (candidate_validators.py + InterviewRepository)

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] `recruitment/application/interview_scheduler_service.py` created with methods extracted from CandidateService:
  - `schedule_interview(candidate_id, start, duration_minutes, interviewer_ids, notes)` → Interview
  - `reschedule_interview(interview_id, new_start, new_duration_minutes, force)`
  - `cancel_interview(interview_id, reason)`
  - `complete_interview(interview_id)`
  - `create_replacement_interview(candidate_id, cancelled_interview_id, ...)`
  - `list_interviews_for_candidate(candidate_id)` → list
  - `list_calendar_conflicts(start, end, candidate_id, exclude_interview_id)`
  - `resolve_calendar_conflict(conflict_id, resolution)`
  - Constructor: CandidateRepository, InterviewRepository, CalendarPort, OrgSettingsRepo, ConnectionRepo, TokenCipher, session, user_id
  - **No** GmailSender, EventPublisher, MinIO client
- [ ] `recruitment/__init__.py` re-exports InterviewSchedulerService
- [ ] `container.py`: new `get_interview_scheduler_service()` dep
- [ ] `candidate_router.py`: add `InterviewSchedulerServiceDep`, use it for:
  - schedule/reschedule/cancel/complete endpoints
  - create_interview, create_replacement_interview endpoints
  - InterviewParticipant queries (replaces raw `_session.execute()` leak)
- [ ] `conflict_router.py`: import InterviewSchedulerService, use for conflict listing + resolution
- [ ] `CandidateService` interview methods become dead code (not called by any router)
- [ ] New test file `tests/modules/recruitment/test_interview_scheduler_service.py` covering:
  - Schedule from NEW and REVIEWING statuses
  - Reschedule with conflict detection
  - Cancel/completer interview
  - Calendar event CRUD through CalendarPort
