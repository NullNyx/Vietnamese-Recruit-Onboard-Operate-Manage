"""Evaluation contract, types, and runner for the Job Application classifier baseline.

The evaluator is designed to be reproducible without depending on a live AI
provider. It accepts either:

- An injectable ``Predictor`` callable (a synchronous function that maps
  ``EvaluationItem`` → ``Prediction``).
- Frozen predictions (a ``dict[str, Prediction]`` keyed by item id), which
  can be captured once and replayed in CI.

When both are provided, frozen predictions take precedence per-item and the
predictor fills in any missing items.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.modules.gmail.domain.enums import EmailCategory

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────────────────────────────

#: A callable alias that predicts the category for one evaluation item.
#: The evaluator calls it as ``predictor(item) → Prediction``.
#: This is a ``Callable`` type alias, not a ``Protocol``.
Predictor = Callable[["EvaluationItem"], "Prediction"]


@dataclass(frozen=True)
class Cohort:
    """Metadata for a single evaluation cohort.

    Attributes:
        label: Human-readable cohort name.
        color: Hex colour (for visualisation, not used in computation).
    """

    label: str
    color: str


@dataclass(frozen=True)
class VersionInfo:
    """Version information recorded in the report.

    Attributes:
        dataset: Semantic version of the evaluation dataset.
        model: Model identifier (e.g. ``"gemma-4-1.0"``).
        prompt: Prompt version hash or tag.
        policy: Policy / rules version (e.g. ``"rules-v2"`` or a git hash).
    """

    dataset: str = ""
    model: str = ""
    prompt: str = ""
    policy: str = ""


@dataclass(frozen=True)
class EvaluationItem:
    """A single redacted email entry in the evaluation dataset.

    Attributes:
        id: Unique identifier within the dataset.
        subject: Email subject (redacted).
        sender_email: Sender email address (redacted).
        sender_name: Sender display name (redacted).
        snippet: Email body preview (redacted).
        has_attachments: Whether the email has attachments.
        ground_truth: The correct ``EmailCategory``.
        cohorts: List of cohort labels this item belongs to.
        redacted: Marker indicating this item has been redacted
            (all PII replaced with synthetic placeholders).
    """

    id: str
    subject: str
    sender_email: str
    sender_name: str
    snippet: str
    has_attachments: bool
    ground_truth: EmailCategory
    cohorts: tuple[str, ...] = ()
    redacted: bool = True


@dataclass(frozen=True)
class Prediction:
    """A single classifier prediction for one evaluation item.

    Attributes:
        item_id: References ``EvaluationItem.id``.
        category: The predicted ``EmailCategory``.
        confidence: Confidence score (0.0 – 1.0).
        source: Prediction source (e.g. ``"rules"``, ``"ai"``, ``"frozen"``).
    """

    item_id: str
    category: EmailCategory
    confidence: float
    source: str = ""


@dataclass(frozen=True)
class MetricRow:
    """Metrics for a single category or cohort.

    Attributes:
        recall: True Positive / (True Positive + False Negative).
        precision: True Positive / (True Positive + False Positive).
        review_rate: Fraction of ground-truth items in this category
            whose prediction confidence fell below the review threshold.
        support: Number of items in this group.
        tp: True positive count.
        fp: False positive count.
        fn: False negative count.
    """

    recall: float
    precision: float
    review_rate: float
    support: int
    tp: int = 0
    fp: int = 0
    fn: int = 0


@dataclass(frozen=True)
class EvaluationReport:
    """Full evaluation report capturing metrics and version metadata.

    Attributes:
        overall: Aggregate metrics across all items.
        per_category: Metrics keyed by ``EmailCategory``.
        per_cohort: Metrics keyed by cohort label.
        versions: Version information for reproducibility.
    """

    overall: MetricRow
    per_category: dict[str, MetricRow] = field(default_factory=dict)
    per_cohort: dict[str, MetricRow] = field(default_factory=dict)
    versions: VersionInfo = field(default_factory=VersionInfo)

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a plain dict (JSON-serialisable)."""
        return asdict(self)


@dataclass(frozen=True)
class EvaluationDataset:
    """A versioned, redacted evaluation dataset.

    Attributes:
        version: Dataset version string (semver).
        description: Human-readable description.
        cohorts: Mapping of cohort name → ``Cohort`` metadata.
        items: The evaluation items.
    """

    version: str
    description: str
    cohorts: dict[str, Cohort]
    items: tuple[EvaluationItem, ...]


