"""Redis-based sliding window rate limiter for ESS endpoints.

Uses Redis sorted sets to implement a sliding window counter that tracks
requests per employee within a 60-second window. Returns 429 with
Retry-After header when the limit is exceeded.
"""

from __future__ import annotations

import math
import time
from uuid import UUID

import redis.asyncio as redis
from fastapi import Depends, HTTPException

from src.modules.identity.container import get_redis_client
from src.modules.self_service.api.dependencies import get_current_employee

# Rate limit configuration
_MAX_REQUESTS_PER_MINUTE = 60
_WINDOW_SECONDS = 60


class ESSRateLimiter:
    """Redis-based sliding window rate limiter for ESS endpoints.

    Tracks requests per employee using Redis sorted sets. Each request
    is stored as a member with its timestamp as the score, enabling
    efficient sliding window calculations.

    Args:
        redis_client: An async Redis client instance.
        max_requests: Maximum requests allowed per window (default: 60).
        window_seconds: Sliding window duration in seconds (default: 60).

    Example:
        >>> limiter = ESSRateLimiter(redis_client)
        >>> await limiter.check_rate_limit(employee_id)  # raises HTTPException on 429
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int = _MAX_REQUESTS_PER_MINUTE,
        window_seconds: int = _WINDOW_SECONDS,
    ) -> None:
        self._redis = redis_client
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    async def check_rate_limit(self, employee_id: UUID) -> None:
        """Check whether the employee is within the rate limit.

        Uses a sliding window algorithm with Redis sorted sets:
        1. Remove expired entries outside the current window.
        2. Count remaining entries in the window.
        3. If at or over the limit, raise 429 with Retry-After header.
        4. Otherwise, add the current request timestamp.

        Args:
            employee_id: The authenticated employee's UUID.

        Raises:
            HTTPException: 429 with Retry-After header when rate limit exceeded.
        """
        key = f"rate_limit:ess:{employee_id}"
        now = time.time()
        window_start = now - self._window_seconds

        pipe = self._redis.pipeline()

        # Remove entries outside the sliding window
        pipe.zremrangebyscore(key, "-inf", window_start)

        # Count entries within the current window
        pipe.zcard(key)

        results = await pipe.execute()
        current_count: int = results[1]

        if current_count >= self._max_requests:
            # Calculate Retry-After: time until the oldest entry expires
            oldest_entries = await self._redis.zrange(key, 0, 0, withscores=True)
            if oldest_entries:
                oldest_timestamp = oldest_entries[0][1]
                retry_after = math.ceil(
                    (oldest_timestamp + self._window_seconds) - now
                )
                retry_after = max(retry_after, 1)
            else:
                retry_after = self._window_seconds

            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Add the current request and set key expiry
        pipe = self._redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, self._window_seconds)
        await pipe.execute()


async def get_ess_rate_limiter(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> ESSRateLimiter:
    """Provide an ESSRateLimiter instance via FastAPI DI.

    Returns:
        An ESSRateLimiter configured with the shared Redis client.
    """
    return ESSRateLimiter(redis_client=redis_client)


async def check_ess_rate_limit(
    employee_id: UUID = Depends(get_current_employee),
    rate_limiter: ESSRateLimiter = Depends(get_ess_rate_limiter),
) -> UUID:
    """FastAPI dependency that enforces rate limiting for ESS endpoints.

    This dependency should be used alongside or instead of get_current_employee
    on ESS routes. It first resolves the employee_id (via get_current_employee),
    then checks the rate limit. If the limit is exceeded, it raises a 429.
    Otherwise, it returns the employee_id for use by the route handler.

    Args:
        employee_id: The authenticated employee's UUID (from get_current_employee).
        rate_limiter: The rate limiter instance (from DI).

    Returns:
        The authenticated employee's UUID (same as get_current_employee).

    Raises:
        HTTPException: 429 with Retry-After header when rate limit exceeded.
        HTTPException: 401/403 from get_current_employee if auth fails.
    """
    await rate_limiter.check_rate_limit(employee_id)
    return employee_id
