"""Persistence adapter for content-free classification rollout telemetry."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gmail.application.classification_rollout import RolloutTelemetryEvent
from src.modules.gmail.application.classification_telemetry import (
    OperationalTelemetry,
    TelemetrySample,
    summarize_telemetry,
)
from src.modules.gmail.domain.entities import ClassificationRolloutEventRecord


class ClassificationRolloutRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, event: RolloutTelemetryEvent) -> None:
        """Persist one decision; the caller owns commit/rollback."""
        self._session.add(
            ClassificationRolloutEventRecord(
                gmail_message_id=event.gmail_message_id,
                mode=event.mode.value,
                selected_classifier_version=event.selected_classifier_version,
                stable_intent=event.stable_intent or None,
                candidate_intent=event.candidate_intent,
                policy_version=event.policy_version,
                has_cv=event.has_cv,
                stable_latency_ms=event.stable_latency_ms,
                candidate_latency_ms=event.candidate_latency_ms,
                candidate_provider_error=event.candidate_provider_error,
            )
        )

    async def summarize(self, *, hours: int = 24) -> OperationalTelemetry:
        """Measure latest per-email rollout outcomes for an operational window."""
        result = await self._session.execute(
            text(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (gmail_message_id) *
                    FROM classification_rollout_events
                    WHERE created_at >= now() - make_interval(hours => :hours)
                    ORDER BY gmail_message_id, created_at DESC
                )
                SELECT
                    event.stable_intent,
                    event.candidate_intent,
                    item.corrected_intent,
                    item.inbox_status,
                    event.has_cv,
                    COALESCE(event.candidate_latency_ms, event.stable_latency_ms) AS latency_ms,
                    event.candidate_provider_error
                FROM latest AS event
                LEFT JOIN recruitment_inbox_items AS item USING (gmail_message_id)
                """
            ),
            {"hours": hours},
        )
        samples = [
            TelemetrySample(
                stable_intent=row["stable_intent"],
                candidate_intent=row["candidate_intent"],
                corrected_intent=row["corrected_intent"],
                inbox_status=row["inbox_status"],
                has_cv=row["has_cv"],
                latency_ms=row["latency_ms"],
                provider_error=row["candidate_provider_error"],
            )
            for row in result.mappings().all()
        ]
        duplicate_result = await self._session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT gmail_message_id
                    FROM job_applications
                    GROUP BY gmail_message_id
                    HAVING COUNT(*) > 1
                ) AS duplicates
                """
            )
        )
        duplicate_count = int(duplicate_result.scalar_one())
        return summarize_telemetry(samples, duplicate_count=duplicate_count)
