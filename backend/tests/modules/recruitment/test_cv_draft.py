"""Tests for the CV draft safety contract."""

from src.modules.recruitment.application.cv_draft import assess_cv_draft, merge_confirmed_fields
from src.modules.recruitment.domain.value_objects import EducationItem, ExperienceItem, ParsedCV


def _cv(**overrides) -> ParsedCV:
    values = {
        "name": "Nguyen Van A",
        "email": "a@example.com",
        "phone": "0901234567",
        "skills": ["Python"],
        "summary": "Developer",
    }
    values.update(overrides)
    return ParsedCV(**values)


def test_provenance_points_to_source_and_missing_fields_are_flagged() -> None:
    draft = assess_cv_draft(_cv(), "Nguyen Van A a@example.com 0901234567 Python Developer")

    assert draft.provenance["name"].status == "extracted"
    assert draft.provenance["email"].source_fragment == "a@example.com"
    assert draft.provenance["education"].status == "missing"


def test_structured_items_use_text_evidence() -> None:
    draft = assess_cv_draft(
        _cv(
            experience=[ExperienceItem(company="Acme", title="Engineer")],
            education=[EducationItem(institution="HUST")],
        ),
        "Nguyen Van A a@example.com Acme Engineer HUST",
    )

    assert draft.provenance["experience[0]"].status == "extracted"
    assert draft.provenance["education[0]"].status == "extracted"


def test_critical_value_not_in_source_is_hallucination() -> None:
    draft = assess_cv_draft(_cv(email="invented@example.com"), "Nguyen Van A b@example.com Python")

    assert draft.provenance["email"].status == "conflict"
    assert any(error.code == "critical_field_hallucination" for error in draft.validation_errors)
    assert any(error.code == "conflicting_email" for error in draft.validation_errors)


def test_confirmed_values_survive_reparse() -> None:
    previous = _cv(name="HR Confirmed Name").model_dump()
    reparsed = merge_confirmed_fields(_cv(name="AI Replacement"), previous, ["name"])

    assert reparsed.name == "HR Confirmed Name"
    assert "name" in reparsed.confirmed_fields
    reparsed = assess_cv_draft(reparsed, "AI Replacement invented@example.com")
    assert reparsed.provenance["name"].status == "confirmed"
