# 02 — Build CandidateLifecycleService + Migrate lifecycle callers

**What to build:** Create CandidateLifecycleService with lifecycle-only responsibilities. Migrate all lifecycle callers (router, context_builder, tool_registry, cv_processor, review_service) from CandidateService to CandidateLifecycleService. CandidateService still exists with interview methods untouched — CI stays green.

**Blocked by:** 01 — Prefactor (candidate_validators.py + InterviewRepository)

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] `recruitment/application/candidate_lifecycle_service.py` created with methods extracted from CandidateService:
  - `create_or_update_candidate(parsed_cv)` — implements CandidateCreator protocol
  - `get_candidate(candidate_id)` → CandidateDetail
  - `list_candidates(filters)` → PaginatedCandidates
  - `accept_candidate(candidate_id)` → publishes `candidate_accepted`
  - `reject_candidate(candidate_id, reason)`
  - `archive_candidate(candidate_id)`
  - `assign_candidate(candidate_id, job_opening_id)`
  - `reassign_candidate(candidate_id, new_job_opening_id)`
  - `unassign_candidate(candidate_id)`
  - Constructor: CandidateRepository, CVDocumentRepository, JobOpeningRepository, MinIO client, EventPublisher, session, user_id
  - **No** CalendarPort, GmailSender, GmailChecker, ConnectionRepo, Crypto
- [ ] `recruitment/__init__.py` re-exports CandidateLifecycleService
- [ ] `container.py`: new `get_candidate_lifecycle_service()` dep
- [ ] `candidate_router.py`: add `CandidateLifecycleServiceDep`, use it for:
  - accept/reject/archive endpoints
  - assign/reassign/unassign endpoints
  - get/list endpoints
  - CandidateService still used for interview endpoints (will be migrated in ticket 03)
- [ ] `assistant/context_builder.py`: import CandidateLifecycleService instead of CandidateService
- [ ] `assistant/tool_registry.py`: import CandidateLifecycleService instead of CandidateService
- [ ] `cv_processor.py`: `CandidateCreator` protocol bound to CandidateLifecycleService
- [ ] `review_service.py`: uses CandidateLifecycleService.create_or_update_candidate
- [ ] New test file `tests/modules/recruitment/test_candidate_lifecycle_service.py` covering all lifecycle paths
- [ ] Existing tests in `test_candidate_service.py` still pass (CandidateService unchanged)
