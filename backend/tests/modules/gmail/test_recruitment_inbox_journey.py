"""Journey tests for Recruitment Inbox (GH #184).

Tests the end-to-end flow of uncertain emails being routed to the
Recruitment Inbox, HR correcting/dismissing items, and the inbox
filtering behaviour — all through the ClassificationService public
seam and the inbox API boundary.

Coverage:
1. Uncertain email → inbox item creation (existing)
2. Silent callback failure → needs_review, not needs_classification
3. Exhausted provider retry → inbox item via _classify_single
4. Dismissed retry suppression → existing item returned without mutation
5. Filter state reachability → each InboxStatus filter returns real items
6. Attachment metadata propagation
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.gmail.application.classification_service import ClassificationService
from src.modules.gmail.domain.enums import EmailCategory
from src.modules.gmail.infrastructure.ai_classifier import ClassificationResult
from src.modules.gmail.infrastructure.config import GmailSettings
from src.modules.recruitment.application.inbox_service import InboxService
from src.modules.recruitment.domain.entities import RecruitmentInboxItem
from src.modules.recruitment.domain.enums import InboxStatus
from src.modules.recruitment.infrastructure.repositories import (
    RecruitmentInboxItemRepository,
)


def _make_mock_email(
    email_id: str | None = None,
    thread_id: str | None = None,
    sender_email: str = "candidate@example.com",
    sender_name: str = "Nguyen Van A",
    has_attachments: bool = False,
    subject: str = "Ung tuyen Python Developer",
    snippet: str = "Toi muon ung tuyen vi tri Python Developer",
    retry_count: int = 0,
    is_permanently_failed: bool = False,
) -> MagicMock:
    """Create a mock EmailMessage with realistic attributes."""
    email = MagicMock()
    email.id = uuid4()
    email.gmail_message_id = email_id or f"msg_{uuid4().hex[:12]}"
    email.gmail_thread_id = thread_id or f"thread_{uuid4().hex[:12]}"
    email.subject = subject
    email.sender_email = sender_email
    email.sender_name = sender_name
    email.snippet = snippet
    email.has_attachments = has_attachments
    email.attachments = []
    email.processing_status = "unprocessed"
    email.category = None
    email.user_id = uuid4()
    email.retry_count = retry_count
    email.is_permanently_failed = is_permanently_failed
    email.processing_error = None
    return email


def _make_low_confidence_recruitment_result() -> ClassificationResult:
    """Low confidence recruitment classification (below threshold)."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.40,
        source="ai",
        matched_signals=["subject:ung tuyen", "sender_domain:example.com"],
        source_hints=(("sender_role", "candidate"),),
    )


def _make_low_confidence_vendor_result() -> ClassificationResult:
    """Low confidence vendor classification (below threshold, non-recruitment)."""
    return ClassificationResult(
        category=EmailCategory.vendor,
        confidence=0.40,
        source="ai",
        matched_signals=["subject:bao gia"],
    )


def _make_high_confidence_recruitment_result() -> ClassificationResult:
    """High confidence recruitment classification (above threshold)."""
    return ClassificationResult(
        category=EmailCategory.recruitment,
        confidence=0.90,
        source="ai",
        matched_signals=["subject:ung tuyen", "sender_domain:example.com"],
    )


@pytest.fixture
def settings() -> GmailSettings:
    """GmailSettings with standard thresholds."""
    return GmailSettings(
        classification_batch_concurrency=3,
        classification_confidence_threshold=0.75,
        classification_needs_review_threshold=0.5,
    )


@pytest.fixture
def session() -> AsyncMock:
    """Mocked AsyncSession."""
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.flush = AsyncMock()
    return mock


@pytest.fixture
def audit_logger() -> AsyncMock:
    """Mocked AuditLogger."""
    mock = AsyncMock()
    mock.log_operation = AsyncMock()
    return mock


@pytest.fixture
def email_repo() -> AsyncMock:
    """Mocked EmailRepository."""
    mock = AsyncMock()
    mock.session = MagicMock()
    mock.session.execute = AsyncMock()
    return mock


