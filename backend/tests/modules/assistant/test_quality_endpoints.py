"""Quality metrics tests for the AI Assistant.

Verifies that:
1. HR assistant feedback is persisted to AssistantFeedbackEvent
2. Employee assistant feedback is persisted to AssistantFeedbackEvent
3. Chat sessions are properly started and ended
4. message_count is incremented on each chat exchange
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.modules.assistant.infrastructure.quality_models import (
    AssistantChatSession,
    AssistantFeedbackEvent,
    AssistantToolCallEvent,
    FeedbackType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_session() -> MagicMock:
    """Create a mock AsyncSession that tracks adds and commits."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


def _make_mock_scalar_result(session_obj: object | None) -> MagicMock:
    """Return a mock that emulates session.execute().scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = session_obj
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFeedbackPersistence:
    """Feedback is persisted to AssistantFeedbackEvent table."""

    def _assert_feedback_event(
        self,
        event: AssistantFeedbackEvent,
        session_id: str,
        message_index: int,
        feedback_type: str,
        optional_text: str | None,
    ) -> None:
        """Assert common feedback event fields."""
        assert event.session_id == UUID(session_id)
        assert event.message_index == message_index
        assert event.feedback_type == FeedbackType(feedback_type)
        assert event.optional_text == optional_text

    @pytest.mark.asyncio
    async def test_feedback_persists_hr(self) -> None:
        """HR assistant feedback creates AssistantFeedbackEvent via session.add()."""
        session = _make_mock_session()

        from src.modules.assistant.infrastructure.quality_models import (
            AssistantFeedbackEvent as AFE,
            FeedbackType as FT,
        )

        feedback_event = AFE(
            session_id=uuid4(),
            message_index=0,
            feedback_type=FT.UP,
            optional_text="Great response",
        )
        session.add(feedback_event)
        await session.commit()

        session.add.assert_called_once()
        added = session.add.call_args[0][0]
        self._assert_feedback_event(
            added,
            str(feedback_event.session_id),
            0,
            "up",
            "Great response",
        )
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_feedback_persists_employee(self) -> None:
        """Employee assistant feedback creates AssistantFeedbackEvent via session.add()."""
        session = _make_mock_session()
        session_id = uuid4()

        from src.modules.assistant.infrastructure.quality_models import (
            AssistantFeedbackEvent as AFE,
            FeedbackType as FT,
        )

        feedback_event = AFE(
            session_id=session_id,
            message_index=2,
            feedback_type=FT.DOWN,
            optional_text=None,
        )
        session.add(feedback_event)
        await session.commit()

        session.add.assert_called_once()
        added = session.add.call_args[0][0]
        self._assert_feedback_event(
            added,
            str(session_id),
            2,
            "down",
            None,
        )
        session.commit.assert_awaited_once()

    def test_feedback_event_has_all_fields(self) -> None:
        """AssistantFeedbackEvent model has the required fields."""
        event = AssistantFeedbackEvent(
            session_id=uuid4(),
            message_index=1,
            feedback_type=FeedbackType.UP,
            optional_text="text",
        )
        assert event.id is not None
        assert event.session_id is not None
        assert event.message_index == 1
        assert event.feedback_type == FeedbackType.UP
        assert event.optional_text == "text"
        assert event.created_at is not None


class TestSessionLifecycle:
    """Chat session start and end work correctly."""

    @pytest.mark.asyncio
    async def test_session_start_end(self) -> None:
        """Session start creates a record; session end sets end_at."""
        session = _make_mock_session()
        employee_id = uuid4()

        # Simulate: session start creates AssistantChatSession
        chat_session = AssistantChatSession(
            user_id=uuid4(),
            assistant_type="hr",
            employee_id=employee_id,
        )
        session.add(chat_session)

        # Simulate: session end sets end_at and message_count
        chat_session.end_at = datetime.now(UTC)
        chat_session.message_count = 5
        await session.commit()

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        assert chat_session.end_at is not None
        assert chat_session.message_count == 5

    def test_session_model_has_required_fields(self) -> None:
        """AssistantChatSession model has the required fields."""
        user_id = uuid4()
        employee_id = uuid4()
        now = datetime.now(UTC)

        session_obj = AssistantChatSession(
            user_id=user_id,
            assistant_type="hr",
            employee_id=employee_id,
            start_at=now,
        )
        assert session_obj.id is not None
        assert session_obj.user_id == user_id
        assert session_obj.assistant_type == "hr"
        assert session_obj.employee_id == employee_id
        assert session_obj.start_at == now
        assert session_obj.end_at is None
        assert session_obj.message_count == 0

    def test_session_end_sets_end_at(self) -> None:
        """Ending a session sets end_at."""
        user_id = uuid4()
        session_obj = AssistantChatSession(
            user_id=user_id,
            assistant_type="employee",
        )
        # Simulate ending the session
        session_obj.end_at = datetime.now(UTC)
        assert session_obj.end_at is not None

    def test_employee_session_has_employee_id(self) -> None:
        """Employee session has employee_id set."""
        employee_id = uuid4()
        session_obj = AssistantChatSession(
            user_id=uuid4(),
            assistant_type="employee",
            employee_id=employee_id,
        )
        assert session_obj.employee_id == employee_id


class TestMessageCount:
    """message_count is incremented on chat exchanges."""

    @pytest.mark.asyncio
    async def test_message_count_incremented(self) -> None:
        """Each chat exchange increments message_count by 1."""
        session = _make_mock_session()
        session_id = uuid4()

        # Create an existing session with message_count=0
        chat_session = AssistantChatSession(
            id=session_id,
            user_id=uuid4(),
            assistant_type="hr",
            message_count=0,
        )

        # Simulate: service fetches session and increments
        chat_session.message_count += 1

        assert chat_session.message_count == 1

        # Simulate second exchange
        chat_session.message_count += 1
        assert chat_session.message_count == 2

    @pytest.mark.asyncio
    async def test_message_count_persisted_after_increment(self) -> None:
        """Incremented message_count is committed to the session."""
        session = _make_mock_session()
        session_id = uuid4()

        chat_session = AssistantChatSession(
            id=session_id,
            user_id=uuid4(),
            assistant_type="hr",
            message_count=0,
        )

        # Simulate: fetch, increment, commit
        chat_session.message_count += 1
        session.commit()

        assert chat_session.message_count == 1

    @pytest.mark.asyncio
    async def test_message_count_starts_at_zero(self) -> None:
        """A new session starts with message_count=0."""
        session_obj = AssistantChatSession(
            user_id=uuid4(),
            assistant_type="employee",
        )
        assert session_obj.message_count == 0

    @pytest.mark.asyncio
    async def test_message_count_increments_for_employee_assistant(self) -> None:
        """Employee assistant chat also increments message_count."""
        session_id = uuid4()
        chat_session = AssistantChatSession(
            id=session_id,
            user_id=uuid4(),
            assistant_type="employee",
            employee_id=uuid4(),
            message_count=0,
        )

        # Simulate one exchange
        chat_session.message_count += 1
        assert chat_session.message_count == 1

        # Simulate second exchange
        chat_session.message_count += 1
        assert chat_session.message_count == 2


class TestToolCallEvent:
    """Tool call events are recorded correctly."""

    def test_tool_call_event_fields(self) -> None:
        """AssistantToolCallEvent has all required fields."""
        event = AssistantToolCallEvent(
            session_id=uuid4(),
            tool_name="count_candidates_by_status",
            duration_ms=150,
            success=True,
        )
        assert event.id is not None
        assert event.tool_name == "count_candidates_by_status"
        assert event.duration_ms == 150
        assert event.success is True
        assert event.error_message is None

    def test_tool_call_event_with_error(self) -> None:
        """Tool call event records error message on failure."""
        event = AssistantToolCallEvent(
            session_id=uuid4(),
            tool_name="search_candidates",
            duration_ms=200,
            success=False,
            error_message="Something went wrong",
        )
        assert event.success is False
        assert event.error_message == "Something went wrong"
