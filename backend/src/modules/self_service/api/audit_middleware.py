"""Audit logging middleware for Employee Self-Service endpoints.

Logs all ESS endpoint access events including HTTP method, path,
employee_id (extracted from JWT), response status, and request duration.
Follows structured logging format for analysis and compliance.

Requirements: 12.4 - Log all self-service data access events for audit purposes.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("ess.audit")


class ESSAuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all requests to ESS endpoints for audit purposes.

    Captures method, path, employee_id (from JWT token claims), response
    status code, and request duration. Never logs sensitive data such as
    request bodies or token values.
    """

    ESS_PATH_PREFIX = "/api/v1/ess"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and log audit event for ESS endpoints."""
        # Only audit ESS endpoints
        if not request.url.path.startswith(self.ESS_PATH_PREFIX):
            return await call_next(request)

        start_time = time.perf_counter()

        # Extract employee_id from token if available (best-effort, no blocking)
        employee_id = self._extract_employee_id(request)

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Log the audit event (structured)
        logger.info(
            "ESS access: method=%s path=%s employee_id=%s status=%d duration_ms=%.2f",
            request.method,
            request.url.path,
            employee_id or "anonymous",
            response.status_code,
            duration_ms,
            extra={
                "event_type": "ess_access",
                "method": request.method,
                "path": request.url.path,
                "employee_id": str(employee_id) if employee_id else None,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            },
        )

        return response

    def _extract_employee_id(self, request: Request) -> str | None:
        """Extract employee_id from JWT token cookie (best-effort).

        Does not validate the token — just decodes the payload to get
        the employee_id claim for logging purposes. Returns None if
        extraction fails for any reason.
        """
        try:
            import json
            import base64

            token = request.cookies.get("access_token")
            if not token:
                return None

            # Decode JWT payload (second segment) without verification
            # This is safe for logging — actual auth is handled by dependencies
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Add padding for base64 decoding
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes)
            return payload.get("employee_id")
        except Exception:
            # Never block request processing due to audit extraction failure
            return None
