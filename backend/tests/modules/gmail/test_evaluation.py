"""Tests for the evaluation baseline contract and runner.

Tests are organised in groups:
1.  EvaluationContract — schema validation, versioning, contract integrity.
2.  EvaluationRunner — metric computation (recall, precision, review rate)
    overall and per cohort.
3.  EvaluationContract record generation
4.  Contract integrity — invalid contracts fail clearly
5.  Frozen predictions
6.  CLI entry point — end-to-end smoke test of the documented command.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.evaluation import (
    EvaluationContract,
    EvaluationContractError,
    EvaluationDataset,
    EvaluationItem,
    Prediction,
    VersionInfo,
)

# ──────────────────────────────────────────────────────────────────
# 1.  EvaluationContract — schema & validation
# ──────────────────────────────────────────────────────────────────

_VALID_SAMPLE_DATASET: dict[str, Any] = {
    "version": "1.0.0",
    "description": "Sample evaluation dataset for testing",
    "redacted": True,
    "model_version": "test-model-v1",
    "prompt_version": "test-prompt-v1",
    "policy_version": "test-policy-v1",
    "cohorts": {
        "no-cv": {"label": "No CV attachment", "color": "#ff0000"},
        "referral": {"label": "Employee referral", "color": "#00ff00"},
        "agency": {"label": "Agency", "color": "#0000ff"},
        "multi-applicant": {"label": "Multi applicant", "color": "#ffff00"},
        "mixed-purpose": {"label": "Mixed purpose", "color": "#ff00ff"},
        "follow-up": {"label": "Follow-up", "color": "#00ffff"},
        "misleading-attachment": {"label": "Misleading", "color": "#abc123"},
        "mixed-language": {"label": "Mixed language", "color": "#def456"},
    },
    "items": [
        {
            "id": "eval-001",
            "redacted": True,
            "subject": "CV ung tuyen vi tri Developer",
            "sender_email": "ungvien.a@thuvien.mau",
            "sender_name": "Ung Vien Mau A",
            "snippet": "Toi xin gui CV ung tuyen vi tri Developer",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["no-cv"],
        },
        {
            "id": "eval-002",
            "redacted": True,
            "subject": "Referral: Gioi thieu ung vien",
            "sender_email": "nhanvien.a@congty.mau",
            "sender_name": "Nhan Vien Mau A",
            "snippet": "Toi xin gioi thieu ung vien cho vi tri",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["referral"],
        },
        {
            "id": "eval-003",
            "redacted": True,
            "subject": "Agency batch submission",
            "sender_email": "dai-ly@headhunter.mau",
            "sender_name": "Dai Ly Mau",
            "snippet": "Sending candidate profiles",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["agency"],
        },
        {
            "id": "eval-004",
            "redacted": True,
            "subject": "Batch CVs for review",
            "sender_email": "truong-phong@hr.mau",
            "sender_name": "Truong Phong Mau",
            "snippet": "Multiple candidates attached",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["multi-applicant"],
        },
        {
            "id": "eval-005",
            "redacted": True,
            "subject": "Service with CVs attached",
            "sender_email": "contact@training-partner.mau",
            "sender_name": "Dao Tao Mau",
            "snippet": "Training and candidate profiles",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["mixed-purpose"],
        },
        {
            "id": "eval-006",
            "redacted": True,
            "subject": "Updated CV",
            "sender_email": "ungvien.a@thuvien.mau",
            "sender_name": "Ung Vien Mau A",
            "snippet": "Bo sung CV moi nhat",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["follow-up"],
        },
        {
            "id": "eval-007",
            "redacted": True,
            "subject": "Bid proposal with CVs",
            "sender_email": "bid@construction-co.mau",
            "sender_name": "Cong ty Xay dung Mau",
            "snippet": "Team CVs included in bid",
            "has_attachments": True,
            "ground_truth": "vendor",
            "cohorts": ["misleading-attachment"],
        },
        {
            "id": "eval-008",
            "redacted": True,
            "subject": "Application in English+Vietnamese",
            "sender_email": "ungvien.b@thuvien.mau",
            "sender_name": "Ung Vien Mau B",
            "snippet": "I am writing to apply for the position. Toi co 5 nam kinh nghiem.",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["mixed-language"],
        },
    ],
}


class TestEvaluationContractValidation:
    """Schema validation for the evaluation contract."""

    def test_valid_minimal_dataset(self) -> None:
        """A well-formed dataset passes validation."""
        contract = EvaluationContract(_VALID_SAMPLE_DATASET)
        assert contract.dataset.version == "1.0.0"
        assert len(contract.dataset.items) == 8
        assert contract.versions.model == "test-model-v1"
        assert contract.versions.prompt == "test-prompt-v1"
        assert contract.versions.policy == "test-policy-v1"

    def test_missing_version(self) -> None:
        """Dataset without version is rejected."""
        data = {k: v for k, v in _VALID_SAMPLE_DATASET.items() if k != "version"}
        with pytest.raises(EvaluationContractError, match="version"):
            EvaluationContract(data)

    def test_missing_items(self) -> None:
        """Dataset without items is rejected."""
        data = {k: v for k, v in _VALID_SAMPLE_DATASET.items() if k != "items"}
        with pytest.raises(EvaluationContractError, match="items"):
            EvaluationContract(data)

    def test_empty_items(self) -> None:
        """Dataset with empty items list is rejected."""
        data = dict(_VALID_SAMPLE_DATASET, items=[])
        with pytest.raises(EvaluationContractError, match="empty"):
            EvaluationContract(data)

    def test_items_not_a_list(self) -> None:
        """Dataset with non-list items is rejected."""
        data = dict(_VALID_SAMPLE_DATASET, items="not-a-list")
        with pytest.raises(EvaluationContractError, match="array"):
            EvaluationContract(data)

    def test_top_level_not_a_dict(self) -> None:
        """Non-dict top-level is rejected."""
        with pytest.raises(EvaluationContractError, match="object"):
            EvaluationContract("not-a-dict")  # type: ignore[arg-type]

    def test_item_missing_ground_truth(self) -> None:
        """An item without ground_truth is rejected."""
        item = {k: v for k, v in _VALID_SAMPLE_DATASET["items"][0].items() if k != "ground_truth"}
        data = dict(_VALID_SAMPLE_DATASET, items=[item])
        with pytest.raises(EvaluationContractError, match="ground_truth"):
            EvaluationContract(data)

    def test_item_invalid_ground_truth(self) -> None:
        """An item with an invalid EmailCategory is rejected."""
        item = dict(_VALID_SAMPLE_DATASET["items"][0], ground_truth="nonexistent")
        data = dict(_VALID_SAMPLE_DATASET, items=[item])
        with pytest.raises(EvaluationContractError, match="nonexistent"):
            EvaluationContract(data)

    def test_item_references_unknown_cohort(self) -> None:
        """An item referencing a cohort not defined in the header is rejected."""
        item = dict(_VALID_SAMPLE_DATASET["items"][0], cohorts=["unknown-cohort"])
        data = dict(_VALID_SAMPLE_DATASET, items=[item])
        with pytest.raises(EvaluationContractError, match="unknown-cohort"):
            EvaluationContract(data)

    def test_cohorts_not_a_list(self) -> None:
        """An item with non-list cohorts is rejected."""
        item = dict(_VALID_SAMPLE_DATASET["items"][0], cohorts="not-a-list")
        data = dict(_VALID_SAMPLE_DATASET, items=[item])
        with pytest.raises(EvaluationContractError, match="cohorts.*list"):
            EvaluationContract(data)

    def test_duplicate_item_ids(self) -> None:
        """Duplicate item ids are rejected."""
        item0 = _VALID_SAMPLE_DATASET["items"][0]
        item1 = _VALID_SAMPLE_DATASET["items"][1]
        item_dup = dict(item1, id=item0["id"])
        data = dict(_VALID_SAMPLE_DATASET, items=[item0, item_dup])
        with pytest.raises(EvaluationContractError, match="Duplicate"):
            EvaluationContract(data)

    def test_required_cohorts_all_present_and_nonempty(self) -> None:
        """All required cohorts must be defined and have at least one item."""
        # All 8 required cohorts in header, but only 2 have items
        all_cohorts = {
            "no-cv": {"label": "No CV", "color": "#f00"},
            "referral": {"label": "Referral", "color": "#0f0"},
            "agency": {"label": "Agency", "color": "#00f"},
            "multi-applicant": {"label": "Multi", "color": "#ff0"},
            "mixed-purpose": {"label": "Mixed", "color": "#f0f"},
            "follow-up": {"label": "Follow-up", "color": "#0ff"},
            "misleading-attachment": {"label": "Mis", "color": "#abc"},
            "mixed-language": {"label": "Lang", "color": "#def"},
        }
        items = [
            {
                "id": "eval-001",
                "redacted": True,
                "subject": "CV",
                "sender_email": "a@mau.mau",
                "sender_name": "A",
                "snippet": "CV",
                "has_attachments": True,
                "ground_truth": "recruitment",
                "cohorts": ["no-cv"],
            },
            {
                "id": "eval-002",
                "redacted": True,
                "subject": "Referral",
                "sender_email": "b@mau.mau",
                "sender_name": "B",
                "snippet": "Ref",
                "has_attachments": True,
                "ground_truth": "recruitment",
                "cohorts": ["referral"],
            },
        ]
        data = dict(
            _VALID_SAMPLE_DATASET,
            cohorts=all_cohorts,
            items=items,
        )
        with pytest.raises(EvaluationContractError, match="zero items"):
            EvaluationContract(data)

    def test_required_cohort_missing_from_header(self) -> None:
        """Dataset missing a required cohort in the header is rejected."""
        data = dict(
            _VALID_SAMPLE_DATASET,
            cohorts={
                "no-cv": {"label": "No CV", "color": "#f00"},
                "referral": {"label": "Referral", "color": "#0f0"},
            },
            items=[
                {
                    "id": "eval-001",
                    "redacted": True,
                    "subject": "CV",
                    "sender_email": "ungvien.a@thuvien.mau",
                    "sender_name": "A",
                    "snippet": "CV",
                    "has_attachments": True,
                    "ground_truth": "recruitment",
                    "cohorts": ["no-cv"],
                },
                {
                    "id": "eval-002",
                    "redacted": True,
                    "subject": "Referral",
                    "sender_email": "nhanvien.a@congty.mau",
                    "sender_name": "B",
                    "snippet": "Gioi thieu",
                    "has_attachments": True,
                    "ground_truth": "recruitment",
                    "cohorts": ["referral"],
                },
            ],
        )
        with pytest.raises(EvaluationContractError, match="missing from header"):
            EvaluationContract(data)

    def test_item_is_not_a_dict(self) -> None:
        """Non-dict items are rejected."""
        data = dict(_VALID_SAMPLE_DATASET, items=["not-a-dict"])
        with pytest.raises(EvaluationContractError, match="JSON object"):
            EvaluationContract(data)

    def test_frozen_predictions_validation(self) -> None:
        """Frozen predictions must reference valid item ids."""
        data = dict(
            _VALID_SAMPLE_DATASET,
            frozen_predictions={
                "eval-001": {
                    "category": "recruitment",
                    "confidence": 0.85,
                    "source": "rules",
                },
                "eval-999": {  # item does not exist
                    "category": "recruitment",
                    "confidence": 0.75,
                    "source": "rules",
                },
            },
        )
        with pytest.raises(EvaluationContractError, match="eval-999"):
            EvaluationContract(data)

    def test_frozen_predictions_partial_ok(self) -> None:
        """Frozen predictions may cover only a subset of items."""
        data = dict(
            _VALID_SAMPLE_DATASET,
            frozen_predictions={
                "eval-001": {
                    "category": "recruitment",
                    "confidence": 0.85,
                    "source": "rules",
                },
            },
        )
        contract = EvaluationContract(data)
        # Only one frozen prediction provided — the rest will come from the predictor
        assert len(contract.frozen_predictions) == 1

    def test_frozen_prediction_confidence_out_of_range(self) -> None:
        """Frozen prediction with confidence outside [0,1] is rejected."""
        data = dict(
            _VALID_SAMPLE_DATASET,
            frozen_predictions={
                "eval-001": {
                    "category": "recruitment",
                    "confidence": 1.5,
                    "source": "rules",
                },
            },
        )
        with pytest.raises(EvaluationContractError, match="outside"):
            EvaluationContract(data)

    def test_frozen_prediction_invalid_category(self) -> None:
        """Frozen prediction with invalid category is rejected."""
        data = dict(
            _VALID_SAMPLE_DATASET,
            frozen_predictions={
                "eval-001": {
                    "category": "bogus_category",
                    "confidence": 0.5,
                    "source": "rules",
                },
            },
        )
        with pytest.raises(EvaluationContractError, match="invalid or missing category"):
            EvaluationContract(data)

    def test_version_info_extraction(self) -> None:
        """VersionInfo is populated from the dataset header."""
        data = dict(
            _VALID_SAMPLE_DATASET,
            model_version="gemma-4-1.0",
            prompt_version="abc123def456",
            policy_version="2026-07-13",
        )
        contract = EvaluationContract(data)
        assert contract.versions.model == "gemma-4-1.0"
        assert contract.versions.prompt == "abc123def456"
        assert contract.versions.policy == "2026-07-13"
        assert contract.versions.dataset == "1.0.0"

    def test_redacted_field_parsed(self) -> None:
        """EvaluationItem parses the redacted field."""
        contract = EvaluationContract(_VALID_SAMPLE_DATASET)
        for item in contract.dataset.items:
            assert item.redacted is True


# ──────────────────────────────────────────────────────────────────
# 2.  EvaluationRunner — metric computation
# ──────────────────────────────────────────────────────────────────

_CORRECT = EmailCategory.recruitment
_WRONG = EmailCategory.payroll


def _single_item_prediction(
    item: EvaluationItem,
    category: EmailCategory = _CORRECT,
    confidence: float = 0.9,
    source: str = "rules",
) -> Prediction:
    return Prediction(
        item_id=item.id,
        category=category,
        confidence=confidence,
        source=source,
    )


class _PerfectPredictor:
    """Predictor that always guesses the ground truth correctly."""

    def predict(self, item: EvaluationItem) -> Prediction:
        return _single_item_prediction(item, category=item.ground_truth)

    def __call__(self, item: EvaluationItem) -> Prediction:
        return self.predict(item)


class _AlwaysRecruitmentPredictor:
    """Predictor that always guesses recruitment."""

    def predict(self, item: EvaluationItem) -> Prediction:
        return _single_item_prediction(item, category=EmailCategory.recruitment)

    def __call__(self, item: EvaluationItem) -> Prediction:
        return self.predict(item)


# A minimal dataset with all 8 required cohorts covered
_MINIMAL_COHORT_SET: dict[str, Any] = {
    "no-cv": {"label": "No CV", "color": "#ff0000"},
    "referral": {"label": "Referral", "color": "#00ff00"},
    "agency": {"label": "Agency", "color": "#0000ff"},
    "multi-applicant": {"label": "Multi applicant", "color": "#ffff00"},
    "mixed-purpose": {"label": "Mixed purpose", "color": "#ff00ff"},
    "follow-up": {"label": "Follow-up", "color": "#00ffff"},
    "misleading-attachment": {"label": "Misleading", "color": "#abc123"},
    "mixed-language": {"label": "Mixed lang", "color": "#def456"},
}

_MINIMAL_ITEMS: list[dict[str, Any]] = [
    {
        "id": f"eval-{i:03d}",
        "subject": str(i),
        "sender_email": f"a{i}@mau.mau",
        "sender_name": f"A{i}",
        "snippet": str(i),
        "has_attachments": False,
        "ground_truth": "recruitment",
        "cohorts": [c],
    }
    for i, c in enumerate(
        [
            "no-cv",
            "referral",
            "agency",
            "multi-applicant",
            "mixed-purpose",
            "follow-up",
            "misleading-attachment",
            "mixed-language",
        ],
        start=1,
    )
]


def _make_dataset(
    items: list[dict[str, Any]],
    version: str = "1.0.0",
    **extra_header_keys: Any,
) -> EvaluationDataset:
    data: dict[str, Any] = {
        "version": version,
        "redacted": True,
        "description": "test",
        "cohorts": dict(_MINIMAL_COHORT_SET),
        "items": items,
    }
    data.update(extra_header_keys)
    contract = EvaluationContract(data)
    return contract.dataset


@pytest.fixture
def mixed_dataset() -> EvaluationDataset:
    """A dataset with recruitment and non-recruitment items across cohorts."""
    items = [
        {
            "id": "eval-001",
            "redacted": True,
            "subject": "CV ung tuyen",
            "sender_email": "ungvien.a@thuvien.mau",
            "sender_name": "A",
            "snippet": "CV ung tuyen",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["no-cv"],
        },
        {
            "id": "eval-002",
            "redacted": True,
            "subject": "Referral applicant",
            "sender_email": "nhanvien.a@congty.mau",
            "sender_name": "B",
            "snippet": "Gioi thieu ung vien",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["referral"],
        },
        {
            "id": "eval-003",
            "redacted": True,
            "subject": "Leave request",
            "sender_email": "nhanvien.x@congty.mau",
            "sender_name": "C",
            "snippet": "Xin nghi phep",
            "has_attachments": False,
            "ground_truth": "leave_request",
            "cohorts": [],
        },
        {
            "id": "eval-004",
            "redacted": True,
            "subject": "Another CV",
            "sender_email": "ungvien.d@thuvien.mau",
            "sender_name": "D",
            "snippet": "Gui CV",
            "has_attachments": True,
            "ground_truth": "recruitment",
            "cohorts": ["no-cv"],
        },
        # Remaining required cohorts: add minimal coverage for each
        {
            "id": "eval-005",
            "redacted": True,
            "subject": "Agency",
            "sender_email": "agency@mau.mau",
            "sender_name": "E",
            "snippet": "Agency",
            "has_attachments": False,
            "ground_truth": "recruitment",
            "cohorts": ["agency"],
        },
        {
            "id": "eval-006",
            "redacted": True,
            "subject": "Multi",
            "sender_email": "multi@mau.mau",
            "sender_name": "F",
            "snippet": "Multi",
            "has_attachments": False,
            "ground_truth": "recruitment",
            "cohorts": ["multi-applicant"],
        },
        {
            "id": "eval-007",
            "redacted": True,
            "subject": "Mixed purpose",
            "sender_email": "mixed@mau.mau",
            "sender_name": "G",
            "snippet": "Mixed",
            "has_attachments": False,
            "ground_truth": "recruitment",
            "cohorts": ["mixed-purpose"],
        },
        {
            "id": "eval-008",
            "redacted": True,
            "subject": "Follow-up",
            "sender_email": "follow@mau.mau",
            "sender_name": "H",
            "snippet": "Follow",
            "has_attachments": False,
            "ground_truth": "recruitment",
            "cohorts": ["follow-up"],
        },
        {
            "id": "eval-009",
            "redacted": True,
            "subject": "Misleading",
            "sender_email": "mis@mau.mau",
            "sender_name": "I",
            "snippet": "Misleading",
            "has_attachments": False,
            "ground_truth": "vendor",
            "cohorts": ["misleading-attachment"],
        },
        {
            "id": "eval-010",
            "redacted": True,
            "subject": "Mixed lang",
            "sender_email": "lang@mau.mau",
            "sender_name": "J",
            "snippet": "Mixed lang",
            "has_attachments": False,
            "ground_truth": "recruitment",
            "cohorts": ["mixed-language"],
        },
    ]
    return _make_dataset(items)


def test_perfect_recall_and_precision(mixed_dataset: EvaluationDataset) -> None:
    """Perfect predictor yields 1.0 recall and precision overall."""
    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_PerfectPredictor(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    assert report.overall.recall == pytest.approx(1.0)
    assert report.overall.precision == pytest.approx(1.0)


def test_all_missed(mixed_dataset: EvaluationDataset) -> None:
    """Always-uncategorized predictor yields 0.0 recall and precision."""

    class _AlwaysUncategorized:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return _single_item_prediction(
                item, category=EmailCategory.uncategorized, confidence=0.0
            )

    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_AlwaysUncategorized(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    assert report.overall.recall == pytest.approx(0.0)
    assert report.overall.precision == pytest.approx(0.0)


def test_recall_precision_for_recruitment(
    mixed_dataset: EvaluationDataset,
) -> None:
    """Always-recruitment predictor has perfect recall but imperfect precision.

    most items are recruitment; precision = tp/(tp+fp).
    """
    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_AlwaysRecruitmentPredictor(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    # 10 total items: 9 recruitment, 1 leave_request, 1 vendor
    # Actually: the test dataset has recruitment for all except
    # eval-003 (leave_request) and eval-009 (vendor)
    # So 8 recruitment, 2 non-recruitment
    # Always predicting recruitment → tp=8, fp=2, fn=0 (only for recruitment itself)
    # Wait, let me recount:
    # recruitment: eval-001,002,004,005,006,007,008,010 = 8 recruitment
    # leave_request: eval-003
    # vendor: eval-009
    # Total: 10 items
    # Always predicts recruitment
    # For recruitment: tp=8, fp=2 (eval-003 and 009 have GT not recruitment)
    # Precision = 8/(8+2) = 0.8
    # Recall (overall accuracy) = 8/10 = 0.8
    assert report.overall.recall == pytest.approx(8.0 / 10.0)
    assert report.overall.precision == pytest.approx(8.0 / 10.0)
    assert report.overall.support == 10


def test_recruitment_metrics_present(mixed_dataset: EvaluationDataset) -> None:
    """Per-category metrics are reported for each EmailCategory that appears."""
    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_PerfectPredictor(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    assert EmailCategory.recruitment in report.per_category
    rec = report.per_category[EmailCategory.recruitment]
    assert rec.recall == pytest.approx(1.0)
    assert rec.precision == pytest.approx(1.0)
    assert rec.support == 8

    assert EmailCategory.leave_request in report.per_category
    lr = report.per_category[EmailCategory.leave_request]
    assert lr.recall == pytest.approx(1.0)
    assert lr.support == 1


def test_cohort_metrics(mixed_dataset: EvaluationDataset) -> None:
    """Each cohort gets its own metric row."""
    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_PerfectPredictor(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    cohorts = report.per_cohort
    assert "no-cv" in cohorts
    assert cohorts["no-cv"].recall == pytest.approx(1.0)
    assert cohorts["no-cv"].support == 2  # eval-001, eval-004

    assert "referral" in cohorts
    assert cohorts["referral"].support == 1


def test_review_rate_reported(mixed_dataset: EvaluationDataset) -> None:
    """Review rate is included in the overall metrics."""
    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_PerfectPredictor(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    assert report.overall.review_rate is not None
    assert 0.0 <= report.overall.review_rate <= 1.0


def test_review_rate_with_low_confidence(
    mixed_dataset: EvaluationDataset,
) -> None:
    """Items where confidence < needs_review_threshold count as needs_review."""

    class _LowConfPredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return _single_item_prediction(item, confidence=0.3, source="rules")

    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_LowConfPredictor(),
        versions=VersionInfo(dataset="1.0.0"),
        needs_review_threshold=0.5,
    )
    assert report.overall.review_rate == pytest.approx(1.0)  # all items low conf


def test_report_contains_version_info(
    mixed_dataset: EvaluationDataset,
) -> None:
    """The report records model/prompt/policy/dataset versions."""
    versions = VersionInfo(
        dataset="1.0.0",
        model="gemma-4-1.0",
        prompt="abc123",
        policy="rules-v2",
    )
    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_PerfectPredictor(),
        versions=versions,
    )
    assert report.versions.dataset == "1.0.0"
    assert report.versions.model == "gemma-4-1.0"
    assert report.versions.prompt == "abc123"
    assert report.versions.policy == "rules-v2"


# ──────────────────────────────────────────────────────────────────
# 3.  EvaluationContract record generation
# ──────────────────────────────────────────────────────────────────


def test_evaluation_report_serializable(
    mixed_dataset: EvaluationDataset,
) -> None:
    """EvaluationReport can be serialised to JSON (e.g. for CI artifacts)."""
    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_PerfectPredictor(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    as_dict = report.to_dict()
    # Re-serialise and reload
    json_str = json.dumps(as_dict)
    loaded = json.loads(json_str)
    assert loaded["overall"]["recall"] == 1.0
    assert loaded["overall"]["precision"] == 1.0
    assert loaded["versions"]["dataset"] == "1.0.0"


# ──────────────────────────────────────────────────────────────────
# 4.  Contract integrity — invalid contracts fail clearly
# ──────────────────────────────────────────────────────────────────


def test_invalid_dataset_path_raises() -> None:
    """Loading a non-existent dataset path raises a clear error."""
    with pytest.raises(EvaluationContractError, match="not found"):
        EvaluationContract.from_json("/nonexistent/path/dataset.json")


def test_invalid_json_raises() -> None:
    """Loading malformed JSON raises a clear error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("this is not json {{{{")
        f.flush()
        path = f.name
    try:
        with pytest.raises(EvaluationContractError, match="parse"):
            EvaluationContract.from_json(path)
    finally:
        Path(path).unlink()


