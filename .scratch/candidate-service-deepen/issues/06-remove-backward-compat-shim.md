# 06 — Refactor test support: remove CandidateService backward-compat shim

**What to build:** Update `_interview_support.py` and `test_interview_support_smoke.py` to use `InterviewSchedulerService` instead of the old `CandidateService`, then delete `candidate_service.py`. This removes the last 3042 lines of dead production code.

**Blocked by:** 05 — Contract (must complete first)

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] `_interview_support.py`:
  - `build_calendar_harness()` creates an `InterviewSchedulerService` instance instead of `CandidateService`
  - `CalendarServiceHarness.service` type changed to `InterviewSchedulerService`
  - Constructor params updated: add `interview_repo=AsyncMock()`, remove `cv_document_repo`, `minio_client`, `oauth_grant_repo`, `oauth_service`
  - `monkeypatch.setattr(candidate_service, "log_audit", ...)` → target `interview_scheduler_service` instead
- [ ] `test_interview_support_smoke.py`:
  - `from src.modules.recruitment.application import candidate_service` → `interview_scheduler_service`
  - `candidate_service.log_audit` → `interview_scheduler_service.log_audit`
  - `candidate_service.CalendarPort` → import directly from `interview_scheduler_service`
- [ ] `test_publisher_enqueue_integration.py` (onboarding test):
  - `from ...candidate_service import CandidateService` → `from ...candidate_lifecycle_service import CandidateLifecycleService`
  - `CandidateService(...)` → `CandidateLifecycleService(...)` with updated constructor
- [ ] `backend/src/modules/recruitment/application/candidate_service.py` deleted
- [ ] All test files that import from `candidate_service` updated (grep to confirm zero remaining imports)
- [ ] `ruff check --fix` và `ruff format` chạy clean
- [ ] `python -m pytest tests/modules/recruitment/ -q --tb=no` — test count không giảm so với baseline

## Instructions
1. Dùng skill implement
2. Lưu ý: 22 interview property tests đang FAIL pre-existing — đừng cố fix chúng, chỉ update imports
3. Báo cáo code-review result + test summary
