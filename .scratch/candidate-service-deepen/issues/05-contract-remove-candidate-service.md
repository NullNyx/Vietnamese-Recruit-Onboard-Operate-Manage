# 05 — Contract: Remove CandidateService

**What to build:** Delete the old CandidateService class and its tests. Clean up container.py wiring. All callers already use CandidateLifecycleService, InterviewSchedulerService, and CandidateNotificationService.

**Blocked by:** 02, 03, 04 — all three new services must be live with no remaining callers on CandidateService

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] `recruitment/application/candidate_service.py` deleted
- [ ] `CandidateService` removed from `recruitment/__init__.py`
- [ ] `container.py`: remove `get_candidate_service()` and all CandidateService wiring in:
  - `get_review_service()` — uses CandidateLifecycleService directly
  - `get_cv_processor_service()` — uses CandidateLifecycleService directly
  - `arq_process_cv_from_email()` — uses CandidateLifecycleService directly
- [ ] `tests/modules/recruitment/test_candidate_service.py` deleted (replaced by test_*_service.py files)
- [ ] `conflict_router.py`: import CandidateService removed
- [ ] `candidate_router.py`: `CandidateServiceDep` removed, only new service deps remain
- [ ] `CandidateCreator` protocol in cv_processor.py points to `CandidateLifecycleService`
- [ ] All tests pass
- [ ] `ruff check --fix` và `ruff format` chạy clean