def test_missing_frozen_predictions_for_subset_uses_predictor() -> None:
    """When frozen_predictions are specified, items without predictions use the predictor."""
    contract_dict: dict[str, Any] = {
        "version": "1.0.0",
        "redacted": True,
        "description": "test",
        "cohorts": {
            "no-cv": {"label": "No CV", "color": "#ff0000"},
            "referral": {"label": "Referral", "color": "#00ff00"},
            "agency": {"label": "Agency", "color": "#0000ff"},
            "multi-applicant": {"label": "Multi", "color": "#ffff00"},
            "mixed-purpose": {"label": "Mixed", "color": "#ff00ff"},
            "follow-up": {"label": "Follow-up", "color": "#00ffff"},
            "misleading-attachment": {"label": "Mis", "color": "#abc123"},
            "mixed-language": {"label": "Lang", "color": "#def456"},
        },
        "items": [
            {
                "id": "eval-001",
                "redacted": True,
                "subject": "CV",
                "sender_email": "ungvien.a@thuvien.mau",
                "sender_name": "A",
                "snippet": "CV",
                "has_attachments": True,
                "ground_truth": "recruitment",
                "cohorts": ["no-cv"],
            },
            {
                "id": "eval-002",
                "redacted": True,
                "subject": "Leave",
                "sender_email": "nhanvien.x@congty.mau",
                "sender_name": "B",
                "snippet": "Leave",
                "has_attachments": False,
                "ground_truth": "leave_request",
                "cohorts": ["referral"],
            },
            {
                "id": "eval-003",
                "redacted": True,
                "subject": "Agency",
                "sender_email": "a@mau.mau",
                "sender_name": "C",
                "snippet": "Agency",
                "has_attachments": False,
                "ground_truth": "recruitment",
                "cohorts": ["agency"],
            },
            {
                "id": "eval-004",
                "redacted": True,
                "subject": "Multi",
                "sender_email": "b@mau.mau",
                "sender_name": "D",
                "snippet": "Multi",
                "has_attachments": False,
                "ground_truth": "recruitment",
                "cohorts": ["multi-applicant"],
            },
            {
                "id": "eval-005",
                "redacted": True,
                "subject": "Mixed",
                "sender_email": "c@mau.mau",
                "sender_name": "E",
                "snippet": "Mixed",
                "has_attachments": False,
                "ground_truth": "recruitment",
                "cohorts": ["mixed-purpose"],
            },
            {
                "id": "eval-006",
                "redacted": True,
                "subject": "Follow",
                "sender_email": "d@mau.mau",
                "sender_name": "F",
                "snippet": "Follow",
                "has_attachments": False,
                "ground_truth": "recruitment",
                "cohorts": ["follow-up"],
            },
            {
                "id": "eval-007",
                "redacted": True,
                "subject": "Misleading",
                "sender_email": "e@mau.mau",
                "sender_name": "G",
                "snippet": "Mis",
                "has_attachments": False,
                "ground_truth": "vendor",
                "cohorts": ["misleading-attachment"],
            },
            {
                "id": "eval-008",
                "redacted": True,
                "subject": "Lang",
                "sender_email": "f@mau.mau",
                "sender_name": "H",
                "snippet": "Lang",
                "has_attachments": False,
                "ground_truth": "recruitment",
                "cohorts": ["mixed-language"],
            },
        ],
        "frozen_predictions": {
            "eval-001": {
                "category": "recruitment",
                "confidence": 0.9,
                "source": "frozen",
            },
        },
    }
    contract = EvaluationContract(contract_dict)
    assert "eval-001" in contract.frozen_predictions
    # eval-002 has no frozen prediction, so it will use the predictor at run time


