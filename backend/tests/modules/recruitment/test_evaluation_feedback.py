"""Privacy contract and journey tests for safe evaluation feedback (GH #187).

Tests verify:
1. Correction records store only safe metadata — no raw body, thread, or COT
2. HR can opt-in individual samples for evaluation set with redaction
3. Only redacted data is written to versioned evaluation sets
4. Corrections never trigger online learning
5. API journey through the full select → redact → commit flow
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.recruitment.application.evaluation_service import (
    CorrectionEvaluationService,
    CorrectionRecordNotFoundError,
    EvaluationSetNotFoundError,
)
from src.modules.recruitment.domain.entities import (
    CorrectionRecord,
    EvaluationSample,
    EvaluationSet,
)
from src.modules.recruitment.domain.enums import (
    CorrectionEvaluationStatus,
)
from src.modules.recruitment.infrastructure.repositories import (
    CorrectionRecordRepository,
    EvaluationSampleRepository,
    EvaluationSetRepository,
    RecruitmentInboxItemRepository,
)

# =========================================================================
# Helpers
# =========================================================================


def _make_mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _make_correction_repo() -> MagicMock:
    repo = MagicMock(spec=CorrectionRecordRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_source_id = AsyncMock(return_value=[])
    repo.get_by_evaluation_status = AsyncMock(return_value=[])
    repo.update = AsyncMock()
    return repo


def _make_eval_set_repo() -> MagicMock:
    repo = MagicMock(spec=EvaluationSetRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_version = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])
    return repo


def _make_eval_sample_repo() -> MagicMock:
    repo = MagicMock(spec=EvaluationSampleRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list_by_evaluation_set_id = AsyncMock(return_value=[])
    repo.list_by_correction_record_id = AsyncMock(return_value=[])
    return repo


def _make_inbox_repo() -> MagicMock:
    repo = MagicMock(spec=RecruitmentInboxItemRepository)
    repo.get_by_id = AsyncMock()
    repo.get_by_gmail_message_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    return repo


# =========================================================================
# Privacy Contract Tests (GH #187 AC)
# =========================================================================


class TestDefaultRetentionPrivacy:
    """Correction records must NOT store raw body, thread, or COT by default.

    These tests verify the privacy contract: only prediction, correction,
    versions, minimal metadata, and timestamps are stored.
    """

    def test_error_if_raw_body_passed_to_record_correction(self) -> None:
        """Raw email body must never be stored in correction records.

        The CorrectionRecord entity has NO field for raw body, so this
        test verifies the contract is structurally enforced.
        """
        field_names = set(CorrectionRecord.model_fields.keys())
        assert "raw_body" not in field_names, "Raw body field must not exist on CorrectionRecord"
        assert "body" not in field_names, "Body field must not exist on CorrectionRecord"
        assert "thread_content" not in field_names, "Thread content must not exist"
        assert "chain_of_thought" not in field_names, "COT must not exist on CorrectionRecord"

    def test_error_if_attachments_content_passed(self) -> None:
        """Attachment content must never be storable in correction records."""
        field_names = set(CorrectionRecord.model_fields.keys())
        assert "attachment_content" not in field_names
        assert "attachments" not in field_names

    async def test_correction_stores_only_safe_metadata(self) -> None:
        """A correction record stores only prediction, correction, versions,
        minimal metadata, and timestamps — not raw content."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        eval_set_repo = _make_eval_set_repo()
        eval_sample_repo = _make_eval_sample_repo()

        returned_record = CorrectionRecord(
            id=uuid4(),
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            model_version="gemma-4-1.0",
            prompt_version="v2.1",
            policy_version="v1.0",
            evaluation_status=CorrectionEvaluationStatus.NONE,
            triggers_online_learning=False,
        )
        correction_repo.create.return_value = returned_record

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=eval_set_repo,
            evaluation_sample_repo=eval_sample_repo,
        )

        # Act: record a correction with only safe metadata
        result = await service.record_correction(
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            confidence_raw=0.75,
            confidence_calibrated=0.65,
            model_version="gemma-4-1.0",
            prompt_version="v2.1",
            policy_version="v1.0",
            evidence=[{"signal": "subject:ung tuyen"}],
        )

        # Assert: safe metadata is preserved
        assert result.prediction_intent == "job_application"
        assert result.corrected_intent == "other"
        assert result.model_version == "gemma-4-1.0"
        assert result.prompt_version == "v2.1"
        assert result.policy_version == "v1.0"
        assert result.triggers_online_learning is False
        assert result.evaluation_status == CorrectionEvaluationStatus.NONE

    async def test_correction_never_triggers_online_learning(self) -> None:
        """The triggers_online_learning field is always False by design."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        returned_record = CorrectionRecord(
            id=uuid4(),
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            triggers_online_learning=False,
        )
        correction_repo.create.return_value = returned_record

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=_make_eval_set_repo(),
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        result = await service.record_correction(
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
        )
        assert result.triggers_online_learning is False


class TestEvaluationSamplePrivacy:
    """Evaluation samples must be redacted before storage."""

    def test_error_if_pii_in_evaluation_sample(self) -> None:
        """EvaluationSample has no raw fields — only redacted ones."""
        field_names = set(EvaluationSample.model_fields.keys())
        assert "redacted_subject" in field_names
        assert "redacted_snippet" in field_names
        assert "redacted_sender_name" in field_names
        assert "redacted_sender_email" in field_names
        # Raw fields must NOT exist
        assert "raw_subject" not in field_names
        assert "raw_body" not in field_names
        assert "raw_email" not in field_names

    async def test_evaluation_sample_has_version_info(self) -> None:
        """Evaluation samples preserve version info for reproducibility."""
        sample = EvaluationSample(
            id=uuid4(),
            correction_record_id=uuid4(),
            evaluation_set_id=uuid4(),
            redacted_subject="[Redacted] Application",
            redacted_snippet="[Redacted]",
            redacted_sender_name="[Redacted]",
            redacted_sender_email="[Redacted]",
            ground_truth_intent="other",
            model_version="gemma-4-1.0",
            prompt_version="v2.1",
            policy_version="v1.0",
            cohorts=["no-cv"],
        )
        assert sample.model_version == "gemma-4-1.0"
        assert sample.prompt_version == "v2.1"
        assert sample.policy_version == "v1.0"
        assert sample.cohorts == ["no-cv"]

    async def test_evaluation_set_versioned(self) -> None:
        """Evaluation sets have unique semantic versions."""
        es1 = EvaluationSet(version="1.0.0", description="Initial set")
        es2 = EvaluationSet(version="1.1.0", description="Added samples")
        assert es1.version != es2.version
        assert es1.version == "1.0.0"
        assert es2.version == "1.1.0"


# =========================================================================
# Service Layer Tests
# =========================================================================


class TestRecordCorrection:
    """Recording corrections through CorrectionEvaluationService."""

    async def test_record_correction_creates_correction_record(self) -> None:
        """record_correction creates a CorrectionRecord and returns it."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        expected_id = uuid4()
        created_record = CorrectionRecord(
            id=expected_id,
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            triggers_online_learning=False,
        )
        correction_repo.create.return_value = created_record

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=_make_eval_set_repo(),
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        result = await service.record_correction(
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
        )

        assert result.id == expected_id
        correction_repo.create.assert_awaited_once()