# ─────────────────────────────────────────────────────────────────────
# Required cohorts — every baseline contract must define all eight
# and at least one item must belong to each.
# ─────────────────────────────────────────────────────────────────────

REQUIRED_COHORTS: list[str] = [
    "no-cv",
    "referral",
    "agency",
    "multi-applicant",
    "mixed-purpose",
    "follow-up",
    "misleading-attachment",
    "mixed-language",
]

# ─────────────────────────────────────────────────────────────────────
# Custom exception
# ─────────────────────────────────────────────────────────────────────


class EvaluationContractError(ValueError):
    """Raised when an evaluation contract is invalid or cannot be loaded."""


# ─────────────────────────────────────────────────────────────────────
# Contract implementation
# ─────────────────────────────────────────────────────────────────────


def _parse_item(raw: dict[str, Any]) -> EvaluationItem:
    """Parse a raw dict into an ``EvaluationItem``, validating fields."""
    item_id = raw.get("id")
    if not item_id:
        raise EvaluationContractError("Each item must have an 'id' field")

    ground_truth_raw = raw.get("ground_truth")
    if not ground_truth_raw:
        raise EvaluationContractError(f"Item {item_id} is missing 'ground_truth'")

    try:
        ground_truth = EmailCategory(ground_truth_raw)
    except ValueError:
        raise EvaluationContractError(
            f"Item {item_id}: invalid ground_truth {ground_truth_raw!r}; "
            f"valid values: {[e.value for e in EmailCategory]}"
        )

    return EvaluationItem(
        id=item_id,
        subject=raw.get("subject", ""),
        sender_email=raw.get("sender_email", ""),
        sender_name=raw.get("sender_name", ""),
        snippet=raw.get("snippet", ""),
        has_attachments=bool(raw.get("has_attachments", False)),
        ground_truth=ground_truth,
        cohorts=tuple(raw.get("cohorts", [])),
        redacted=bool(raw.get("redacted", True)),
    )


