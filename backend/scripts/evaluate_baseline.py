#!/usr/bin/env python
"""Evaluate the current Job Application / email classifier against a versioned,
redacted evaluation dataset.

Usage:
    uv run python scripts/evaluate_baseline.py \\
        --dataset data/evaluation/v1.0.0/dataset.json \\
        [--frozen-predictions data/evaluation/v1.0.0/frozen_predictions.json] \\
        [--predictor rules] \\
        [--output report.json]

If ``--frozen-predictions`` is provided, no live classifier runs.
Otherwise ``--predictor`` selects the classifier backend (default: ``rules``).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from src.modules.gmail.evaluation import (
    EvaluationContract,
    EvaluationContractError,
    EvaluationItem,
    Prediction,
    Predictor,
    VersionInfo,
)

logger = logging.getLogger(__name__)


def _make_rules_predictor() -> Predictor:
    """Build a predictor that wraps the current ``RulesClassifier``."""
    from src.modules.gmail.application.rules_classifier import RulesClassifier

    classifier = RulesClassifier()

    def predict(item: EvaluationItem) -> Prediction:
        result = classifier.classify(
            subject=item.subject,
            sender_email=item.sender_email,
            snippet=item.snippet,
            has_attachments=item.has_attachments,
        )
        return Prediction(
            item_id=item.id,
            category=result.category,
            confidence=result.confidence,
            source=result.source,
        )

    return predict


def _load_frozen_predictions(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load frozen predictions from a JSON file.

    Returns a dict of item_id → raw prediction dict.

    Raises:
        EvaluationContractError: If the file is missing, malformed, or
            the data is not a dict.
    """
    p = Path(path)
    if not p.exists():
        raise EvaluationContractError(f"Frozen predictions file not found: {p}")
    try:
        with open(p, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise EvaluationContractError(f"Failed to parse frozen predictions file {p}: {exc}")
    if not isinstance(raw, dict):
        raise EvaluationContractError(
            f"Frozen predictions file must contain a JSON object (dict), got {type(raw).__name__}"
        )
    return raw


def _convert_frozen(
    fp_raw: dict[str, Any],
    item_ids: set[str],
) -> dict[str, Prediction]:
    """Convert a raw frozen predictions dict into Prediction objects.

    Raises:
        EvaluationContractError: For any validation failure (unknown item,
            invalid category, confidence out of range).
    """
    from src.modules.gmail.domain.enums import EmailCategory

    frozen: dict[str, Prediction] = {}
    for item_id, pred_data_raw in fp_raw.items():
        if item_id == "_metadata":
            continue
        if not isinstance(pred_data_raw, dict):
            raise EvaluationContractError(
                f"Frozen prediction for {item_id!r}: expected a JSON object, "
                f"got {type(pred_data_raw).__name__}"
            )
        pred_data: dict[str, Any] = pred_data_raw
        cat_raw = pred_data.get("category", "")
        try:
            category = EmailCategory(str(cat_raw))
        except ValueError:
            raise EvaluationContractError(
                f"Frozen prediction for {item_id!r}: invalid category "
                f"{cat_raw!r}; valid values: {[e.value for e in EmailCategory]}"
            )
        confidence = float(pred_data.get("confidence", 0.0))
        if not (0.0 <= confidence <= 1.0):
            raise EvaluationContractError(
                f"Frozen prediction for {item_id!r}: confidence {confidence} is outside [0.0, 1.0]"
            )
        frozen[item_id] = Prediction(
            item_id=item_id,
            category=category,
            confidence=confidence,
            source=str(pred_data.get("source", "frozen")),
        )
    return frozen


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the Job Application / email classifier baseline"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to the evaluation dataset JSON file",
    )
    parser.add_argument(
        "--frozen-predictions",
        default=None,
        help="Path to frozen predictions JSON (disables live predictor)",
    )
    parser.add_argument(
        "--predictor",
        default="rules",
        choices=["rules", "none"],
        help="Classifier backend to use (default: rules; ignored if --frozen-predictions set)",
    )
    parser.add_argument(
        "--needs-review-threshold",
        type=float,
        default=0.5,
        help="Confidence below this threshold flags needs_review (default: 0.5)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write the evaluation report as JSON",
    )
    args = parser.parse_args()

    # ── Load contract ──────────────────────────────────────────────
    try:
        contract = EvaluationContract.from_json(args.dataset)
    except EvaluationContractError as exc:
        print(f"FATAL: Invalid evaluation contract: {exc}", file=sys.stderr)
        sys.exit(1)

    item_ids = {item.id for item in contract.dataset.items}

    print(f"Loaded evaluation dataset v{contract.versions.dataset}")
    print(f"  Items: {len(contract.dataset.items)}")
    print(f"  Cohorts: {list(contract.dataset.cohorts.keys())}")
    print(f"  Model: {contract.versions.model or '(not recorded)'}")
    print(f"  Prompt: {contract.versions.prompt or '(not recorded)'}")
    print(f"  Policy: {contract.versions.policy or '(not recorded)'}")

    # ── Load frozen predictions OR create predictor ────────────────
    frozen_predictions: dict[str, Prediction] | None = None
    predictor: Predictor | None = None
    source_versions: VersionInfo | None = None

    if args.frozen_predictions:
        try:
            fp_raw = _load_frozen_predictions(args.frozen_predictions)
            frozen_predictions = _convert_frozen(fp_raw, item_ids)
            # Extract predictor version metadata from frozen file
            fp_meta = fp_raw.get("_metadata", {})
            predictor_meta = fp_meta.get("predictor", {}) if isinstance(fp_meta, dict) else {}
            if predictor_meta:
                source_versions = VersionInfo(
                    model=str(predictor_meta.get("model", "")),
                    prompt=str(predictor_meta.get("prompt", "")),
                    policy=str(predictor_meta.get("policy", "")),
                )
        except EvaluationContractError as exc:
            print(f"FATAL: Invalid frozen predictions: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"  Using frozen predictions: {len(frozen_predictions)} items")
        if source_versions:
            print(f"  Predictor: {source_versions.model}")
            print(f"  Policy:    {source_versions.policy}")
    elif args.predictor == "rules":
        predictor = _make_rules_predictor()
        print("  Using RulesClassifier as predictor")
    else:
        predictor = None
        print("  WARNING: No predictor and no frozen predictions — evaluation will fail")

    # ── Run evaluation ─────────────────────────────────────────────
    # Pass CLI-frozen predictions as an override to contract.run.
    # This is the fix for defect 1: previously frozen_predictions was
    # parsed but never forwarded to the runner.
    try:
        report = contract.run(
            predictor=predictor,
            needs_review_threshold=args.needs_review_threshold,
            frozen_predictions=frozen_predictions,
            source_versions=source_versions,
        )
    except EvaluationContractError as exc:
        print(f"FATAL: Evaluation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Print results ──────────────────────────────────────────────
    print()
    print("=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)
    print()

    # Print version info
    print("VERSIONS")
    print(f"  Dataset: {report.versions.dataset}")
    print(f"  Model:   {report.versions.model or '(not recorded)'}")
    print(f"  Prompt:  {report.versions.prompt or '(not recorded)'}")
    print(f"  Policy:  {report.versions.policy or '(not recorded)'}")
    print()

    # Print overall
    o = report.overall
    print(f"OVERALL (support={o.support})")
    print(f"  Recall:    {o.recall:.4f}  ({o.tp}/{o.tp + o.fn})")
    print(f"  Precision: {o.precision:.4f}  ({o.tp}/{o.tp + o.fp})")
    print(f"  Review:    {o.review_rate:.4f}  ({o.tp + o.fn} items)")
    print()

    # Print per-category
    if report.per_category:
        print("BY CATEGORY")
        for cat_name, row in sorted(report.per_category.items()):
            print(
                f"  {cat_name:25s}  "
                f"recall={row.recall:.4f}  "
                f"precision={row.precision:.4f}  "
                f"review={row.review_rate:.4f}  "
                f"support={row.support}"
            )
        print()

    # Print per-cohort
    if report.per_cohort:
        print("BY COHORT")
        for cohort_name, row in sorted(report.per_cohort.items()):
            print(
                f"  {cohort_name:30s}  "
                f"recall={row.recall:.4f}  "
                f"precision={row.precision:.4f}  "
                f"review={row.review_rate:.4f}  "
                f"support={row.support}"
            )
        print()

    # ── Save report ────────────────────────────────────────────────
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
