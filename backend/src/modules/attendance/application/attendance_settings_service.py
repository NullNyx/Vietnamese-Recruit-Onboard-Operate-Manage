"""Attendance settings service for office network allowlist management."""

import ipaddress

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


def _normalize_input(value: str) -> str:
    """Normalize a plain IP or CIDR string.

    A bare IPv4 address (e.g. ``192.168.1.10``) is automatically expanded
    to ``/32`` so the rest of the pipeline only ever sees CIDR notation.
    Already-CIDR values pass through unchanged.

    Args:
        value: A CIDR or plain-IPv4 string.

    Returns:
        A normalized CIDR string.

    Raises:
        InvalidCidrError: If the value is not a valid IPv4 address or CIDR.
    """
    normalized = value.strip()
    try:
        addr = ipaddress.ip_address(normalized)
        if isinstance(addr, ipaddress.IPv6Address):
            raise InvalidCidrError(value)
        # It's a bare IPv4 → normalize to /32
        return f"{addr}/32"
    except InvalidCidrError:
        raise
    except ValueError:
        pass
    # Not a bare IP; validate as CIDR
    try:
        net = ipaddress.ip_network(normalized, strict=False)
        if isinstance(net, ipaddress.IPv6Network):
            raise InvalidCidrError(value)
        return str(net)
    except InvalidCidrError:
        raise
    except ValueError:
        raise InvalidCidrError(value)


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
            networks: List of CIDR strings (plain IPs are auto-normalized to /32).

        Returns:
            The persisted list of CIDR strings.

        Raises:
            InvalidCidrError: If any CIDR is invalid.
            TooManyNetworksError: If more than 20 entries.
        """
        normalized = self._validate_and_normalize(networks)
        return await self._org_repo.set_attendance_allowed_networks(normalized)

    async def add_networks(self, networks: list[str]) -> list[str]:
        """Add one or more CIDRs to the allowlist.

        Args:
            networks: List of CIDR strings to add (plain IPs auto-normalized).

        Returns:
            The updated list of CIDR strings.

        Raises:
            InvalidCidrError: If any CIDR is invalid.
            DuplicateCidrError: If any CIDR already exists.
            TooManyNetworksError: If would exceed 20 entries.
        """
        normalized = self._validate_and_normalize(networks)
        try:
            return await self._org_repo.add_networks(normalized)
        except ValueError as e:
            msg = str(e).lower()
            if "already allowed" in msg or "duplicate" in msg:
                # Extract the CIDR from the error message
                raise DuplicateCidrError(networks[0]) from e
            if "too many" in msg:
                raise TooManyNetworksError(20) from e
            raise

    async def remove_network(self, cidr: str) -> list[str]:
        """Remove a CIDR from the allowlist.

        Args:
            cidr: CIDR string to remove (plain IPs auto-normalized).

        Returns:
            The updated list of CIDR strings.

        Raises:
            CidrNotFoundError: If CIDR not in allowlist.
        """
        normalized = _normalize_input(cidr)
        try:
            return await self._org_repo.remove_network(normalized)
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
    def _validate_and_normalize(networks: list[str]) -> list[str]:
        """Validate and normalize a network list.

        Plain IPv4 addresses are automatically converted to /32 CIDR.
        Duplicate detection runs after normalization.

        Args:
            networks: List of CIDR or plain-IPv4 strings.

        Returns:
            A list of normalized, deduplicated CIDR strings.

        Raises:
            InvalidCidrError: If any entry is invalid.
            DuplicateCidrError: If duplicates exist (after normalization).
            TooManyNetworksError: If exceeds max limit.
        """
        if len(networks) > 20:
            raise TooManyNetworksError(20)

        seen: set[str] = set()
        normalized: list[str] = []
        for raw in networks:
            cidr = _normalize_input(raw)
            if cidr in seen:
                raise DuplicateCidrError(raw)
            seen.add(cidr)
            normalized.append(cidr)
        return normalized
