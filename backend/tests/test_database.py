import pytest
from unittest.mock import MagicMock, patch
from src.database import get_session

def test_get_session_success():
    """
    Test that the session yields correctly and commits upon success.
    Note: The source code uses `Session(_get_engine())` and explicitly calls
    `session.commit()` inside the try block after yielding.
    """
    mock_session_instance = MagicMock()

    with patch("src.database.Session", return_value=mock_session_instance) as MockSession, \
         patch("src.database._get_engine") as mock_get_engine:

        # __enter__ returns the session context manager
        mock_session_instance.__enter__.return_value = mock_session_instance

        gen = get_session()

        # Yields the session
        session = next(gen)

        assert session is mock_session_instance

        # Finish generator without exception, which triggers session.commit()
        with pytest.raises(StopIteration):
            next(gen)

        # Ensure commit is called inside the try block
        mock_session_instance.commit.assert_called_once()
        mock_session_instance.rollback.assert_not_called()

def test_get_session_rollback():
    """
    Test that the session rollbacks and raises an exception when an error occurs
    within the generator's yielded scope.
    """
    mock_session_instance = MagicMock()

    with patch("src.database.Session", return_value=mock_session_instance) as MockSession, \
         patch("src.database._get_engine") as mock_get_engine:

        mock_session_instance.__enter__.return_value = mock_session_instance

        gen = get_session()

        session = next(gen)

        # Simulate exception raised in the scope using the generator
        with pytest.raises(ValueError, match="Test error"):
            gen.throw(ValueError("Test error"))

        mock_session_instance.rollback.assert_called_once()
        mock_session_instance.commit.assert_not_called()