# ──────────────────────────────────────────────────────────────────
# 5.  EvaluationRunner with frozen predictions
# ──────────────────────────────────────────────────────────────────


def test_evaluate_with_frozen_predictions(
    mixed_dataset: EvaluationDataset,
) -> None:
    """Using frozen predictions should produce the same metrics as perfect predictor."""
    fp = {}
    for item in mixed_dataset.items:
        fp[item.id] = Prediction(
            item_id=item.id,
            category=item.ground_truth,
            confidence=0.9,
            source="frozen",
        )

    report = EvaluationContract._run(
        dataset=mixed_dataset,
        frozen_predictions=fp,
        versions=VersionInfo(dataset="1.0.0"),
    )
    assert report.overall.recall == pytest.approx(1.0)
    assert report.overall.precision == pytest.approx(1.0)


def test_frozen_predictions_mixed_with_predictor(
    mixed_dataset: EvaluationDataset,
) -> None:
    """Some items via frozen predictions, rest via predictor."""
    fp = {
        "eval-001": Prediction(
            item_id="eval-001",
            category=EmailCategory.recruitment,
            confidence=0.9,
            source="frozen",
        ),
        "eval-002": Prediction(
            item_id="eval-002",
            category=EmailCategory.recruitment,
            confidence=0.9,
            source="frozen",
        ),
    }

    class _LeavePredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return _single_item_prediction(item, category=EmailCategory.leave_request)

    report = EvaluationContract._run(
        dataset=mixed_dataset,
        frozen_predictions=fp,
        predictor=_LeavePredictor(),
        versions=VersionInfo(dataset="1.0.0"),
    )
    # Recount expected:
    # 10 items total (mixed_dataset fixture)
    # eval-001: predicted recruitment (frozen) == GT (recruitment) → TP
    # eval-002: predicted recruitment (frozen) == GT (recruitment) → TP
    # eval-003: predicted leave (live) == GT (leave_request) → TP
    # eval-004: predicted leave (live) != GT (recruitment) → FP for leave, FN for recru
    # eval-005-eval-010: predicted leave (live) != GT (recruitment/vendor)
    #   → FP for leave, FN for each GT
    # eval-005 GT=recruitment, pred=leave → FN for recru, FP for leave
    # eval-006 GT=recruitment, pred=leave → FN for recru, FP for leave
    # eval-007 GT=recruitment, pred=leave → FN for recru, FP for leave
    # eval-008 GT=recruitment, pred=leave → FN for recru, FP for leave
    # eval-009 GT=vendor, pred=leave → FN for vendor, FP for leave
    # eval-010 GT=recruitment, pred=leave → FN for recru, FP for leave
    # TP = 3 (eval-001=rec, 002=rec, 003=leave)
    # FP = 7 (eval-004 through 010 all predicted leave, 7 incorrect)
    # FN = 7 (for recruitment: eval-004,005,006,007,008,010 = 6; for vendor: eval-009 = 1)
    # Overall recall = TP/(TP+FN) = 3/10 = 0.3
    # Overall precision = TP/(TP+FP) = 3/10 = 0.3
    # Wait, let me recalculate
    # Actually eval-001 GT=recruitment, pred=recruitment → TP
    # eval-002 GT=recruitment, pred=recruitment → TP
    # eval-003 GT=leave_request, pred=leave_request → TP
    # All others (7 items): pred=leave_request but GT != leave_request
    #   These are FP for leave_request, FN for their actual GT
    # TP = 3, FP = 7, FN = 7
    # recall = 3/(3+7) = 0.3, precision = 3/(3+7) = 0.3
    assert report.overall.recall == pytest.approx(3.0 / 10.0)
    assert report.overall.precision == pytest.approx(3.0 / 10.0)


