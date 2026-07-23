# 01 — Prefactor: Extract candidate_validators.py + InterviewRepository

**What to build:** Extract pure functions and repository that will be shared by the new services, without changing any external behavior. CandidateService is refactored to use these internally — all existing tests pass unchanged.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] `recruitment/application/candidate_validators.py` created with:
  - `VALID_TRANSITIONS` dict (moved from `candidate_service.py`)
  - `_validate_transition(current_status, target_status, action)` function
  - `validate_candidate_fields(parsed_cv)` function
- [ ] `InterviewRepository` class added to `recruitment/infrastructure/repositories.py` with:
  - `create(interview)` — persist new Interview
  - `get_by_id(id)` — get single Interview by UUID
  - `get_by_id_for_update(id)` — for optimistic locking
  - `update(interview)` — persist changes
  - `find_by_candidate_id(candidate_id)` — list interviews for a candidate
  - `get_participants(interview_id)` — get InterviewParticipant list
  - `add_participant(participant)` — persist participant
  - `delete(id)` — remove interview
- [ ] CandidateService imports and uses `candidate_validators` + `InterviewRepository` internally
- [ ] All existing tests in `test_candidate_service.py` pass
- [ ] All existing integration tests pass