class TestSelectForEvaluation:
    """Opt-in flow for evaluation sets."""

    async def test_select_correction_for_evaluation(self) -> None:
        """Selecting a correction for evaluation updates its status."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        record_id = uuid4()
        record = CorrectionRecord(
            id=record_id,
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            evaluation_status=CorrectionEvaluationStatus.NONE,
            triggers_online_learning=False,
        )
        correction_repo.get_by_id.return_value = record
        correction_repo.update.return_value = record

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=_make_eval_set_repo(),
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        updated = await service.select_for_evaluation(
            correction_record_id=record_id,
            redacted_subject="Ung tuyen vi tri [REDACTED]",
            redacted_snippet="Toi muon ung tuyen [REDACTED]",
        )

        assert updated.evaluation_status == CorrectionEvaluationStatus.SELECTED
        assert updated.redacted_subject == "Ung tuyen vi tri [REDACTED]"
        assert updated.redacted_snippet == "Toi muon ung tuyen [REDACTED]"
        correction_repo.update.assert_awaited()

    async def test_select_nonexistent_correction_raises(self) -> None:
        """Selecting a non-existent correction raises CorrectionRecordNotFoundError."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        correction_repo.get_by_id.return_value = None

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=_make_eval_set_repo(),
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        with pytest.raises(CorrectionRecordNotFoundError):
            await service.select_for_evaluation(correction_record_id=uuid4())