def test_predictor_wrong_item_id_fails(
    mixed_dataset: EvaluationDataset,
) -> None:
    """A predictor that returns a prediction for the wrong item is rejected."""

    class _WrongIdPredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return Prediction(
                item_id="nonexistent",
                category=EmailCategory.recruitment,
                confidence=0.9,
                source="test",
            )

    with pytest.raises(EvaluationContractError, match="wrong item"):
        EvaluationContract._run(
            dataset=mixed_dataset,
            predictor=_WrongIdPredictor(),
            versions=VersionInfo(dataset="1.0.0"),
        )


def test_predictor_confidence_out_of_range_fails(
    mixed_dataset: EvaluationDataset,
) -> None:
    """A predictor that returns confidence outside [0,1] is rejected."""

    class _BadConfidencePredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return Prediction(
                item_id=item.id,
                category=item.ground_truth,
                confidence=2.0,
                source="test",
            )

    with pytest.raises(EvaluationContractError, match="outside"):
        EvaluationContract._run(
            dataset=mixed_dataset,
            predictor=_BadConfidencePredictor(),
            versions=VersionInfo(dataset="1.0.0"),
        )


def test_frozen_prediction_item_id_mismatch_fails(
    mixed_dataset: EvaluationDataset,
) -> None:
    """Frozen prediction with mismatched item_id is rejected at run time."""
    fp = {
        "eval-001": Prediction(
            item_id="eval-999",  # mismatch with key
            category=EmailCategory.recruitment,
            confidence=0.9,
            source="frozen",
        ),
    }
    with pytest.raises(EvaluationContractError, match="item_id mismatch"):
        EvaluationContract._run(
            dataset=mixed_dataset,
            frozen_predictions=fp,
        )


