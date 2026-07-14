"""Deterministic safety checks for AI CV drafts.

The LLM proposes values; this module supplies verifiable evidence and keeps
critical values that cannot be found in the source out of the accepted path.
"""

from __future__ import annotations

import re
from typing import Any

from src.modules.recruitment.domain.value_objects import (
    CVFieldValidation,
    FieldProvenance,
    ParsedCV,
)

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d .()-]{7,}\d)")


def assess_cv_draft(parsed_cv: ParsedCV, source_text: str) -> ParsedCV:
    """Attach provenance and field-level validation to an AI proposal.

    Matching is intentionally conservative: a value is only marked
    ``extracted`` when its literal text occurs in the OCR source. Name and
    email are critical fields, so an absent non-empty value is explicitly
    marked ``hallucinated`` and the draft requires HR confirmation.
    """
    source = source_text.casefold()
    confirmed = set(parsed_cv.confirmed_fields)
    provenance: dict[str, FieldProvenance] = {}
    findings: list[CVFieldValidation] = []

    def scalar(field: str, value: str, *, critical: bool = False) -> None:
        value = value.strip()
        if not value:
            provenance[field] = FieldProvenance(status="missing")
            if critical:
                findings.append(
                    CVFieldValidation(
                        field=field,
                        code="missing_critical_field",
                        message=f"Critical field '{field}' is missing",
                        severity="error",
                    )
                )
            return
        if value.casefold() in source:
            provenance[field] = FieldProvenance(
                source_fragment=value, status="extracted", needs_confirmation=True
            )
        else:
            provenance[field] = FieldProvenance(status="hallucinated")
            findings.append(
                CVFieldValidation(
                    field=field,
                    code="critical_field_hallucination" if critical else "value_not_in_source",
                    message=f"Value for '{field}' was not found in the source fragment",
                    severity="error" if critical else "warning",
                )
            )

    scalar("name", parsed_cv.name, critical=True)
    scalar("email", parsed_cv.email, critical=True)
    scalar("phone", parsed_cv.phone)
    scalar("summary", parsed_cv.summary)

    for field, values in (
        ("skills", parsed_cv.skills),
        ("experience", parsed_cv.experience),
        ("education", parsed_cv.education),
    ):
        if not values:
            provenance[field] = FieldProvenance(status="missing")
        for index, value in enumerate(values):
            key = f"{field}[{index}]"
            if isinstance(value, str):
                scalar(key, value)
                continue
            parts = [part for part in value.model_dump().values() if isinstance(part, str) and part]
            evidence = next((part for part in parts if part.casefold() in source), "")
            if evidence:
                provenance[key] = FieldProvenance(
                    source_fragment=evidence,
                    status="extracted",
                    needs_confirmation=True,
                )
            else:
                provenance[key] = FieldProvenance(status="hallucinated")
                findings.append(
                    CVFieldValidation(
                        field=key,
                        code="value_not_in_source",
                        message=f"Value for '{key}' was not found in the source fragment",
                    )
                )

    # A source containing a different contact value is a conflict, not proof
    # that the model chose the right one.
    source_emails = {m.casefold() for m in _EMAIL_RE.findall(source_text)}
    if parsed_cv.email and source_emails and parsed_cv.email.casefold() not in source_emails:
        findings.append(
            CVFieldValidation(
                field="email",
                code="conflicting_email",
                message="The source contains a different email address",
                severity="error",
            )
        )
        provenance["email"] = provenance["email"].model_copy(
            update={"status": "conflict", "needs_confirmation": True}
        )

    source_phones = set(_PHONE_RE.findall(source_text))
    if parsed_cv.phone and source_phones and parsed_cv.phone not in source_phones:
        findings.append(
            CVFieldValidation(
                field="phone",
                code="conflicting_phone",
                message="The source contains a different phone number",
                severity="warning",
            )
        )
        provenance["phone"] = provenance["phone"].model_copy(
            update={"status": "conflict", "needs_confirmation": True}
        )

    for field in confirmed:
        if field in provenance:
            provenance[field] = provenance[field].model_copy(
                update={"status": "confirmed", "needs_confirmation": False}
            )
    findings = [item for item in findings if item.field not in confirmed]
    return parsed_cv.model_copy(update={"provenance": provenance, "validation_errors": findings})


def merge_confirmed_fields(
    parsed_cv: ParsedCV,
    previous_data: dict[str, Any] | None,
    confirmed_fields: list[str] | set[str] | None,
) -> ParsedCV:
    """Keep HR-confirmed values when a later AI parse produces a new draft."""
    confirmed = set(confirmed_fields or ())
    if not previous_data or not confirmed:
        return parsed_cv
    current = parsed_cv.model_dump()
    previous = ParsedCV.model_validate(previous_data).model_dump()
    for field in confirmed:
        if field in previous and field in current:
            current[field] = previous[field]
    current["confirmed_fields"] = confirmed
    if "provenance" in current:
        for field in confirmed:
            if field in current["provenance"]:
                current["provenance"][field] = FieldProvenance(
                    source_fragment=current["provenance"][field].get("source_fragment", ""),
                    status="confirmed",
                    needs_confirmation=False,
                ).model_dump()
    return ParsedCV.model_validate(current)
