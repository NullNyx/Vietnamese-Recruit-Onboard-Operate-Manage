"""Measured rollout telemetry uses latest durable workflow outcomes."""

import pytest

from src.modules.gmail.application.classification_telemetry import (
    TelemetrySample,
    summarize_telemetry,
)


def test_summarizes_release_metrics_and_no_cv_cohort() -> None:
    samples = [
        TelemetrySample(
            stable_intent="recruitment",
            candidate_intent="recruitment",
            corrected_intent="job_application",
            inbox_status="needs_classification",
            has_cv=False,
            latency_ms=100,
            provider_error=False,
        ),
        TelemetrySample(
            stable_intent=None,
            candidate_intent="vendor",
            corrected_intent="job_application",
            inbox_status="needs_classification",
            has_cv=True,
            latency_ms=500,
            provider_error=True,
        ),
    ]

    telemetry = summarize_telemetry(samples, duplicate_count=1)

    assert telemetry.sample_size == 2
    assert telemetry.job_application_recall_proxy == pytest.approx(0.5)
    assert telemetry.stable_recall_proxy == pytest.approx(0.5)
    assert telemetry.no_cv_recall_proxy == pytest.approx(1.0)
    assert telemetry.correction_rate == pytest.approx(1.0)
    assert telemetry.review_rate == pytest.approx(1.0)
    assert telemetry.needs_classification_rate == pytest.approx(1.0)
    assert telemetry.p95_latency_ms == 500
    assert telemetry.provider_error_rate == pytest.approx(0.5)
    assert telemetry.duplicate_count == 1