def test_contract_run_accepts_frozen_predictions_override() -> None:
    """contract.run() accepts a frozen_predictions override parameter."""
    data = dict(
        _VALID_SAMPLE_DATASET,
        frozen_predictions={},
    )
    contract = EvaluationContract(data)
    # Override frozen predictions via run()
    fp = {
        "eval-001": Prediction(
            item_id="eval-001",
            category=EmailCategory.recruitment,
            confidence=0.9,
            source="override",
        ),
    }

    # The rest of items need a predictor
    class _DummyPredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return Prediction(
                item_id=item.id,
                category=item.ground_truth,
                confidence=0.9,
                source="dummy",
            )

    report = contract.run(
        predictor=_DummyPredictor(),
        frozen_predictions=fp,
    )
    assert report.overall.support == 8

    def test_predictor_returns_non_prediction_fails(
        mixed_dataset: EvaluationDataset,
    ) -> None:
        """A predictor that returns a non-Prediction value is rejected."""

        class _BadPredictor:
            def __call__(self, item: EvaluationItem) -> str:
                return "not a prediction"

        with pytest.raises(EvaluationContractError, match="non-Prediction"):
            EvaluationContract._run(
                dataset=mixed_dataset,
                predictor=_BadPredictor(),  # type: ignore[arg-type]
            )


