# 04 — Build CandidateNotificationService + Migrate notification callers

**What to build:** Create CandidateNotificationService responsible for sending emails to candidates. Migrate the `send_email_to_candidate` endpoint from CandidateService to the new service. CandidateService's notification method becomes dead code.

**Blocked by:** 01 — Prefactor (candidate_validators.py + InterviewRepository)

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] `recruitment/application/candidate_notification_service.py` created with:
  - `send_email_to_candidate(candidate_id, subject, body_html)` — sends email via Gmail
  - Constructor: CandidateRepository, GmailSendProtocol, session, user_id
  - **No** CalendarPort, EventPublisher, InterviewRepository, MinIO client
- [ ] `container.py`: new `get_candidate_notification_service()` dep
- [ ] `candidate_router.py`: add `CandidateNotificationServiceDep`, use for send_email endpoint
- [ ] CandidateService.send_email_to_candidate becomes dead code (not called)
- [ ] New test file `tests/modules/recruitment/test_candidate_notification_service.py` covering:
  - Successful email send
  - GmailNotConnectedError handling
  - Invalid candidate email error handling
  - Email content formatting