class EvaluationContract:
    """A validated evaluation contract backed by a JSON dataset.

    Usage::

        # Load from a JSON file
        contract = EvaluationContract.from_json("path/to/dataset.json")

        # Or construct from a parsed dict
        contract = EvaluationContract(raw_dict)

        # Run evaluation
        report = contract.run(predictor=my_predictor)

    Attributes:
        dataset: The validated ``EvaluationDataset``.
        versions: Extracted version info from the dataset header.
        frozen_predictions: Optional dict of pre-computed predictions.
        REQUIRED_COHORTS: The eight cohorts every baseline must cover.
    """

    REQUIRED_COHORTS = REQUIRED_COHORTS

    def __init__(self, raw: dict[str, Any]) -> None:
        self._validate(raw, self.REQUIRED_COHORTS)
        self.dataset = self._build_dataset(raw)

        # Extract version info from header fields
        self.versions = VersionInfo(
            dataset=raw.get("version", ""),
            model=raw.get("model_version", ""),
            prompt=raw.get("prompt_version", ""),
            policy=raw.get("policy_version", ""),
        )

        # Parse frozen predictions if provided
        fp_raw = raw.get("frozen_predictions", {})
        fp: dict[str, Prediction] = {}
        item_ids = {item.id for item in self.dataset.items}
        fp_metadata: dict[str, Any] = {}
        if isinstance(fp_raw.get("_metadata"), dict):
            fp_metadata = fp_raw["_metadata"]
        for item_id, pred_raw in fp_raw.items():
            if item_id == "_metadata":
                continue
            if item_id not in item_ids:
                raise EvaluationContractError(
                    f"Frozen prediction references unknown item: {item_id}"
                )
            try:
                category = EmailCategory(pred_raw["category"])
            except (ValueError, KeyError):
                raise EvaluationContractError(
                    f"Frozen prediction for {item_id}: invalid or missing category"
                )
            confidence = float(pred_raw.get("confidence", 0.0))
            if not (0.0 <= confidence <= 1.0):
                raise EvaluationContractError(
                    f"Frozen prediction for {item_id}: confidence {confidence} "
                    f"is outside [0.0, 1.0]"
                )
            fp[item_id] = Prediction(
                item_id=item_id,
                category=category,
                confidence=confidence,
                source=pred_raw.get("source", "frozen"),
            )
        self.frozen_predictions = fp
        self.frozen_metadata = fp_metadata

    # ── factory ──────────────────────────────────────────────────

    @classmethod
    def from_json(cls, path: str | Path) -> EvaluationContract:
        """Load and validate an evaluation contract from a JSON file.

        Args:
            path: Filesystem path to the JSON dataset.

        Returns:
            A validated ``EvaluationContract``.

        Raises:
            EvaluationContractError: If the file is missing, unparseable,
                or schema-invalid.
        """
        p = Path(path)
        if not p.exists():
            raise EvaluationContractError(f"Evaluation dataset not found: {p}")
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise EvaluationContractError(
                f"Failed to parse evaluation dataset {p}: {exc}"
            )
        return cls(raw)

    # ── validation ───────────────────────────────────────────────

    @staticmethod
    def _validate(
        raw: dict[str, Any],
        required_cohorts: list[str] | None = None,
    ) -> None:
        """Validate the raw dataset dict against the contract schema."""
        if not isinstance(raw, dict):
            raise EvaluationContractError(
                "Top-level dataset must be a JSON object"
            )
        if "version" not in raw:
            raise EvaluationContractError(
                "Dataset must include a 'version' field (semver)"
            )
        if "items" not in raw:
            raise EvaluationContractError(
                "Dataset must include an 'items' array"
            )
        if not isinstance(raw["items"], list):
            raise EvaluationContractError(
                "Dataset 'items' field must be a JSON array"
            )
        if not raw["items"]:
            raise EvaluationContractError(
                "Dataset 'items' array must not be empty"
            )

        # Validate cohorts header
        defined_cohorts: set[str] = set(raw.get("cohorts", {}).keys())

        # Validate shape: each item must be a plain dict
        for item in raw["items"]:
            if not isinstance(item, dict):
                raise EvaluationContractError(
                    "Each 'items' entry must be a JSON object (dict)"
                )

        # Check for duplicate ids
        seen_ids: set[str] = set()
        for item in raw["items"]:
            item_id = item.get("id", "")
            if item_id in seen_ids:
                raise EvaluationContractError(
                    f"Duplicate item id: {item_id!r}"
                )
            if item_id:
                seen_ids.add(item_id)

        # Validate each item
        for item in raw["items"]:
            gt = item.get("ground_truth")
            if not gt:
                raise EvaluationContractError(
                    f"Item {item.get('id', '<unknown>')} is missing 'ground_truth'"
                )
            try:
                EmailCategory(gt)
            except ValueError:
                raise EvaluationContractError(
                    f"Item {item.get('id', '<unknown>')}: "
                    f"invalid ground_truth {gt!r}; "
                    f"valid values: {[e.value for e in EmailCategory]}"
                )

            # Check cohorts
            item_cohorts = item.get("cohorts", [])
            if not isinstance(item_cohorts, list):
                raise EvaluationContractError(
                    f"Item {item.get('id', '<unknown>')}: 'cohorts' must be a list"
                )
            for cohort_name in item_cohorts:
                if cohort_name not in defined_cohorts:
                    raise EvaluationContractError(
                        f"Item {item.get('id', '<unknown>')} references "
                        f"unknown cohort {cohort_name!r}; "
                        f"defined cohorts: {sorted(defined_cohorts)}"
                    )

        # Validate that all required cohorts are defined AND non-empty
        if required_cohorts:
            cohort_item_counts: dict[str, int] = {c: 0 for c in required_cohorts}
            missing_cohorts = [c for c in required_cohorts if c not in defined_cohorts]
            if missing_cohorts:
                raise EvaluationContractError(
                    f"Required cohorts missing from header: {missing_cohorts}; "
                    f"defined: {sorted(defined_cohorts)}"
                )
            for item in raw["items"]:
                for c in item.get("cohorts", []):
                    if c in cohort_item_counts:
                        cohort_item_counts[c] += 1
            empty_cohorts = [
                c for c, count in cohort_item_counts.items() if count == 0
            ]
            if empty_cohorts:
                raise EvaluationContractError(
                    f"Required cohorts have zero items: {empty_cohorts}"
                )

    @staticmethod
    def _build_dataset(raw: dict[str, Any]) -> EvaluationDataset:
        """Build an ``EvaluationDataset`` from a validated raw dict."""
        cohorts_raw = raw.get("cohorts", {})
        cohorts = {
            name: Cohort(label=meta.get("label", name), color=meta.get("color", "#ccc"))
            for name, meta in cohorts_raw.items()
        }
        items = tuple(_parse_item(item) for item in raw["items"])
        return EvaluationDataset(
            version=raw["version"],
            description=raw.get("description", ""),
            cohorts=cohorts,
            items=items,
        )

    # ── evaluation runner ───────────────────────────────────────

    def run(
        self,
        predictor: Predictor | None = None,
        needs_review_threshold: float = 0.5,
        frozen_predictions: dict[str, Prediction] | None = None,
        source_versions: VersionInfo | None = None,
    ) -> EvaluationReport:
        """Run evaluation and produce a report.

        Args:
            predictor: A callable ``(EvaluationItem) → Prediction``.
                Optional when all items have frozen predictions.
            needs_review_threshold: Confidence below this value marks the
                prediction as ``needs_review``.
            frozen_predictions: Optional override of
                ``self.frozen_predictions``.  When provided these take
                precedence over dataset-embedded frozen predictions.
            source_versions: Optional ``VersionInfo`` that overrides the
                ``model``, ``prompt``, and ``policy`` fields of the report
                version metadata.  Used when frozen predictions carry their
                own predictor version that may differ from the dataset
                header (e.g. predictions recorded from a later classifier
                version).  ``dataset`` is always preserved from the dataset.

        Returns:
            An ``EvaluationReport`` with metrics.
        """
        fp = (
            frozen_predictions
            if frozen_predictions is not None
            else self.frozen_predictions
        )
        effective_versions = self.versions
        if source_versions is not None:
            effective_versions = VersionInfo(
                dataset=self.versions.dataset,
                model=source_versions.model or self.versions.model,
                prompt=source_versions.prompt or self.versions.prompt,
                policy=source_versions.policy or self.versions.policy,
            )
        return self._run(
            dataset=self.dataset,
            predictor=predictor,
            frozen_predictions=fp,
            versions=effective_versions,
            needs_review_threshold=needs_review_threshold,
        )

    @staticmethod
    def _run(
        dataset: EvaluationDataset,
        predictor: Predictor | None = None,
        frozen_predictions: dict[str, Prediction] | None = None,
        versions: VersionInfo | None = None,
        needs_review_threshold: float = 0.5,
    ) -> EvaluationReport:
        """Static evaluation runner (used from tests without building a contract)."""
        fp = frozen_predictions or {}

        predictions: list[Prediction] = []
        for item in dataset.items:
            if item.id in fp:
                pred = fp[item.id]
                if pred.item_id != item.id:
                    raise EvaluationContractError(
                        f"Frozen prediction item_id mismatch: expected {item.id}, "
                        f"got {pred.item_id}"
                    )
                if not (0.0 <= pred.confidence <= 1.0):
                    raise EvaluationContractError(
                        f"Prediction for {item.id}: confidence {pred.confidence} "
                        f"is outside [0.0, 1.0]"
                    )
                predictions.append(pred)
            elif predictor is not None:
                pred = predictor(item)
                if not isinstance(pred, Prediction):
                    raise EvaluationContractError(
                        f"Predictor returned non-Prediction for {item.id}: "
                        f"{type(pred).__name__}"
                    )
                if pred.item_id != item.id:
                    raise EvaluationContractError(
                        f"Predictor returned prediction for wrong item: "
                        f"expected {item.id}, got {pred.item_id}"
                    )
                if not (0.0 <= pred.confidence <= 1.0):
                    raise EvaluationContractError(
                        f"Predictor for {item.id}: confidence {pred.confidence} "
                        f"is outside [0.0, 1.0]"
                    )
                predictions.append(pred)
            else:
                raise EvaluationContractError(
                    f"Item {item.id} has no frozen prediction and no predictor was provided"
                )

        return _compute_metrics(dataset, predictions, versions, needs_review_threshold)