class TestCommitToEvaluationSet:
    """Committing redacted samples to evaluation sets."""

    async def test_commit_selected_to_evaluation_set(self) -> None:
        """Committing a selected correction creates an EvaluationSample."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        eval_set_repo = _make_eval_set_repo()
        eval_sample_repo = _make_eval_sample_repo()

        record_id = uuid4()
        record = CorrectionRecord(
            id=record_id,
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            evaluation_status=CorrectionEvaluationStatus.SELECTED,
            triggers_online_learning=False,
            redacted_subject="Ung tuyen [REDACTED]",
            redacted_snippet="Toi muon [REDACTED]",
            model_version="gemma-4-1.0",
            prompt_version="v2.1",
            policy_version="v1.0",
        )
        correction_repo.get_by_id.return_value = record
        correction_repo.update.return_value = record

        set_id = uuid4()
        eval_set = EvaluationSet(id=set_id, version="1.0.0")
        eval_set_repo.get_by_id.return_value = eval_set

        sample_id = uuid4()
        sample = EvaluationSample(
            id=sample_id,
            correction_record_id=record_id,
            evaluation_set_id=set_id,
            redacted_subject="Ung tuyen [REDACTED]",
            redacted_snippet="Toi muon [REDACTED]",
            redacted_sender_name="",
            redacted_sender_email="",
            ground_truth_intent="other",
        )
        eval_sample_repo.create.return_value = sample

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=eval_set_repo,
            evaluation_sample_repo=eval_sample_repo,
        )

        result = await service.commit_to_evaluation_set(
            correction_record_id=record_id,
            evaluation_set_id=set_id,
        )

        assert result.id == sample_id
        assert result.ground_truth_intent == "other"
        assert result.redacted_subject == "Ung tuyen [REDACTED]"
        # Verify record status updated
        assert record.evaluation_status == CorrectionEvaluationStatus.COMMITTED
        eval_sample_repo.create.assert_awaited_once()

    async def test_commit_not_selected_raises(self) -> None:
        """Committing a correction that isn't selected or redacted raises ValueError."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        record = CorrectionRecord(
            id=uuid4(),
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            evaluation_status=CorrectionEvaluationStatus.NONE,
            triggers_online_learning=False,
        )
        correction_repo.get_by_id.return_value = record

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=_make_eval_set_repo(),
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        with pytest.raises(ValueError, match="expected 'selected' or 'redacted'"):
            await service.commit_to_evaluation_set(
                correction_record_id=uuid4(),
                evaluation_set_id=uuid4(),
            )

    async def test_commit_missing_eval_set_raises(self) -> None:
        """Committing to a non-existent evaluation set raises EvaluationSetNotFoundError."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        eval_set_repo = _make_eval_set_repo()

        record = CorrectionRecord(
            id=uuid4(),
            source_type="inbox_item",
            source_id=uuid4(),
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            evaluation_status=CorrectionEvaluationStatus.SELECTED,
            triggers_online_learning=False,
        )
        correction_repo.get_by_id.return_value = record
        eval_set_repo.get_by_id.return_value = None

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=eval_set_repo,
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        with pytest.raises(EvaluationSetNotFoundError):
            await service.commit_to_evaluation_set(
                correction_record_id=uuid4(),
                evaluation_set_id=uuid4(),
            )


class TestCreateEvaluationSet:
    """Creating versioned evaluation sets."""

    async def test_create_evaluation_set(self) -> None:
        """Creating an evaluation set persists the version and description."""
        session = _make_mock_session()
        eval_set_repo = _make_eval_set_repo()
        set_id = uuid4()
        created_set = EvaluationSet(id=set_id, version="1.0.0", description="Initial")
        eval_set_repo.create.return_value = created_set

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=_make_correction_repo(),
            evaluation_set_repo=eval_set_repo,
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        result = await service.create_evaluation_set(version="1.0.0", description="Initial")
        assert result.id == set_id
        assert result.version == "1.0.0"
        assert result.description == "Initial"


class TestListCorrections:
    """Listing correction records."""

    async def test_list_corrections_for_source(self) -> None:
        """Listing corrections by source returns the correct records."""
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        source_id = uuid4()
        expected_records = [
            CorrectionRecord(
                id=uuid4(),
                source_type="inbox_item",
                source_id=source_id,
                corrected_intent="other",
                corrected_by_user_id=uuid4(),
                triggers_online_learning=False,
            )
        ]
        correction_repo.get_by_source_id.return_value = expected_records

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=_make_eval_set_repo(),
            evaluation_sample_repo=_make_eval_sample_repo(),
        )

        records = await service.list_corrections_for_source(source_id)
        assert len(records) == 1
        correction_repo.get_by_source_id.assert_awaited_once_with(source_id)


# =========================================================================
# Redaction Utility Tests
# =========================================================================


class TestRedaction:
    """The _redact_email_field utility used in inbox_router."""

    def test_redact_email_addresses(self) -> None:
        """Email addresses in subject/snippet are replaced."""
        from src.modules.recruitment.api.inbox_router import _redact_email_field

        result = _redact_email_field("Contact me at nguyen.van.a@example.com")
        assert "[EMAIL]" in result
        assert "nguyen.van.a@example.com" not in result

    def test_redact_phone_numbers(self) -> None:
        """Vietnamese phone numbers are replaced."""
        from src.modules.recruitment.api.inbox_router import _redact_email_field

        result = _redact_email_field("Call me at 0912345678")
        assert "[PHONE]" in result
        assert "0912345678" not in result

    def test_redact_with_plus84(self) -> None:
        """Phone numbers with +84 prefix are also redacted."""
        from src.modules.recruitment.api.inbox_router import _redact_email_field

        result = _redact_email_field("Call +84123456789")
        assert "[PHONE]" in result


# =========================================================================
# End-to-End Journey Test (mocked)
# =========================================================================


class TestEvaluationJourney:
    """Full select → redact → commit journey through the service layer."""

    async def test_full_evaluation_journey(self) -> None:
        """Simulate the complete HR workflow for evaluation feedback.

        1. HR corrects an inbox item → CorrectionRecord created
        2. HR selects the correction for evaluation → status = "selected"
        3. HR commits to a versioned evaluation set → EvaluationSample created
        """
        session = _make_mock_session()
        correction_repo = _make_correction_repo()
        eval_set_repo = _make_eval_set_repo()
        eval_sample_repo = _make_eval_sample_repo()

        # Step 1: Record a correction (simulates HR correcting intent)
        record_id = uuid4()
        source_id = uuid4()
        initial_record = CorrectionRecord(
            id=record_id,
            source_type="inbox_item",
            source_id=source_id,
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            confidence_raw=0.45,
            confidence_calibrated=0.35,
            evaluation_status=CorrectionEvaluationStatus.NONE,
            triggers_online_learning=False,
            evidence=[{"signal": "subject:ung tuyen"}],
        )
        correction_repo.create.return_value = initial_record

        service = CorrectionEvaluationService(
            session=session,
            correction_repo=correction_repo,
            evaluation_set_repo=eval_set_repo,
            evaluation_sample_repo=eval_sample_repo,
        )

        record = await service.record_correction(
            source_type="inbox_item",
            source_id=source_id,
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            confidence_raw=0.45,
            evidence=[{"signal": "subject:ung tuyen"}],
        )
        assert record.evaluation_status == CorrectionEvaluationStatus.NONE
        assert record.triggers_online_learning is False

        # Step 2: Create an evaluation set
        set_id = uuid4()
        evaluation_set = EvaluationSet(id=set_id, version="1.0.0", description="Release v1 cohort")
        eval_set_repo.create.return_value = evaluation_set

        created_set = await service.create_evaluation_set(
            version="1.0.0",
            description="Release v1 cohort",
        )
        assert created_set.version == "1.0.0"

        # Step 3: Select the correction for evaluation (with redacted content)
        selected_record = CorrectionRecord(
            id=record_id,
            source_type="inbox_item",
            source_id=source_id,
            prediction_intent="job_application",
            corrected_intent="other",
            corrected_by_user_id=uuid4(),
            evaluation_status=CorrectionEvaluationStatus.SELECTED,
            triggers_online_learning=False,
            redacted_subject="Ung tuyen [REDACTED]",
            redacted_snippet="Toi muon ung tuyen [REDACTED]",
            evidence=[{"signal": "subject:ung tuyen"}],
        )
        correction_repo.get_by_id.return_value = selected_record
        correction_repo.update.return_value = selected_record

        selected = await service.select_for_evaluation(
            correction_record_id=record_id,
            redacted_subject="Ung tuyen [REDACTED]",
            redacted_snippet="Toi muon ung tuyen [REDACTED]",
        )
        assert selected.evaluation_status == CorrectionEvaluationStatus.SELECTED

        # Step 4: Commit to evaluation set
        eval_set_repo.get_by_id.return_value = evaluation_set
        sample_id = uuid4()
        sample = EvaluationSample(
            id=sample_id,
            correction_record_id=record_id,
            evaluation_set_id=set_id,
            redacted_subject="Ung tuyen [REDACTED]",
            redacted_snippet="Toi muon ung tuyen [REDACTED]",
            redacted_sender_name="",
            redacted_sender_email="",
            ground_truth_intent="other",
        )
        eval_sample_repo.create.return_value = sample

        committed = await service.commit_to_evaluation_set(
            correction_record_id=record_id,
            evaluation_set_id=set_id,
        )
        assert committed.ground_truth_intent == "other"
        assert committed.redacted_subject == "Ung tuyen [REDACTED]"
        assert selected_record.evaluation_status == CorrectionEvaluationStatus.COMMITTED

        # Step 5: Verify no raw content leaked
        assert "raw_body" not in CorrectionRecord.model_fields
        assert "chain_of_thought" not in CorrectionRecord.model_fields
