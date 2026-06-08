"""Attendance settings service for office network allowlist management."""

import re

from src.modules.attendance.domain.exceptions import (
    CidrNotFoundError,
    DuplicateCidrError,
    InvalidCidrError,
    TooManyNetworksError,
)
from src.modules.attendance.domain.value_objects import (
    AttendanceNetworkConfig,
)
from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)


class AttendanceSettingsService:
    """Service for managing attendance network configuration.

    Provides methods to get, set, add, and remove CIDR ranges from the
    organization's attendance allowlist. Also provides IP validation
    for check-in/check-out operations.
    """

    def __init__(self, org_repo: OrganizationSettingsRepository) -> None:
        """Initialize the service.

        Args:
            org_repo: The organization settings repository.
        """
        self._org_repo = org_repo

    async def get_allowed_networks(self) -> list[str]:
        """Get the list of allowed CIDR ranges.

        Returns:
            List of CIDR strings. Empty list means allow all.
        """
        return await self._org_repo.get_attendance_allowed_networks()

    async def get_network_config(self) -> AttendanceNetworkConfig:
        """Get the attendance network configuration as a value object.

        Returns:
            An AttendanceNetworkConfig instance.
        """
        networks = await self.get_allowed_networks()
        if not networks:
            return AttendanceNetworkConfig.empty()
        return AttendanceNetworkConfig.from_cidr_strings(networks)

    async def set_allowed_networks(self, networks: list[str]) -> list[str]:
        """Replace the entire allowlist.

        Args:
            networks: List of CIDR strings.

        Returns:
            The persisted list of CIDR strings.

        Raises:
            InvalidCidrError: If any CIDR is invalid.
            TooManyNetworksError: If more than 20 entries.
        """
        self._validate_networks(networks)
        return await self._org_repo.set_attendance_allowed_networks(networks)

    async def add_networks(self, networks: list[str]) -> list[str]:
        """Add one or more CIDRs to the allowlist.

        Args:
            networks: List of CIDR strings to add.

        Returns:
            The updated list of CIDR strings.

        Raises:
            InvalidCidrError: If any CIDR is invalid.
            DuplicateCidrError: If any CIDR already exists.
            TooManyNetworksError: If would exceed 20 entries.
        """
        self._validate_networks(networks)
        return await self._org_repo.add_networks(networks)

    async def remove_network(self, cidr: str) -> list[str]:
        """Remove a CIDR from the allowlist.

        Args:
            cidr: CIDR string to remove.

        Returns:
            The updated list of CIDR strings.

        Raises:
            CidrNotFoundError: If CIDR not in allowlist.
        """
        try:
            return await self._org_repo.remove_network(cidr)
        except ValueError as e:
            if "not found" in str(e).lower():
                raise CidrNotFoundError(cidr) from e
            raise

    async def is_ip_allowed(self, ip: str) -> bool:
        """Check if an IP is allowed for attendance check-in/out.

        Args:
            ip: The client IP address to check.

        Returns:
            True if the IP is allowed, False otherwise.
            Returns True if allowlist is empty (allow all).
        """
        config = await self.get_network_config()
        return config.is_ip_allowed(ip)

    @staticmethod
    def _validate_networks(networks: list[str]) -> None:
        """Validate network list and convert ValueError to domain exceptions.

        Args:
            networks: List of CIDR strings to validate.

        Raises:
            InvalidCidrError: If any CIDR is invalid.
            TooManyNetworksError: If exceeds max limit.
        """
        if len(networks) > 20:
            raise TooManyNetworksError(20)

        cidr_re = re.compile(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/(?:[0-9]|[12][0-9]|3[0-2])$"
        )

        seen: set[str] = set()
        for cidr in networks:
            normalized = cidr.strip()
            if not cidr_re.match(normalized):
                raise InvalidCidrError(cidr)
            if normalized in seen:
                raise DuplicateCidrError(cidr)
            seen.add(normalized)
