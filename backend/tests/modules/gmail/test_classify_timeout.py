"""Unit tests for request-level timeout behavior in the classify endpoint.

Validates that the POST /api/gmail/classify endpoint returns HTTP 504
with a JSON error body when the classification process exceeds the
configured request timeout.

**Validates: Requirements 2.3**
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.modules.gmail.infrastructure.config import GmailSettings


def _create_test_app():
    """Create a minimal FastAPI app with only the gmail router for testing."""
    from fastapi import FastAPI

    from src.modules.gmail.api.router import router as gmail_router

    app = FastAPI()
    app.include_router(gmail_router)
    return app


def _make_mock_user():
    """Create a mock user with required attributes."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    user.role = "user"
    return user


def _make_mock_email():
    """Create a mock EmailMessage with required attributes."""
    email = MagicMock()
    email.gmail_message_id = f"msg_{uuid4().hex[:12]}"
    email.subject = "Test email subject"
    email.sender_email = "test@example.com"
    email.sender_name = "Test Sender"
    email.snippet = "This is a test email snippet"
    email.has_attachments = False
    email.processing_status = "unprocessed"
    email.category = None
    email.user_id = uuid4()
    return email


class TestClassifyEndpointTimeout:
    """Tests that the classify endpoint returns HTTP 504 when timeout is exceeded."""

    async def test_returns_504_when_classification_exceeds_timeout(self) -> None:
        """When AI classification takes longer than the request timeout,
        the endpoint should return HTTP 504 with a JSON error body."""
        mock_user = _make_mock_user()
        mock_emails = [_make_mock_email() for _ in range(3)]

        # Mock the session and its execute method
        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_emails

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        # For the count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3

        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_count_result])
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # Mock email_repo
        mock_email_repo = MagicMock()
        mock_email_repo.session = mock_session

        # Create settings with a very short timeout (1 second)
        test_settings = GmailSettings(
            classification_request_timeout_seconds=1,
            classification_batch_concurrency=3,
            classification_confidence_threshold=0.75,
        )

        # Mock ClassificationService.classify_batch to sleep beyond the timeout
        async def slow_classify_batch(*args, **kwargs):
            await asyncio.sleep(3)  # 3s > 1s timeout
            return 3

        app = _create_test_app()

        from src.modules.gmail.container import get_email_repository
        from src.modules.identity.container import get_current_user

        # Override dependencies
        from src.modules.gmail.container import get_connection_service

        mock_connection_service = AsyncMock()
        mock_connection_service.get_status = AsyncMock(
            return_value=MagicMock(status="connected")
        )

        async def _mock_get_connection_service():
            return mock_connection_service

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_email_repository] = lambda: mock_email_repo
        app.dependency_overrides[get_connection_service] = _mock_get_connection_service

        with patch(
            "src.modules.gmail.infrastructure.config.GmailSettings",
            return_value=test_settings,
        ):
            with patch(
                "src.modules.gmail.application.classification_service"
                ".ClassificationService.classify_batch",
                side_effect=slow_classify_batch,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post("/api/gmail/classify")

        assert response.status_code == 504
        body = response.json()
        assert "detail" in body

    async def test_504_response_body_contains_timeout_message(self) -> None:
        """The 504 response body should contain a 'detail' field with a
        meaningful timeout message."""
        mock_user = _make_mock_user()
        mock_emails = [_make_mock_email() for _ in range(2)]

        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_emails

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_count_result])
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        mock_email_repo = MagicMock()
        mock_email_repo.session = mock_session

        test_settings = GmailSettings(
            classification_request_timeout_seconds=1,
            classification_batch_concurrency=3,
            classification_confidence_threshold=0.75,
        )

        async def slow_classify_batch(*args, **kwargs):
            await asyncio.sleep(3)
            return 2

        app = _create_test_app()

        from src.modules.gmail.container import get_email_repository
        from src.modules.identity.container import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_email_repository] = lambda: mock_email_repo


        from src.modules.gmail.container import get_connection_service

        mock_connection_service = AsyncMock()
        mock_connection_service.get_status = AsyncMock(
            return_value=MagicMock(status="connected")
        )

        async def _mock_get_connection_service():
            return mock_connection_service

        app.dependency_overrides[get_connection_service] = _mock_get_connection_service
        with patch(
            "src.modules.gmail.infrastructure.config.GmailSettings",
            return_value=test_settings,
        ):
            with patch(
                "src.modules.gmail.application.classification_service"
                ".ClassificationService.classify_batch",
                side_effect=slow_classify_batch,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post("/api/gmail/classify")

        assert response.status_code == 504
        body = response.json()
        assert "detail" in body
        # The detail message should mention timeout
        assert "timeout" in body["detail"].lower() or "Timeout" in body["detail"]

    async def test_successful_classification_within_timeout(self) -> None:
        """When classification completes within the timeout, the endpoint
        should return HTTP 200 with the normal response schema."""
        mock_user = _make_mock_user()
        mock_emails = [_make_mock_email() for _ in range(2)]
        # Set category on emails so results_summary works
        for email in mock_emails:
            email.category = "recruitment"

        mock_session = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_emails

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_count_result])
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        mock_email_repo = MagicMock()
        mock_email_repo.session = mock_session

        # Use a generous timeout so classification succeeds
        test_settings = GmailSettings(
            classification_request_timeout_seconds=10,
            classification_batch_concurrency=3,
            classification_confidence_threshold=0.75,
        )

        async def fast_classify_batch(*args, **kwargs):
            await asyncio.sleep(0.1)  # Fast — well within 10s timeout
            return 2

        app = _create_test_app()

        from src.modules.gmail.container import get_email_repository
        from src.modules.identity.container import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_email_repository] = lambda: mock_email_repo


        from src.modules.gmail.container import get_connection_service

        mock_connection_service = AsyncMock()
        mock_connection_service.get_status = AsyncMock(
            return_value=MagicMock(status="connected")
        )

        async def _mock_get_connection_service():
            return mock_connection_service

        app.dependency_overrides[get_connection_service] = _mock_get_connection_service
        with patch(
            "src.modules.gmail.infrastructure.config.GmailSettings",
            return_value=test_settings,
        ):
            with patch(
                "src.modules.gmail.application.classification_service"
                ".ClassificationService.classify_batch",
                side_effect=fast_classify_batch,
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post("/api/gmail/classify")

        assert response.status_code == 200
        body = response.json()
        assert "classified_count" in body
        assert body["classified_count"] == 2
        assert "total" in body
        assert "remaining" in body
        assert "message" in body
        assert "results" in body
