"""Evaluation framework for the Job Application / email classifier.

Provides a reproducible, versioned, redacted evaluation baseline.
The evaluator consumes an injectable predictor or frozen predictions
so reproducibility never depends on a live AI provider.
"""

from src.modules.gmail.evaluation._contract import (
    Cohort,
    EvaluationContract,
    EvaluationContractError,
    EvaluationDataset,
    EvaluationItem,
    EvaluationReport,
    MetricRow,
    Prediction,
    Predictor,
    VersionInfo,
)

__all__ = [
    "Cohort",
    "EvaluationContract",
    "EvaluationContractError",
    "EvaluationDataset",
    "EvaluationItem",
    "EvaluationReport",
    "MetricRow",
    "Prediction",
    "Predictor",
    "VersionInfo",
]