# ─────────────────────────────────────────────────────────────────────
# Metric computation
# ─────────────────────────────────────────────────────────────────────


def _compute_metrics(
    dataset: EvaluationDataset,
    predictions: list[Prediction],
    versions: VersionInfo | None,
    needs_review_threshold: float,
) -> EvaluationReport:
    """Compute recall, precision, review rate from predictions.

    Review rate attribution uses ground-truth categories:
    ``review_rate`` for category X is the fraction of items whose
    **ground truth** is X and whose prediction confidence fell below
    the ``needs_review_threshold``.  It answers:
    "What fraction of true X emails need manual review?"

    This differs from "fraction of items predicted X that need review",
    which would use predicted category instead of ground truth.

    The primary target is the ``recruitment`` category (Job Application).
    However, per-category metrics are computed for all categories.
    """
    if len(predictions) != len(dataset.items):
        raise EvaluationContractError(
            f"Prediction count ({len(predictions)}) does not match "
            f"item count ({len(dataset.items)})"
        )

    # Build lookup: item id → ground truth
    gt_map: dict[str, EmailCategory] = {item.id: item.ground_truth for item in dataset.items}

    # Build lookup: item id → item (for cohort info)
    item_map: dict[str, EvaluationItem] = {item.id: item for item in dataset.items}

    # ── Confusion buckets ────────────────────────────────────────
    # We compute per-category metrics as one-vs-rest.
    # For each item:
    #   - If predicted category == GT: TP for that category.
    #   - If predicted category != GT: FP for predicted, FN for GT.

    all_categories: set[EmailCategory] = set()
    for item in dataset.items:
        all_categories.add(item.ground_truth)
    for pred in predictions:
        all_categories.add(pred.category)

    # Per-category: tp, fp, fn, review_count
    cat_stats: dict[EmailCategory, dict[str, int]] = {
        cat: {"tp": 0, "fp": 0, "fn": 0, "review": 0} for cat in all_categories
    }

    # Per-cohort: same structure
    all_cohort_names: set[str] = set()
    for item in dataset.items:
        all_cohort_names.update(item.cohorts)
    cohort_stats: dict[str, dict[str, int]] = {
        cohort: {"tp": 0, "fp": 0, "fn": 0, "review": 0, "support": 0}
        for cohort in all_cohort_names
    }

    for pred in predictions:
        item = item_map[pred.item_id]
        gt = gt_map[pred.item_id]

        # Per-category
        if pred.category == gt:
            cat_stats[pred.category]["tp"] += 1
        else:
            cat_stats[pred.category]["fp"] += 1
            cat_stats[gt]["fn"] += 1

        if pred.confidence < needs_review_threshold:
            cat_stats[gt]["review"] += 1

        # Per-cohort
        for cohort in item.cohorts:
            if pred.category == gt:
                cohort_stats[cohort]["tp"] += 1
            else:
                cohort_stats[cohort]["fp"] += 1
                cohort_stats[cohort]["fn"] += 1
            if pred.confidence < needs_review_threshold:
                cohort_stats[cohort]["review"] += 1
            cohort_stats[cohort]["support"] += 1

    # ── Build MetricRow per category ────────────────────────────
    per_category: dict[str, MetricRow] = {}
    for cat in sorted(all_categories, key=lambda c: c.value):
        s = cat_stats[cat]
        tp, fp, fn, review = s["tp"], s["fp"], s["fn"], s["review"]
        support = tp + fn
        recall = tp / support if support > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        review_rate = review / support if support > 0 else 0.0
        per_category[cat.value] = MetricRow(
            recall=recall,
            precision=precision,
            review_rate=review_rate,
            support=support,
            tp=tp,
            fp=fp,
            fn=fn,
        )

    # ── Build MetricRow per cohort ──────────────────────────────
    per_cohort: dict[str, MetricRow] = {}
    for cohort in sorted(all_cohort_names):
        s = cohort_stats[cohort]
        tp, fp, fn, review, support = (
            s["tp"], s["fp"], s["fn"], s["review"], s["support"]
        )
        recall = tp / support if support > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        review_rate = review / support if support > 0 else 0.0
        per_cohort[cohort] = MetricRow(
            recall=recall,
            precision=precision,
            review_rate=review_rate,
            support=support,
            tp=tp,
            fp=fp,
            fn=fn,
        )

    # ── Overall metrics ─────────────────────────────────────────
    total_tp = sum(cat_stats[cat]["tp"] for cat in all_categories)
    total_fp = sum(cat_stats[cat]["fp"] for cat in all_categories)
    total_fn = sum(cat_stats[cat]["fn"] for cat in all_categories)
    total_support = len(dataset.items)

    overall_recall = total_tp / total_support if total_support > 0 else 0.0
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    total_review = sum(cat_stats[cat]["review"] for cat in all_categories)
    overall_review_rate = total_review / total_support if total_support > 0 else 0.0

    overall = MetricRow(
        recall=overall_recall,
        precision=overall_precision,
        review_rate=overall_review_rate,
        support=total_support,
        tp=total_tp,
        fp=total_fp,
        fn=total_fn,
    )

    return EvaluationReport(
        overall=overall,
        per_category=per_category,
        per_cohort=per_cohort,
        versions=versions or VersionInfo(),
    )
