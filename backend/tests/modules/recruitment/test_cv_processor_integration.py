"""Integration tests for CV Processor pipeline.

Tests:
1. High confidence CV -> Candidate created, status = completed
2. Low confidence CV -> no Candidate, status = needs_review
3. Multiple attachments -> CVDocument per attachment

**Validates: auto-CV path routes correctly**
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.recruitment.application.cv_processor import (
    AttachmentInput,
    CVProcessorService,
)
from src.modules.recruitment.domain.enums import ProcessingStatus
from src.modules.recruitment.domain.value_objects import ParsedCV
from src.modules.recruitment.infrastructure.llm_adapter import ParsedCVResult


def _make_attachment_input(
    filename: str = "cv.pdf",
    mime_type: str = "application/pdf",
    size_bytes: int = 1024,
    data: bytes = b"PDF content bytes here for testing",
) -> AttachmentInput:
    return AttachmentInput(
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        data=data,
    )


def _build_processor(
    mock_session,
    recruitment_settings,
    mock_candidate_creator,
    ocr_text: str = "Nguyen Van A Python Developer 5 years experience in software engineering",
    parsed_cv: ParsedCV | None = None,
):
    """Build a CVProcessorService with mocked dependencies."""
    if parsed_cv is None:
        parsed_cv = ParsedCV(
            name="Nguyen Van A",
            email="a@example.com",
            phone="0901234567",
            skills=["Python"],
            experience=[],
            education=[],
            summary="Developer",
        )

    mock_minio = AsyncMock()
    mock_minio.upload_cv = AsyncMock(return_value="bucket/cv.pdf")

    mock_ocr = AsyncMock()
    mock_ocr.extract_text = AsyncMock(return_value=ocr_text)

    mock_llm = AsyncMock()
    mock_llm.parse_cv = AsyncMock(
        return_value=ParsedCVResult(parsed_cv=parsed_cv, token_usage={})
    )

    mock_pii = MagicMock()
    mock_pii.redact = MagicMock(return_value="[redacted] " + ocr_text[:50])

    mock_candidate_repo = AsyncMock()
    mock_cv_doc_repo = AsyncMock()
    mock_cv_doc_repo.create = AsyncMock(side_effect=lambda doc: doc)
    mock_cv_doc_repo.update = AsyncMock(side_effect=lambda doc: doc)

    processor = CVProcessorService(
        minio_client=mock_minio,
        ocr_adapter=mock_ocr,
        llm_adapter=mock_llm,
        pii_redactor=mock_pii,
        candidate_repo=mock_candidate_repo,
        cv_document_repo=mock_cv_doc_repo,
        settings=recruitment_settings,
        session=mock_session,
        candidate_creator=mock_candidate_creator,
    )

    return processor, mock_cv_doc_repo


@pytest.fixture(autouse=True)
def mock_log_audit():
    with patch(
        "src.modules.recruitment.application.cv_processor.log_audit",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def recruitment_settings():
    from src.modules.recruitment.infrastructure.config import RecruitmentSettings
    return RecruitmentSettings()


@pytest.fixture
def mock_candidate_creator():
    creator = AsyncMock()
    creator.create_or_update_candidate = AsyncMock(
        return_value=MagicMock(id=uuid4(), name="Nguyen Van A")
    )
    return creator


class TestHighConfidenceCreatesCandidate:
    """High confidence CV (>= 0.7) should create Candidate and set status=completed."""

    async def test_high_confidence_creates_candidate(
        self,
        mock_session,
        recruitment_settings,
        mock_candidate_creator,
    ) -> None:
        # name(0.25) + email(0.25) + phone(0.10) + skills(0.10) + summary(0.05) = 0.75
        # 0.75 >= 0.7 threshold -> COMPLETED + Candidate
        parsed_cv = ParsedCV(
            name="Nguyen Van A",
            email="a@example.com",
            phone="0901234567",
            skills=["Python"],
            experience=[],
            education=[],
            summary="Developer",
        )
        processor, _ = _build_processor(
            mock_session, recruitment_settings, mock_candidate_creator,
            parsed_cv=parsed_cv,
        )

        cv_doc = await processor.process_single_attachment(
            email_message_id=uuid4(),
            attachment=_make_attachment_input(),
            gmail_message_id="msg_high_conf",
        )

        assert cv_doc.processing_status == ProcessingStatus.COMPLETED
        assert mock_candidate_creator.create_or_update_candidate.called


class TestLowConfidenceRoutesToReview:
    """Low confidence CV (< 0.7) should NOT create Candidate, status=needs_review."""

    async def test_low_confidence_sets_needs_review(
        self,
        mock_session,
        recruitment_settings,
        mock_candidate_creator,
    ) -> None:
        # name(0.25) + email(0.25) = 0.50
        # 0.50 < 0.7 threshold -> NEEDS_REVIEW, no Candidate
        parsed_cv = ParsedCV(
            name="Unknown",
            email="unknown@example.com",
            phone="",
            skills=[],
            experience=[],
            education=[],
            summary="",
        )
        processor, _ = _build_processor(
            mock_session, recruitment_settings, mock_candidate_creator,
            parsed_cv=parsed_cv,
        )

        cv_doc = await processor.process_single_attachment(
            email_message_id=uuid4(),
            attachment=_make_attachment_input(),
            gmail_message_id="msg_low_conf",
        )

        assert cv_doc.processing_status == ProcessingStatus.NEEDS_REVIEW
        assert not mock_candidate_creator.create_or_update_candidate.called


class TestCVProcessorCreatesDocuments:
    """CV processor should create CVDocument records for each attachment."""

    async def test_creates_cv_document_per_attachment(
        self,
        mock_session,
        recruitment_settings,
        mock_candidate_creator,
    ) -> None:
        processor, mock_cv_doc_repo = _build_processor(
            mock_session, recruitment_settings, mock_candidate_creator,
        )

        cv_doc = await processor.process_single_attachment(
            email_message_id=uuid4(),
            attachment=_make_attachment_input(),
            gmail_message_id="msg_doc_create",
        )

        assert cv_doc is not None
        assert mock_cv_doc_repo.create.called

    async def test_process_cv_from_email_handles_multiple_attachments(
        self,
        mock_session,
        recruitment_settings,
        mock_candidate_creator,
    ) -> None:
        processor, _ = _build_processor(
            mock_session, recruitment_settings, mock_candidate_creator,
        )

        attachments = [
            _make_attachment_input(filename="cv1.pdf"),
            _make_attachment_input(filename="cv2.pdf"),
        ]

        cv_documents = await processor.process_cv_from_email(
            email_message_id=uuid4(),
            attachments=attachments,
            gmail_message_id="msg_multi",
        )

        assert len(cv_documents) == 2
