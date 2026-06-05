"""Domain gate service for the Identity & Auth module.

Checks whether an email's domain is allowed by the Organization's
allowed_domains configuration.  When the allowed_domains list is
empty, all domains pass (no restriction).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.recruitment.infrastructure.org_settings_repository import (
        OrganizationSettingsRepository,
    )


class DomainGateService:
    """Checks whether an email domain is permitted by the Organization.

    Args:
        org_settings_repository: Repository for reading Organization
            settings including the allowed_domains list.
    """

    def __init__(
        self,
        org_settings_repository: OrganizationSettingsRepository,
    ) -> None:
        self._repo = org_settings_repository

    async def is_email_allowed(self, email: str) -> bool:
        """Check if the email's domain is in the Organization's allowed list.

        Args:
            email: The authenticated user's email address.

        Returns:
            True if allowed (domain matches or list is empty), False
            if the domain is not in the allowed list or the email
            is malformed.
        """
        allowed = await self._repo.get_allowed_domains()
        if not allowed:
            return True  # Empty list = no restriction

        if "@" not in email:
            return False

        domain = email.split("@")[-1].lower()
        return domain in allowed