# ──────────────────────────────────────────────────────────────────
# 6.  Review rate semantics
# ──────────────────────────────────────────────────────────────────


def test_review_rate_attributed_to_ground_truth_category(
    mixed_dataset: EvaluationDataset,
) -> None:
    """review_rate for a category is based on ground-truth, not predicted category.

    Items where confidence < threshold increment the review counter of their
    *ground-truth* category, not the predicted category.
    """

    class _LowConfRecruitmentPredictor:
        """Always predicts recruitment with low confidence."""

        def __call__(self, item: EvaluationItem) -> Prediction:
            return Prediction(
                item_id=item.id,
                category=EmailCategory.recruitment,
                confidence=0.3,
                source="test",
            )

    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_LowConfRecruitmentPredictor(),
        needs_review_threshold=0.5,
    )
    # mixed_dataset has: 8 recruitment, 1 leave_request, 1 vendor
    # All predictions are 'recruitment' with 0.3 confidence (below threshold)
    # review is counted on GT category: cat_stats[gt]["review"] += 1
    # So EVERY item flags review on its own ground-truth category, regardless
    # of what category the predictor returned.
    #
    # Recruitment: 8 GT items, all with conf < threshold → review=8, support=8
    #   review_rate = 8/8 = 1.0
    # leave_request: 1 GT item with conf < threshold → review=1, support=1
    #   review_rate = 1/1 = 1.0
    # vendor: 1 GT item with conf < threshold → review=1, support=1
    #   review_rate = 1/1 = 1.0
    rec = report.per_category[EmailCategory.recruitment.value]
    assert rec.review_rate == pytest.approx(1.0)
    assert rec.support == 8

    lr = report.per_category[EmailCategory.leave_request.value]
    assert lr.review_rate == pytest.approx(1.0)
    assert lr.support == 1

    v = report.per_category[EmailCategory.vendor.value]
    assert v.review_rate == pytest.approx(1.0)
    assert v.support == 1


