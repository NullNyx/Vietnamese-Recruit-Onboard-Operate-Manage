"""Evaluation feedback service for safe classification evaluation.

Records HR corrections with minimal metadata (no raw content), manages
opt-in for evaluation samples, and handles redaction before committing
to versioned evaluation sets.

Key design decisions:
- Corrections never trigger online learning or automatic prompt/model changes.
- Raw body, thread content, attachment content, and chain-of-thought are
  never stored durably by default.
- Only redacted data is written to versioned evaluation sets.
- HR opts in individual samples; bulk opt-in is not supported.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.recruitment.domain.entities import (
    CorrectionRecord,
    EvaluationSample,
    EvaluationSet,
)
from src.modules.recruitment.domain.enums import CorrectionEvaluationStatus
from src.modules.recruitment.infrastructure.repositories import (
    CorrectionRecordRepository,
    EvaluationSampleRepository,
    EvaluationSetRepository,
    RecruitmentInboxItemRepository,
)

logger = logging.getLogger(__name__)


class CorrectionRecordNotFoundError(Exception):
    """Raised when a correction record is not found."""


class EvaluationSetNotFoundError(Exception):
    """Raised when an evaluation set is not found."""


class EvaluationSampleNotFoundError(Exception):
    """Raised when an evaluation sample is not found."""


class CorrectionEvaluationService:
    """Manages safe classification evaluation feedback.

    Owns the lifecycle of correction records and evaluation samples,
    enforcing privacy-preserving defaults at every step.

    Args:
        session: The async database session.
        correction_repo: Repository for CorrectionRecord persistence.
        evaluation_set_repo: Repository for EvaluationSet persistence.
        evaluation_sample_repo: Repository for EvaluationSample persistence.
        inbox_repo: Repository for RecruitmentInboxItem (for reading inbox context).
    """

    def __init__(
        self,
        session: AsyncSession,
        correction_repo: CorrectionRecordRepository,
        evaluation_set_repo: EvaluationSetRepository,
        evaluation_sample_repo: EvaluationSampleRepository,
        inbox_repo: RecruitmentInboxItemRepository | None = None,
    ) -> None:
        self._session = session
        self._corrections = correction_repo
        self._eval_sets = evaluation_set_repo
        self._eval_samples = evaluation_sample_repo
        self._inbox_repo = inbox_repo

    # ------------------------------------------------------------------
    # Recording corrections
    # ------------------------------------------------------------------

    async def record_correction(
        self,
        source_type: str,
        source_id: UUID,
        prediction_intent: str | None,
        corrected_intent: str,
        corrected_by_user_id: UUID,
        confidence_raw: float | None = None,
        confidence_calibrated: float | None = None,
        previous_inbox_status: str | None = None,
        model_version: str | None = None,
        prompt_version: str | None = None,
        policy_version: str | None = None,
        evidence: list[dict[str, Any]] | None = None,
        source_hints: list[dict[str, Any]] | None = None,
        redacted_subject: str | None = None,
        redacted_snippet: str | None = None,
    ) -> CorrectionRecord:
        """Record an HR correction with safe, minimal metadata.

        This is the ONLY way a correction should be stored. Raw email body,
        thread content, attachment content, and chain-of-thought are NEVER
        passed to this method.

        Args:
            source_type: "inbox_item" or "job_application".
            source_id: UUID of the source entity.
            prediction_intent: The system's predicted intent.
            corrected_intent: The HR-corrected intent.
            corrected_by_user_id: UUID of the HR user.
            confidence_raw: Raw confidence score from the provider.
            confidence_calibrated: Calibrated confidence score.
            previous_inbox_status: Inbox status before correction.
            model_version: Classifier model version identifier.
            prompt_version: Prompt version identifier.
            policy_version: Policy version identifier.
            evidence: Safe evidence list (never raw content).
            source_hints: Safe source hints (never raw content).
            redacted_subject: Already-redacted subject line.
            redacted_snippet: Already-redacted email snippet.

        Returns:
            The created CorrectionRecord.
        """
        record = CorrectionRecord(
            source_type=source_type,
            source_id=source_id,
            prediction_intent=prediction_intent,
            corrected_intent=corrected_intent,
            corrected_by_user_id=corrected_by_user_id,
            confidence_raw=confidence_raw,
            confidence_calibrated=confidence_calibrated,
            previous_inbox_status=previous_inbox_status,
            model_version=model_version,
            prompt_version=prompt_version,
            policy_version=policy_version,
            evidence=evidence,
            source_hints=source_hints,
            evaluation_status=CorrectionEvaluationStatus.NONE,
            triggers_online_learning=False,
            redacted_subject=redacted_subject,
            redacted_snippet=redacted_snippet,
        )
        created = await self._corrections.create(record)
        logger.info(
            "Recorded correction id=%s source_type=%s source_id=%s "
            "prediction=%s corrected=%s user=%s",
            created.id,
            source_type,
            source_id,
            prediction_intent,
            corrected_intent,
            corrected_by_user_id,
        )
        return created

    # ------------------------------------------------------------------
    # Evaluation opt-in
    # ------------------------------------------------------------------

    async def select_for_evaluation(
        self,
        correction_record_id: UUID,
        redacted_subject: str = "",
        redacted_snippet: str = "",
    ) -> CorrectionRecord:
        """Opt a correction record into evaluation.

        This marks the record as "selected" so it can be redacted and
        committed to an evaluation set. The caller SHOULD provide
        redacted_subject and redacted_snippet before calling this method.

        Args:
            correction_record_id: UUID of the correction record.
            redacted_subject: Redacted subject line.
            redacted_snippet: Redacted email snippet.

        Returns:
            The updated CorrectionRecord.

        Raises:
            CorrectionRecordNotFoundError: If the record does not exist.
        """
        record = await self._corrections.get_by_id(correction_record_id)
        if record is None:
            raise CorrectionRecordNotFoundError(
                f"Correction record {correction_record_id} not found"
            )

        record.evaluation_status = CorrectionEvaluationStatus.SELECTED
        if redacted_subject:
            record.redacted_subject = redacted_subject
        if redacted_snippet:
            record.redacted_snippet = redacted_snippet
        updated = await self._corrections.update(record)
        await self._session.commit()
        logger.info(
            "Selected correction id=%s for evaluation",
            correction_record_id,
        )
        return updated

    async def commit_to_evaluation_set(
        self,
        correction_record_id: UUID,
        evaluation_set_id: UUID,
    ) -> EvaluationSample:
        """Commit a redacted sample to a versioned evaluation set.

        The correction record must have evaluation_status = "selected"
        or "redacted". This method transitions it to "committed".

        Args:
            correction_record_id: UUID of the correction record.
            evaluation_set_id: UUID of the evaluation set.

        Returns:
            The created EvaluationSample.

        Raises:
            CorrectionRecordNotFoundError: If the record does not exist.
            EvaluationSetNotFoundError: If the evaluation set does not exist.
            ValueError: If the record is not in a selectable state.
        """
        record = await self._corrections.get_by_id(correction_record_id)
        if record is None:
            raise CorrectionRecordNotFoundError(
                f"Correction record {correction_record_id} not found"
            )
        if record.evaluation_status not in (
            CorrectionEvaluationStatus.SELECTED,
            CorrectionEvaluationStatus.REDACTED,
        ):
            raise ValueError(
                f"Correction record {correction_record_id} has status "
                f"{record.evaluation_status!r}; expected 'selected' or 'redacted'"
            )

        evaluation_set = await self._eval_sets.get_by_id(evaluation_set_id)
        if evaluation_set is None:
            raise EvaluationSetNotFoundError(f"Evaluation set {evaluation_set_id} not found")

        now = datetime.now(UTC)

        # Build cohorts from evidence and source hints
        cohorts: list[str] = []
        if record.evidence:
            for ev in record.evidence:
                signal = ev.get("signal", "")
                if "cv" not in signal.lower() and "attachment" not in signal.lower():
                    pass  # no-CV signal detection
            # Check if there's evidence of no CV
            signals = [ev.get("signal", "").lower() for ev in record.evidence]
            has_no_cv = bool(signals) and all(
                "cv" not in signal and "attachment" not in signal
                for signal in signals
            )
            if has_no_cv:
                cohorts.append("no-cv")

        # Derive sender name and email from context if available
        sender_name = ""
        sender_email = ""
        if record.source_type == "inbox_item" and self._inbox_repo:
            inbox_item = await self._inbox_repo.get_by_id(record.source_id)
            if inbox_item is not None:
                sender_name = inbox_item.sender_name
                sender_email = inbox_item.sender_email

        sample = EvaluationSample(
            correction_record_id=record.id,
            evaluation_set_id=evaluation_set.id,
            redacted_subject=record.redacted_subject or "",
            redacted_snippet=record.redacted_snippet or "",
            redacted_sender_name=sender_name,
            redacted_sender_email=sender_email,
            ground_truth_intent=record.corrected_intent,
            model_version=record.model_version,
            prompt_version=record.prompt_version,
            policy_version=record.policy_version,
            cohorts=cohorts,
            redacted_at=now,
        )
        created = await self._eval_samples.create(sample)

        record.evaluation_status = CorrectionEvaluationStatus.COMMITTED
        await self._corrections.update(record)
        await self._session.commit()

        logger.info(
            "Committed evaluation sample id=%s to set id=%s (version=%s)",
            created.id,
            evaluation_set_id,
            evaluation_set.version,
        )
        return created

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def get_correction_record(self, record_id: UUID) -> CorrectionRecord:
        """Get a single correction record by ID.

        Args:
            record_id: UUID of the correction record.

        Returns:
            The CorrectionRecord entity.

        Raises:
            CorrectionRecordNotFoundError: If not found.
        """
        record = await self._corrections.get_by_id(record_id)
        if record is None:
            raise CorrectionRecordNotFoundError(f"Correction record {record_id} not found")
        return record

    async def list_corrections_for_source(self, source_id: UUID) -> list[CorrectionRecord]:
        """List correction records for a source entity.

        Args:
            source_id: UUID of the inbox item or job application.

        Returns:
            List of CorrectionRecord entities.
        """
        return await self._corrections.get_by_source_id(source_id)

    async def list_corrections_by_evaluation_status(self, status: str) -> list[CorrectionRecord]:
        """List correction records filtered by evaluation status.

        Args:
            status: The evaluation status to filter by.

        Returns:
            List of CorrectionRecord entities.
        """
        return await self._corrections.get_by_evaluation_status(status)

    async def create_evaluation_set(
        self,
        version: str,
        description: str = "",
    ) -> EvaluationSet:
        """Create a new versioned evaluation set.

        Args:
            version: Semantic version string (e.g. "1.0.0").
            description: Human-readable description.

        Returns:
            The created EvaluationSet.
        """
        evaluation_set = EvaluationSet(
            version=version,
            description=description,
        )
        created = await self._eval_sets.create(evaluation_set)
        await self._session.commit()
        logger.info("Created evaluation set id=%s version=%s", created.id, version)
        return created

    async def list_evaluation_sets(self) -> list[EvaluationSet]:
        """List all evaluation sets, newest first.

        Returns:
            List of EvaluationSet entities.
        """
        return await self._eval_sets.list_all()

    async def list_samples_for_set(self, evaluation_set_id: UUID) -> list[EvaluationSample]:
        """List all samples in an evaluation set.

        Args:
            evaluation_set_id: UUID of the evaluation set.

        Returns:
            List of EvaluationSample entities.
        """
        return await self._eval_samples.list_by_evaluation_set_id(evaluation_set_id)
