"""Unit tests for ESS rate limiter (sliding window with Redis sorted sets).

Tests the ESSRateLimiter class and the check_ess_rate_limit dependency
that enforces 60 requests per minute per employee.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.self_service.api.rate_limiter import (
    ESSRateLimiter,
    check_ess_rate_limit,
)


@pytest.fixture
def employee_id():
    """Generate a fixed employee UUID for tests."""
    return uuid4()


@pytest.fixture
def mock_redis():
    """Create a mock async Redis client."""
    return AsyncMock()


@pytest.fixture
def rate_limiter(mock_redis):
    """Create an ESSRateLimiter with mocked Redis."""
    return ESSRateLimiter(redis_client=mock_redis)


class TestESSRateLimiterInit:
    """Tests for ESSRateLimiter initialization."""

    def test_stores_redis_client(self, rate_limiter, mock_redis):
        """Should store the Redis client reference."""
        assert rate_limiter._redis is mock_redis

    def test_default_max_requests(self, rate_limiter):
        """Should default to 60 max requests."""
        assert rate_limiter._max_requests == 60

    def test_default_window_seconds(self, rate_limiter):
        """Should default to 60 second window."""
        assert rate_limiter._window_seconds == 60

    def test_custom_max_requests(self, mock_redis):
        """Should accept custom max_requests."""
        limiter = ESSRateLimiter(mock_redis, max_requests=100)
        assert limiter._max_requests == 100

    def test_custom_window_seconds(self, mock_redis):
        """Should accept custom window_seconds."""
        limiter = ESSRateLimiter(mock_redis, window_seconds=120)
        assert limiter._window_seconds == 120


class TestESSRateLimiterKeyFormat:
    """Tests for Redis key format."""

    async def test_uses_correct_key_format(self, rate_limiter, mock_redis, employee_id):
        """Should use rate_limit:ess:{employee_id} as the Redis key."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.zadd = AsyncMock()
        pipeline_mock.expire = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 0])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        await rate_limiter.check_rate_limit(employee_id)

        expected_key = f"rate_limit:ess:{employee_id}"
        pipeline_mock.zremrangebyscore.assert_called_once()
        call_args = pipeline_mock.zremrangebyscore.call_args
        assert call_args[0][0] == expected_key