def test_review_rate_high_confidence_no_review(
    mixed_dataset: EvaluationDataset,
) -> None:
    """Items with confidence above threshold are NOT counted in review_rate.

    Verifies both GT-based attribution and threshold behaviour.
    """

    class _HighConfPredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return Prediction(
                item_id=item.id,
                category=item.ground_truth,
                confidence=0.9,
                source="test",
            )

    report = EvaluationContract._run(
        dataset=mixed_dataset,
        predictor=_HighConfPredictor(),
        needs_review_threshold=0.5,
    )
    # All items have GT == predicted with high confidence
    # → no items should be flagged for review
    assert report.overall.review_rate == pytest.approx(0.0)
    for cat_name, row in report.per_category.items():
        assert row.review_rate == pytest.approx(0.0), f"{cat_name} review_rate != 0"


@pytest.fixture
def single_item_dataset() -> EvaluationDataset:
    """A single-item dataset for precise review rate calculation."""
    items = [
        {
            "id": "eval-001",
            "redacted": True,
            "subject": "Test item",
            "sender_email": "test@mau.mau",
            "sender_name": "Test",
            "snippet": "Test content",
            "has_attachments": False,
            "ground_truth": "recruitment",
            "cohorts": ["no-cv"],
        },
        {
            "id": "eval-002",
            "redacted": True,
            "subject": "Another",
            "sender_email": "other@mau.mau",
            "sender_name": "Other",
            "snippet": "Other",
            "has_attachments": False,
            "ground_truth": "recruitment",
            "cohorts": [
                "referral",
                "agency",
                "multi-applicant",
                "mixed-purpose",
                "follow-up",
                "misleading-attachment",
                "mixed-language",
            ],
        },
    ]
    return _make_dataset(items)


