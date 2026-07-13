"""Aggregation contract for Job Application rollout telemetry."""

from dataclasses import dataclass

_JOB_APPLICATION_INTENTS = {"recruitment", "job_application"}


@dataclass(frozen=True)
class TelemetrySample:
    stable_intent: str | None
    candidate_intent: str | None
    corrected_intent: str | None
    inbox_status: str | None
    has_cv: bool
    latency_ms: int
    provider_error: bool
    retry_count: int = 0
    retry_failure: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def selected_intent(self) -> str | None:
        # Stable intent is absent when a canary/full candidate was selected.
        return self.stable_intent or self.candidate_intent


@dataclass(frozen=True)
class OperationalTelemetry:
    sample_size: int
    job_application_recall_proxy: float
    stable_recall_proxy: float
    no_cv_recall_proxy: float | None
    correction_rate: float
    review_rate: float
    needs_classification_rate: float
    p95_latency_ms: int
    provider_error_rate: float
    duplicate_count: int
    retry_failure_rate: float
    total_prompt_tokens: int
    total_completion_tokens: int
    estimated_cost_usd: float


def summarize_telemetry(
    samples: list[TelemetrySample], *, duplicate_count: int
) -> OperationalTelemetry:
    """Compute operational metrics from the latest event for each email."""
    total = len(samples)
    if total == 0:
        return OperationalTelemetry(
            0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0,
            0.0,
            duplicate_count,
            0.0,
            0,
            0,
            0.0,
        )

    labelled = [sample for sample in samples if sample.corrected_intent == "job_application"]
    selected_hits = sum(sample.selected_intent in _JOB_APPLICATION_INTENTS for sample in labelled)
    stable_hits = sum(sample.stable_intent in _JOB_APPLICATION_INTENTS for sample in labelled)
    recall_proxy = selected_hits / len(labelled) if labelled else 0.0
    stable_recall = stable_hits / len(labelled) if labelled else 0.0

    no_cv_labelled = [sample for sample in labelled if not sample.has_cv]
    no_cv_hits = sum(
        sample.selected_intent in _JOB_APPLICATION_INTENTS for sample in no_cv_labelled
    )
    no_cv_recall = no_cv_hits / len(no_cv_labelled) if no_cv_labelled else None

    latencies = sorted(sample.latency_ms for sample in samples)
    p95_index = max(0, (95 * len(latencies) + 99) // 100 - 1)
    return OperationalTelemetry(
        sample_size=total,
        job_application_recall_proxy=recall_proxy,
        stable_recall_proxy=stable_recall,
        no_cv_recall_proxy=no_cv_recall,
        correction_rate=sum(sample.corrected_intent is not None for sample in samples) / total,
        review_rate=sum(sample.inbox_status is not None for sample in samples) / total,
        needs_classification_rate=(
            sum(sample.inbox_status == "needs_classification" for sample in samples) / total
        ),
        p95_latency_ms=latencies[p95_index],
        provider_error_rate=sum(sample.provider_error for sample in samples) / total,
        duplicate_count=duplicate_count,
        retry_failure_rate=sum(sample.retry_failure for sample in samples) / total,
        total_prompt_tokens=sum(sample.prompt_tokens for sample in samples),
        total_completion_tokens=sum(sample.completion_tokens for sample in samples),
        estimated_cost_usd=sum(sample.estimated_cost_usd for sample in samples),
    )
