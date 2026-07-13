"""Contract tests for the expanded Job Application boundary (GH #201)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.recruitment.application.job_application_service import JobApplicationService
from src.modules.recruitment.domain.entities import JobApplication
from src.modules.recruitment.infrastructure.repositories import JobApplicationRepository


@pytest.mark.asyncio
async def test_intent_source_and_cv_presence_are_independent() -> None:
    repo = MagicMock(spec=JobApplicationRepository)
    repo.get_by_gmail_message_id = AsyncMock(return_value=None)
    repo.list_by_gmail_thread_id = AsyncMock(return_value=[])
    repo.create = AsyncMock(side_effect=lambda application: application)
    service = JobApplicationService(session=AsyncMock(), job_application_repo=repo)

    email = MagicMock(
        id=uuid4(),
        gmail_message_id="msg-referral-no-cv",
        gmail_thread_id="thread-referral-no-cv",
        sender_name="HR colleague",
        sender_email="hr@example.com",
        has_attachments=False,
    )
    result = ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.99,
        application_source="employee_referral",
        has_cv=False,
        source_hints=(("applicant_name", "Nguyen Van B"),),
    )

    application = await service.create_from_classification(email, result)

    assert isinstance(application, JobApplication)
    assert application.intent == "job_application"
    assert application.source == "employee_referral"
    assert application.has_cv is False
    assert application.applicant_name == "Nguyen Van B"
    assert application.applicant_email is None
    repo.create.assert_awaited_once()


def test_legacy_recruitment_category_reads_as_job_application() -> None:
    result = ClassificationResult(category=EmailCategory.recruitment, confidence=0.8)

    assert result.category == EmailCategory.recruitment
    assert result.intent == "job_application"
    assert result.is_job_application is True