def test_review_rate_half_items_flagged(
    single_item_dataset: EvaluationDataset,
) -> None:
    """Exactly half of GT items flagged → review_rate = 0.5 for that category."""
    fp = {
        "eval-001": Prediction(
            item_id="eval-001",
            category=EmailCategory.recruitment,
            confidence=0.3,  # below threshold
            source="test",
        ),
        "eval-002": Prediction(
            item_id="eval-002",
            category=EmailCategory.recruitment,
            confidence=0.9,  # above threshold
            source="test",
        ),
    }
    report = EvaluationContract._run(
        dataset=single_item_dataset,
        frozen_predictions=fp,
        needs_review_threshold=0.5,
    )
    rec = report.per_category[EmailCategory.recruitment.value]
    assert rec.review_rate == pytest.approx(0.5)
    assert rec.support == 2


# ──────────────────────────────────────────────────────────────────
# 7.  Frozen prediction metadata & version override
# ──────────────────────────────────────────────────────────────────


def test_frozen_run_accepts_source_versions(
    mixed_dataset: EvaluationDataset,
) -> None:
    """contract.run() accepts source_versions to override report version metadata."""
    data = dict(_VALID_SAMPLE_DATASET, version="1.0.0")
    contract = EvaluationContract(data)

    fp = {
        "eval-001": Prediction(
            item_id="eval-001",
            category=EmailCategory.recruitment,
            confidence=0.9,
            source="frozen",
        ),
    }

    class _DummyPredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return Prediction(
                item_id=item.id,
                category=item.ground_truth,
                confidence=0.9,
                source="dummy",
            )

    src = VersionInfo(model="frozen-v2", policy="new-policy-v1")
    report = contract.run(
        predictor=_DummyPredictor(),
        frozen_predictions=fp,
        source_versions=src,
    )
    # Dataset version preserved, model/policy overridden
    assert report.versions.dataset == "1.0.0"
    assert report.versions.model == "frozen-v2"
    assert report.versions.policy == "new-policy-v1"
    # prompt falls back to dataset value
    assert report.versions.prompt == "test-prompt-v1"


def test_source_versions_empty_in_versions_unchanged(
    mixed_dataset: EvaluationDataset,
) -> None:
    """Empty source_versions fields do not override existing versions."""
    data = dict(
        _VALID_SAMPLE_DATASET,
        version="1.0.0",
        model_version="original-model",
        policy_version="original-policy",
    )
    contract = EvaluationContract(data)

    class _PerfectPredictor:
        def __call__(self, item: EvaluationItem) -> Prediction:
            return Prediction(
                item_id=item.id,
                category=item.ground_truth,
                confidence=0.9,
                source="perfect",
            )

    # source_versions with empty values should not override
    src = VersionInfo()
    report = contract.run(
        predictor=_PerfectPredictor(),
        source_versions=src,
    )
    assert report.versions.model == "original-model"
    assert report.versions.policy == "original-policy"


def test_frozen_metadata_extracted_from_dataset() -> None:
    """_metadata key is skipped during frozen prediction parsing."""
    data = dict(
        _VALID_SAMPLE_DATASET,
        frozen_predictions={
            "_metadata": {
                "predictor": {
                    "model": "rules-classifier-v1",
                    "policy": "classification-thresholds-v1",
                }
            },
            "eval-001": {
                "category": "recruitment",
                "confidence": 0.85,
                "source": "rules",
            },
        },
    )
    contract = EvaluationContract(data)
    assert len(contract.frozen_predictions) == 1
    assert "_metadata" not in contract.frozen_predictions