class TestESSRateLimiterAllowsRequests:
    """Tests for allowing requests under the limit."""

    async def test_allows_when_no_prior_requests(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should allow request when no prior requests exist (count=0)."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.zadd = AsyncMock()
        pipeline_mock.expire = AsyncMock()
        # First pipeline: zremrangebyscore + zcard returns count=0
        pipeline_mock.execute = AsyncMock(return_value=[0, 0])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        # Should not raise
        await rate_limiter.check_rate_limit(employee_id)

    async def test_allows_when_under_limit(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should allow request when count is below 60."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.zadd = AsyncMock()
        pipeline_mock.expire = AsyncMock()
        # 59 requests in window - still under limit
        pipeline_mock.execute = AsyncMock(return_value=[0, 59])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        # Should not raise
        await rate_limiter.check_rate_limit(employee_id)

    async def test_adds_timestamp_to_sorted_set(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should add current timestamp to the sorted set after allowing."""
        call_count = [0]
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.zadd = AsyncMock()
        pipeline_mock.expire = AsyncMock()

        async def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return [0, 5]  # First call: cleanup + count
            return [True, True]  # Second call: zadd + expire

        pipeline_mock.execute = AsyncMock(side_effect=execute_side_effect)
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        await rate_limiter.check_rate_limit(employee_id)

        # Verify zadd was called (second pipeline)
        pipeline_mock.zadd.assert_called_once()

    async def test_sets_key_expiry(self, rate_limiter, mock_redis, employee_id):
        """Should set TTL on the key equal to window_seconds."""
        call_count = [0]
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.zadd = AsyncMock()
        pipeline_mock.expire = AsyncMock()

        async def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return [0, 5]
            return [True, True]

        pipeline_mock.execute = AsyncMock(side_effect=execute_side_effect)
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        await rate_limiter.check_rate_limit(employee_id)

        expected_key = f"rate_limit:ess:{employee_id}"
        pipeline_mock.expire.assert_called_once_with(expected_key, 60)


class TestESSRateLimiterRejectsRequests:
    """Tests for rejecting requests when limit is exceeded."""

    async def test_raises_429_when_at_limit(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should raise HTTPException 429 when count equals max_requests."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 60])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        # Mock zrange to return oldest entry
        now = time.time()
        mock_redis.zrange = AsyncMock(
            return_value=[("entry", now - 50)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(employee_id)

        assert exc_info.value.status_code == 429

    async def test_raises_429_when_over_limit(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should raise HTTPException 429 when count exceeds max_requests."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 100])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        now = time.time()
        mock_redis.zrange = AsyncMock(
            return_value=[("entry", now - 30)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(employee_id)

        assert exc_info.value.status_code == 429

    async def test_429_includes_retry_after_header(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should include Retry-After header in 429 response."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 60])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        now = time.time()
        mock_redis.zrange = AsyncMock(
            return_value=[("entry", now - 50)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(employee_id)

        assert "Retry-After" in exc_info.value.headers
        retry_after = int(exc_info.value.headers["Retry-After"])
        # oldest entry was 50s ago, window is 60s, so ~10s remaining
        assert 1 <= retry_after <= 60

    async def test_retry_after_calculates_correctly(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should calculate Retry-After as time until oldest entry expires."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 60])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        now = time.time()
        # Oldest entry was 55 seconds ago → expires in 5 seconds
        mock_redis.zrange = AsyncMock(
            return_value=[("entry", now - 55)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(employee_id)

        retry_after = int(exc_info.value.headers["Retry-After"])
        # Should be approximately 5 seconds (ceil of 60 - 55 = 5)
        assert 4 <= retry_after <= 6

    async def test_429_includes_rate_limit_exceeded_code(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should include RATE_LIMIT_EXCEEDED error code in detail."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 60])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        now = time.time()
        mock_redis.zrange = AsyncMock(
            return_value=[("entry", now - 30)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(employee_id)

        assert exc_info.value.detail["code"] == "RATE_LIMIT_EXCEEDED"

    async def test_retry_after_minimum_is_1(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should return at least 1 second for Retry-After."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 60])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        now = time.time()
        # Oldest entry is almost exactly at window boundary
        mock_redis.zrange = AsyncMock(
            return_value=[("entry", now - 59.9)]
        )

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(employee_id)

        retry_after = int(exc_info.value.headers["Retry-After"])
        assert retry_after >= 1

    async def test_retry_after_fallback_when_no_oldest(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should fallback to window_seconds when no oldest entry found."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 60])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        # No entries returned (edge case)
        mock_redis.zrange = AsyncMock(return_value=[])

        with pytest.raises(HTTPException) as exc_info:
            await rate_limiter.check_rate_limit(employee_id)

        retry_after = int(exc_info.value.headers["Retry-After"])
        assert retry_after == 60

    async def test_does_not_add_entry_when_rejected(
        self, rate_limiter, mock_redis, employee_id
    ):
        """Should not add a new entry to the sorted set when rate limited."""
        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.zadd = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 60])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        now = time.time()
        mock_redis.zrange = AsyncMock(
            return_value=[("entry", now - 30)]
        )

        with pytest.raises(HTTPException):
            await rate_limiter.check_rate_limit(employee_id)

        # zadd should NOT have been called since we rejected
        pipeline_mock.zadd.assert_not_called()


class TestESSRateLimiterSlidingWindow:
    """Tests for the sliding window cleanup behavior."""

    @patch("src.modules.self_service.api.rate_limiter.time.time")
    async def test_removes_entries_older_than_window(
        self, mock_time, rate_limiter, mock_redis, employee_id
    ):
        """Should remove entries older than window_seconds from the sorted set."""
        mock_time.return_value = 1000.0

        pipeline_mock = AsyncMock()
        pipeline_mock.zremrangebyscore = AsyncMock()
        pipeline_mock.zcard = AsyncMock()
        pipeline_mock.zadd = AsyncMock()
        pipeline_mock.expire = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 0])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        await rate_limiter.check_rate_limit(employee_id)

        expected_key = f"rate_limit:ess:{employee_id}"
        # Should remove entries with score < (1000.0 - 60) = 940.0
        pipeline_mock.zremrangebyscore.assert_called_once_with(
            expected_key, "-inf", 940.0
        )


class TestCheckEssRateLimitDependency:
    """Tests for the check_ess_rate_limit FastAPI dependency."""

    async def test_returns_employee_id_when_allowed(self, employee_id):
        """Should return employee_id when rate limit is not exceeded."""
        mock_limiter = AsyncMock()
        mock_limiter.check_rate_limit = AsyncMock()

        result = await check_ess_rate_limit(
            employee_id=employee_id,
            rate_limiter=mock_limiter,
        )

        assert result == employee_id

    async def test_calls_check_rate_limit_with_employee_id(self, employee_id):
        """Should call check_rate_limit with the employee_id."""
        mock_limiter = AsyncMock()
        mock_limiter.check_rate_limit = AsyncMock()

        await check_ess_rate_limit(
            employee_id=employee_id,
            rate_limiter=mock_limiter,
        )

        mock_limiter.check_rate_limit.assert_called_once_with(employee_id)

    async def test_propagates_429_from_rate_limiter(self, employee_id):
        """Should propagate HTTPException 429 from the rate limiter."""
        mock_limiter = AsyncMock()
        mock_limiter.check_rate_limit = AsyncMock(
            side_effect=HTTPException(
                status_code=429,
                detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests."},
                headers={"Retry-After": "10"},
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await check_ess_rate_limit(
                employee_id=employee_id,
                rate_limiter=mock_limiter,
            )

        assert exc_info.value.status_code == 429
        assert exc_info.value.headers["Retry-After"] == "10"