# ---------------------------------------------------------------------------
# Test: Uncertain Email Routing
# ---------------------------------------------------------------------------


class TestUncertainEmailRouting:
    """Tests for routing uncertain emails to Recruitment Inbox."""

    async def test_low_confidence_recruitment_creates_inbox_item(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Low confidence recruitment email creates a RecruitmentInboxItem
        and sets processing_status to needs_classification."""
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        inbox_repo.create = AsyncMock()
        inbox_repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=None)

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=_make_low_confidence_recruitment_result()
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email()
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "needs_classification"
        assert email.category == "recruitment"

    async def test_low_confidence_non_recruitment_does_not_create_inbox_item(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Low confidence non-recruitment email goes to needs_review,
        not to the Recruitment Inbox."""
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.create = AsyncMock()

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_vendor_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=_make_low_confidence_vendor_result()
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email("msg_vendor_low")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "needs_review"
        assert email.category == "vendor"
        inbox_repo.create.assert_not_awaited()

    async def test_high_confidence_recruitment_creates_application_not_inbox(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """High confidence recruitment creates a JobApplication
        (via on_application_created), not an inbox item."""
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.create = AsyncMock()

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        job_app_repo = MagicMock()
        job_app_repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        job_app_repo.list_by_gmail_thread_id = AsyncMock(return_value=[])
        job_app_repo.create = AsyncMock()

        from src.modules.recruitment.application.job_application_service import (
            JobApplicationService,
        )

        job_app_service = JobApplicationService(
            session=session,
            job_application_repo=job_app_repo,
        )

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_high_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=_make_high_confidence_recruitment_result()
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_app_service.create_from_classification,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email("msg_high_conf")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "classified"

        job_app_repo.create.assert_awaited_once()
        inbox_repo.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test: Silent callback failure -> needs_review, not needs_classification
# ---------------------------------------------------------------------------


class TestCallbackFailure:
    """When the uncertain classification callback fails, the email should
    be marked needs_review with a processing error, NOT needs_classification."""

    async def test_callback_failure_marks_needs_review(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """If on_uncertain_classification raises, the email is marked
        needs_review with processing_error and the batch counts it as 0."""
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.get_by_gmail_message_id = AsyncMock(side_effect=ValueError("DB error"))
        inbox_repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=None)

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=_make_low_confidence_recruitment_result()
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email("msg_cb_fail")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 0
        assert email.processing_status == "needs_review"
        assert email.processing_error is not None
        assert "RecruitmentInboxItem creation failed" in email.processing_error

    async def test_callback_failure_without_callback_passes_through(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """When no on_uncertain_classification is set, recruitment emails below
        threshold are still marked needs_classification."""
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=_make_low_confidence_recruitment_result()
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=None,
        )

        email = _make_mock_email("msg_no_cb")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        assert email.processing_status == "needs_classification"


# ---------------------------------------------------------------------------
# Test: Exhausted provider retry -> inbox item
# ---------------------------------------------------------------------------


class TestExhaustedRetry:
    """When provider retries are exhausted, an inbox item should be created
    with needs_classification status, preserving null prediction, error,
    and retry metadata."""

    async def test_exhausted_retry_creates_inbox_item(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Exhausted provider retries create inbox item via callback,
        with null/uncategorized prediction, error metadata, and retry state."""
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        inbox_repo.create = AsyncMock()
        inbox_repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=None)

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(side_effect=ConnectionError("Provider down"))

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email("msg_exhausted", retry_count=3)
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 0
        assert email.processing_status == "permanently_failed"
        assert email.is_permanently_failed is True

        inbox_repo.create.assert_awaited_once()
        created_item = inbox_repo.create.await_args[0][0]
        assert isinstance(created_item, RecruitmentInboxItem)
        assert created_item.inbox_status == InboxStatus.NEEDS_CLASSIFICATION
        assert created_item.prediction_intent is not None
        assert created_item.confidence_raw == 0.0
        assert created_item.is_retry_exhausted is True
        assert created_item.retry_count >= 3
        assert created_item.processing_error is not None

    async def test_non_exhausted_retry_does_not_create_inbox_item(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """Non-exhausted provider failure does NOT create an inbox item."""
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.create = AsyncMock()
        inbox_repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=None)

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(side_effect=ConnectionError("Provider down"))

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email("msg_retry1", retry_count=0)
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 0
        assert email.processing_status == "ai_unavailable"
        inbox_repo.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test: Dismissed retry suppression
# ---------------------------------------------------------------------------


class TestDismissedRetrySuppression:
    """When an inbox item already exists in dismissed state for a Gmail message,
    the uncertain callback should return the existing dismissed item without
    mutating or reopening it."""

    async def test_dismissed_item_returned_without_mutation(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """If a dismissed inbox item exists, create_from_classification returns
        it without creating or updating."""
        dismissed_item = RecruitmentInboxItem(
            gmail_message_id="msg_dismissed_already",
            gmail_thread_id="thread_dismissed",
            sender_email="candidate@example.com",
            inbox_status=InboxStatus.RESOLVED,
            dismissed=True,
        )

        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=dismissed_item)
        inbox_repo.create = AsyncMock()
        inbox_repo.get_by_gmail_message_id = AsyncMock(return_value=None)

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=_make_low_confidence_recruitment_result()
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email("msg_dismissed_already")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        inbox_repo.create.assert_not_awaited()
        inbox_repo.update.assert_not_awaited()

    async def test_non_dismissed_existing_item_returned_without_duplicate(
        self,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        """If a non-dismissed inbox item already exists, create_from_classification
        returns it without creating a duplicate."""
        existing_item = RecruitmentInboxItem(
            gmail_message_id="msg_existing",
            gmail_thread_id="thread_existing",
            sender_email="candidate@example.com",
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
        )

        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=None)
        inbox_repo.get_by_gmail_message_id = AsyncMock(return_value=existing_item)
        inbox_repo.create = AsyncMock()

        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)

        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(
            return_value=_make_low_confidence_recruitment_result()
        )
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(
            return_value=_make_low_confidence_recruitment_result()
        )

        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=None,
            on_uncertain_classification=inbox_service.create_from_classification,
        )

        email = _make_mock_email("msg_existing")
        user_id = uuid4()

        classified_count = await service.classify_batch(user_id=user_id, emails=[email])

        assert classified_count == 1
        inbox_repo.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test: Filter state reachability
# ---------------------------------------------------------------------------


class TestFilterStateReachability:
    """Each InboxStatus filter value must be reachable by actual persisted
    items with meaningful semantics."""

    @pytest.fixture
    def inbox_repo(self) -> MagicMock:
        repo = MagicMock(spec=RecruitmentInboxItemRepository)
        repo.get_by_id = AsyncMock()
        repo.get_by_gmail_message_id = AsyncMock()
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.list_by_status = AsyncMock(return_value=([], 0))
        repo.find_dismissed_by_gmail_message_id = AsyncMock()
        return repo

    @pytest.fixture
    def inbox_service(self, session: AsyncMock, inbox_repo: MagicMock) -> InboxService:
        return InboxService(session=session, inbox_repo=inbox_repo)

    async def test_needs_classification_filter(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """needs_classification filter returns items that are below
        policy threshold."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_needs_class",
            gmail_thread_id="thread_needs_class",
            sender_email="candidate@example.com",
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
            prediction_intent="job_application",
            confidence_raw=0.35,
        )
        inbox_repo.list_by_status.return_value = ([item], 1)

        items, total = await inbox_service.list_inbox(
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION
        )

        assert total == 1
        assert items[0].inbox_status == InboxStatus.NEEDS_CLASSIFICATION

    async def test_needs_information_filter(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """needs_information filter returns items needing additional info."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_needs_info",
            gmail_thread_id="thread_needs_info",
            sender_email="unknown@example.com",
            inbox_status=InboxStatus.NEEDS_INFORMATION,
            prediction_intent="job_application",
            corrected_intent="job_application",
            confidence_raw=0.45,
        )
        inbox_repo.list_by_status.return_value = ([item], 1)

        items, total = await inbox_service.list_inbox(
            inbox_status=InboxStatus.NEEDS_INFORMATION
        )

        assert total == 1
        assert items[0].inbox_status == InboxStatus.NEEDS_INFORMATION
        assert items[0].corrected_intent == "job_application"

    async def test_ready_for_review_filter(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """ready_for_review filter returns items where HR corrected
        intent to job_application."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_ready",
            gmail_thread_id="thread_ready",
            sender_email="applicant@example.com",
            inbox_status=InboxStatus.READY_FOR_REVIEW,
            prediction_intent="job_application",
            corrected_intent="job_application",
        )
        inbox_repo.list_by_status.return_value = ([item], 1)

        items, total = await inbox_service.list_inbox(
            inbox_status=InboxStatus.READY_FOR_REVIEW
        )

        assert total == 1
        assert items[0].inbox_status == InboxStatus.READY_FOR_REVIEW

    async def test_resolved_filter(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """resolved filter returns items handled by HR."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_resolved",
            gmail_thread_id="thread_resolved",
            sender_email="vendor@example.com",
            inbox_status=InboxStatus.RESOLVED,
            corrected_intent="partner",
            dismissed=False,
        )
        inbox_repo.list_by_status.return_value = ([item], 1)

        items, total = await inbox_service.list_inbox(
            inbox_status=InboxStatus.RESOLVED
        )

        assert total == 1
        assert items[0].inbox_status == InboxStatus.RESOLVED

    async def test_all_four_filters_return_persisted_items(
        self,
    ) -> None:
        """All four InboxStatus values return real items."""
        repo = MagicMock(spec=RecruitmentInboxItemRepository)

        items_by_status = {
            InboxStatus.NEEDS_CLASSIFICATION: RecruitmentInboxItem(
                gmail_message_id="msg_a", gmail_thread_id="t_a",
                sender_email="a@example.com",
                inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
            ),
            InboxStatus.NEEDS_INFORMATION: RecruitmentInboxItem(
                gmail_message_id="msg_b", gmail_thread_id="t_b",
                sender_email="b@example.com",
                inbox_status=InboxStatus.NEEDS_INFORMATION,
            ),
            InboxStatus.READY_FOR_REVIEW: RecruitmentInboxItem(
                gmail_message_id="msg_c", gmail_thread_id="t_c",
                sender_email="c@example.com",
                inbox_status=InboxStatus.READY_FOR_REVIEW,
            ),
            InboxStatus.RESOLVED: RecruitmentInboxItem(
                gmail_message_id="msg_d", gmail_thread_id="t_d",
                sender_email="d@example.com",
                inbox_status=InboxStatus.RESOLVED,
            ),
        }

        for status, item in items_by_status.items():
            repo.list_by_status = AsyncMock(return_value=([item], 1))
            service = InboxService(session=AsyncMock(), inbox_repo=repo)
            items, total = await service.list_inbox(inbox_status=status)
            assert total == 1
            assert items[0].inbox_status == status


# ---------------------------------------------------------------------------
# Test: InboxService business logic
# ---------------------------------------------------------------------------


class AsyncMockWithResult(AsyncMock):
    """AsyncMock that returns a specific value by default."""

    def __init__(self, return_value=None, **kwargs):
        super().__init__(**kwargs)
        self._return_value = return_value

    async def __call__(self, *args, **kwargs):
        if self.side_effect:
            return await super().__call__(*args, **kwargs)
        return self._return_value


class TestInboxService:
    """Tests for the InboxService business logic."""

    @pytest.fixture
    def inbox_repo(self) -> MagicMock:
        repo = MagicMock(spec=RecruitmentInboxItemRepository)
        repo.get_by_id = AsyncMock()
        repo.get_by_gmail_message_id = AsyncMock()
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.list_by_status = AsyncMock(return_value=([], 0))
        repo.find_dismissed_by_gmail_message_id = AsyncMock()
        return repo

    @pytest.fixture
    def inbox_service(self, session: AsyncMock, inbox_repo: MagicMock) -> InboxService:
        return InboxService(session=session, inbox_repo=inbox_repo)

    async def test_list_inbox_default(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """list_inbox returns non-dismissed items by default."""
        items, total = await inbox_service.list_inbox()
        assert total == 0
        assert items == []
        inbox_repo.list_by_status.assert_awaited_once_with(
            inbox_status=None, dismissed=False, page=1, page_size=20
        )

    async def test_list_inbox_with_filter(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """list_inbox with specific status filter."""
        items, total = await inbox_service.list_inbox(
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION
        )
        inbox_repo.list_by_status.assert_awaited_once_with(
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
            dismissed=False,
            page=1,
            page_size=20,
        )

    async def test_get_item_not_found(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """get_item raises for non-existent item."""
        inbox_repo.get_by_id.return_value = None
        with pytest.raises(Exception, match="not found"):
            await inbox_service.get_item(uuid4())

    async def test_correct_intent(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """Correcting intent updates fields and records history."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_test",
            gmail_thread_id="thread_test",
            sender_email="test@example.com",
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
            prediction_intent="job_application",
        )
        inbox_repo.get_by_id.return_value = item
        inbox_repo.update.return_value = item

        user_id = uuid4()
        updated = await inbox_service.correct_intent(
            item_id=item.id,
            corrected_intent="other",
            user_id=user_id,
        )

        assert updated.corrected_intent == "other"
        assert updated.corrected_by_user_id == user_id
        assert updated.inbox_status == InboxStatus.RESOLVED
        assert len(updated.correction_history or []) == 1
        inbox_repo.update.assert_awaited_once()

    async def test_correct_job_application_with_attachment_is_ready_for_review(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """A complete corrected Job Application becomes ready for HR review."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_ready_after_correction",
            gmail_thread_id="thread_ready_after_correction",
            sender_email="candidate@example.com",
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
            has_attachments=True,
        )
        inbox_repo.get_by_id.return_value = item
        inbox_repo.update.return_value = item

        updated = await inbox_service.correct_intent(
            item_id=item.id,
            corrected_intent="job_application",
            user_id=uuid4(),
        )

        assert updated.inbox_status == InboxStatus.READY_FOR_REVIEW

    async def test_correct_incomplete_job_application_needs_information(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """A corrected Job Application without profile material needs information."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_needs_info_after_correction",
            gmail_thread_id="thread_needs_info_after_correction",
            sender_email="candidate@example.com",
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
            has_attachments=False,
            attachments_metadata=[],
        )
        inbox_repo.get_by_id.return_value = item
        inbox_repo.update.return_value = item

        updated = await inbox_service.correct_intent(
            item_id=item.id,
            corrected_intent="job_application",
            user_id=uuid4(),
        )

        assert updated.inbox_status == InboxStatus.NEEDS_INFORMATION

    async def test_dismiss_item(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """Dismissing an item sets dismissed=True and resolves it."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_dismiss",
            gmail_thread_id="thread_dismiss",
            sender_email="test@example.com",
            inbox_status=InboxStatus.NEEDS_CLASSIFICATION,
        )
        inbox_repo.get_by_id.return_value = item
        inbox_repo.update.return_value = item

        user_id = uuid4()
        updated = await inbox_service.dismiss_item(item_id=item.id, user_id=user_id)

        assert updated.dismissed is True
        assert updated.dismissed_by_user_id == user_id
        assert updated.dismissed_at is not None
        assert updated.inbox_status == InboxStatus.RESOLVED
        inbox_repo.update.assert_awaited_once()

    async def test_dismiss_already_dismissed(
        self,
        inbox_service: InboxService,
        inbox_repo: MagicMock,
    ) -> None:
        """Dismissing an already-dismissed item raises."""
        item = RecruitmentInboxItem(
            gmail_message_id="msg_dismissed",
            gmail_thread_id="thread_dismissed",
            sender_email="test@example.com",
            inbox_status=InboxStatus.RESOLVED,
            dismissed=True,
        )
        inbox_repo.get_by_id.return_value = item

        from src.modules.recruitment.application.inbox_service import InboxItemDismissedError

        with pytest.raises(InboxItemDismissedError):
            await inbox_service.dismiss_item(item_id=item.id, user_id=uuid4())

    async def test_attachment_metadata_propagated(
        self,
    ) -> None:
        """Attachment metadata from email is propagated to inbox item."""
        repo = MagicMock(spec=RecruitmentInboxItemRepository)
        repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=None)
        repo.create = AsyncMock()

        service = InboxService(session=AsyncMock(), inbox_repo=repo)

        email = _make_mock_email("msg_attachments", has_attachments=True)

        class MockAttachment:
            filename = "CV.pdf"
            mime_type = "application/pdf"
            size = 123456

        email.attachments = [MockAttachment()]

        await service.create_from_classification(
            email=email,
            classification_result=_make_low_confidence_recruitment_result(),
        )

        repo.create.assert_awaited_once()
        created = repo.create.await_args[0][0]
        assert created.has_attachments is True
        assert created.attachments_metadata is not None
        assert len(created.attachments_metadata) == 1
        assert created.attachments_metadata[0]["name"] == "CV.pdf"
        assert created.attachments_metadata[0]["type"] == "application/pdf"
        assert created.attachments_metadata[0]["size"] == 123456


class TestMultiApplicantRouting:
    """Multi-applicant sources require HR splitting at every confidence."""

    @pytest.mark.parametrize("confidence", [0.40, 0.95])
    async def test_multi_applicant_email_routes_to_ready_inbox_without_single_application(
        self,
        confidence: float,
        settings: GmailSettings,
        session: AsyncMock,
        audit_logger: AsyncMock,
        email_repo: AsyncMock,
    ) -> None:
        result = ClassificationResult(
            category=EmailCategory.recruitment,
            confidence=confidence,
            source="ai",
            matched_signals=["application_language", "multiple_applicants"],
            source_hints=(
                ("sender_role", "agency"),
                ("multiple_applicants", "true"),
            ),
        )
        inbox_repo = MagicMock(spec=RecruitmentInboxItemRepository)
        inbox_repo.find_dismissed_by_gmail_message_id = AsyncMock(return_value=None)
        inbox_repo.get_by_gmail_message_id = AsyncMock(return_value=None)
        inbox_repo.create = AsyncMock(side_effect=lambda item: item)
        inbox_service = InboxService(session=session, inbox_repo=inbox_repo)
        job_application_callback = AsyncMock()
        rules_classifier = MagicMock()
        rules_classifier.classify = MagicMock(return_value=result)
        ai_classifier = AsyncMock()
        ai_classifier.classify = AsyncMock(return_value=result)
        service = ClassificationService(
            rules_classifier=rules_classifier,
            ai_classifier=ai_classifier,
            email_repo=email_repo,
            audit_logger=audit_logger,
            settings=settings,
            session=session,
            on_application_created=job_application_callback,
            on_uncertain_classification=inbox_service.create_from_classification,
        )
        email = _make_mock_email(
            email_id="msg_multi_applicant",
            thread_id="thread_multi_applicant",
            sender_email="recruiter@agency.example",
        )

        classified_count = await service.classify_batch(user_id=uuid4(), emails=[email])

        assert classified_count == 1
        job_application_callback.assert_not_awaited()
        inbox_repo.create.assert_awaited_once()
        created = inbox_repo.create.await_args[0][0]
        assert created.inbox_status == InboxStatus.READY_FOR_REVIEW
        assert created.source_hints == [
            {"key": "sender_role", "value": "agency"},
            {"key": "multiple_applicants", "value": "true"},
        ]
