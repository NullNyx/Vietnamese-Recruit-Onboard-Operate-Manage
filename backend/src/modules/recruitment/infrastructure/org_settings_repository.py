"""Repository for Organization settings (single-row company configuration).

Provides async access to the single ``OrganizationSettings`` row, which holds
the canonical IANA timezone, allowed email domains, and attendance network
configuration. On first access the configured default timezone is seeded and
persisted, enforcing single-row semantics.

Requirements: 11.1, 11.2
"""

import re
from zoneinfo import available_timezones

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.recruitment.domain.entities import OrganizationSettings
from src.modules.recruitment.infrastructure.config import RecruitmentSettings


class OrganizationSettingsRepository:
    """Handles OrganizationSettings persistence using async SQLAlchemy sessions.

    Enforces single-row semantics: there is at most one settings row for the
    Organization. The configured default timezone is seeded on first access,
    so callers always receive a valid IANA timezone string.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(
        self,
        session: AsyncSession,
        settings: RecruitmentSettings | None = None,
    ) -> None:
        """Initialize the repository with an async database session.

        Args:
            session: An SQLAlchemy AsyncSession instance for database operations.
            settings: Recruitment settings supplying the default timezone. A
                fresh ``RecruitmentSettings`` is loaded from the environment
                when not provided.
        """
        self.session = session
        self._settings = settings or RecruitmentSettings()

    @property
    def default_timezone(self) -> str:
        """Return the configured default IANA timezone for the Organization."""
        return self._settings.default_organization_timezone

    async def get_timezone(self) -> str:
        """Return the Organization's configured IANA timezone.

        Reads the single settings row. When no row exists yet (first access),
        the configured default timezone is validated, seeded, and persisted.

        Returns:
            The IANA timezone string stored for the Organization.

        Raises:
            ValueError: If the configured default timezone is not a valid IANA
                timezone recognized by ``zoneinfo.available_timezones()``.
        """
        settings_row = await self._get_row()
        if settings_row is None:
            settings_row = await self._seed_default()
        return settings_row.timezone

    async def set_timezone(self, timezone: str) -> str:
        """Validate and persist the Organization's IANA timezone.

        Updates the single settings row, creating it first when none exists.

        Args:
            timezone: The IANA timezone string to store for the Organization.

        Returns:
            The persisted IANA timezone string.

        Raises:
            ValueError: If ``timezone`` is not a valid IANA timezone recognized
                by ``zoneinfo.available_timezones()``.
        """
        self._validate_timezone(timezone)
        settings_row = await self._get_row()
        if settings_row is None:
            settings_row = OrganizationSettings(timezone=timezone)
        else:
            settings_row.timezone = timezone
        self.session.add(settings_row)
        await self.session.flush()
        return settings_row.timezone

    async def _get_row(self) -> OrganizationSettings | None:
        """Read the single OrganizationSettings row if it exists.

        Returns:
            The OrganizationSettings entity if present, None otherwise.
        """
        statement = select(OrganizationSettings).limit(1)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def _seed_default(self) -> OrganizationSettings:
        """Create and persist the settings row with the configured default.

        Returns:
            The persisted OrganizationSettings entity.

        Raises:
            ValueError: If the configured default timezone is invalid.
        """
        timezone = self.default_timezone
        self._validate_timezone(timezone)
        settings_row = OrganizationSettings(timezone=timezone)
        self.session.add(settings_row)
        await self.session.flush()
        return settings_row

    # ------------------------------------------------------------------
    # Allowed domains
    # ------------------------------------------------------------------

    _DOMAIN_RE = re.compile(
        r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?\.[a-z0-9]"
        r"([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$"
    )
    _MAX_DOMAINS = 50

    async def get_allowed_domains(self) -> list[str]:
        """Return the Organization's allowed email domains.

        Returns:
            The list of allowed domain strings (lowercase, bare domains
            without ``@`` prefix).  An empty list means no restriction.
        """
        settings_row = await self._get_row()
        if settings_row is None:
            return []
        return list(settings_row.allowed_domains or [])

    async def set_allowed_domains(self, domains: list[str]) -> list[str]:
        """Replace the entire allowed_domains list.

        Args:
            domains: The new list of domain strings.

        Returns:
            The persisted list of domains.

        Raises:
            ValueError: If any domain is invalid or the list exceeds the limit.
        """
        normalized = self._normalize_and_validate_domains(domains)
        settings_row = await self._get_row()
        if settings_row is None:
            settings_row = OrganizationSettings(
                timezone=self.default_timezone,
                allowed_domains=normalized,
            )
        else:
            settings_row.allowed_domains = normalized
        self.session.add(settings_row)
        await self.session.flush()
        return list(settings_row.allowed_domains)

    async def add_domains(self, domains: list[str]) -> list[str]:
        """Add one or more domains to the allowed list (set semantics).

        Args:
            domains: Domains to add.

        Returns:
            The updated full list of allowed domains.

        Raises:
            ValueError: If any domain is invalid, duplicate, or the list
                would exceed the limit.
        """
        new_normalized = self._normalize_and_validate_domains(domains)
        current = await self.get_allowed_domains()
        current_set = set(current)
        duplicates = [d for d in new_normalized if d in current_set]
        if duplicates:
            raise ValueError(f"Domains already allowed: {', '.join(duplicates)}")
        combined = current + new_normalized
        if len(combined) > self._MAX_DOMAINS:
            raise ValueError(
                f"Too many domains (max {self._MAX_DOMAINS}, would have {len(combined)})"
            )
        return await self.set_allowed_domains(combined)

    async def remove_domain(self, domain: str) -> list[str]:
        """Remove a single domain from the allowed list.

        Args:
            domain: The domain string to remove.

        Returns:
            The updated full list of allowed domains.

        Raises:
            ValueError: If the domain is not in the current list.
        """
        normalized = domain.strip().lower()
        current = await self.get_allowed_domains()
        if normalized not in current:
            raise ValueError(f"Domain not found: {normalized}")
        updated = [d for d in current if d != normalized]
        return await self.set_allowed_domains(updated)

    def _normalize_and_validate_domains(self, domains: list[str]) -> list[str]:
        """Normalize and validate a list of domain strings.

        Args:
            domains: Raw domain strings from the caller.

        Returns:
            A deduplicated list of normalized, validated domain strings.

        Raises:
            ValueError: If any domain fails validation or the list exceeds
                the maximum allowed count.
        """
        if len(domains) > self._MAX_DOMAINS:
            raise ValueError(f"Too many domains (max {self._MAX_DOMAINS})")
        normalized: list[str] = []
        seen: set[str] = set()
        for d in domains:
            n = d.strip().lower()
            if not self._DOMAIN_RE.match(n):
                raise ValueError(f"Invalid domain: {d!r}")
            if n in seen:
                raise ValueError(f"Duplicate domain: {d!r}")
            seen.add(n)
            normalized.append(n)
        return normalized


    # ------------------------------------------------------------------
    # Organization name
    # ------------------------------------------------------------------

    async def get_organization_name(self) -> str | None:
        """Return the Organization's name."""
        settings_row = await self._get_row()
        return settings_row.organization_name if settings_row else None

    async def set_organization_name(self, name: str) -> str:
        """Set the Organization's name."""
        settings_row = await self._get_row()
        if settings_row is None:
            from src.modules.recruitment.domain.entities import OrganizationSettings
            settings_row = OrganizationSettings(
                timezone=self.default_timezone, organization_name=name
        else:
            settings_row.organization_name = name
        self.session.add(settings_row)
        await self.session.flush()
        return settings_row.organization_name

    # ------------------------------------------------------------------
    # Setup state management
    # ------------------------------------------------------------------

    async def get_setup_status(self) -> dict:
        """Return the current setup state."""
        settings_row = await self._get_row()
        if settings_row is None:
            return {"setup_completed_at": None, "setup_locked_at": None, "is_locked": False}
        return {
            "setup_completed_at": settings_row.setup_completed_at,
            "setup_locked_at": settings_row.setup_locked_at,
            "is_locked": settings_row.setup_locked_at is not None,
        }

    async def complete_setup(self) -> dict:
        """Mark setup as completed and locked."""
        from datetime import UTC
        now = datetime.now(UTC)
        settings_row = await self._get_row()
        if settings_row is None:
            settings_row = OrganizationSettings(
                timezone=self.default_timezone,
                setup_completed_at=now,
                setup_locked_at=now,
        else:
            settings_row.setup_completed_at = now
            settings_row.setup_locked_at = now
        self.session.add(settings_row)
        await self.session.flush()
        return {
            "setup_completed_at": settings_row.setup_completed_at,
            "setup_locked_at": settings_row.setup_locked_at,
        }

    async def is_setup_locked(self) -> bool:
        """Check if setup is locked."""
        settings_row = await self._get_row()
        return settings_row.setup_locked_at is not None if settings_row else False

    @staticmethod
    def _validate_timezone(timezone: str) -> None:
        """Validate a timezone string against the IANA timezone database.

        Args:
            timezone: The IANA timezone string to validate.

        Raises:
            ValueError: If the timezone is not recognized by zoneinfo.
        """
        if timezone not in available_timezones():
            raise ValueError(f"Invalid timezone: {timezone!r}")

    # ------------------------------------------------------------------
    # Attendance network config
    # ------------------------------------------------------------------

    _MAX_NETWORKS = 20
    _CIDR_RE = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:/(?:[0-9]|[12][0-9]|3[0-2]))?$"
    )

    async def get_attendance_allowed_networks(self) -> list[str]:
        """Return the Organization's allowed attendance IP/CIDR ranges.

        Returns:
            The list of CIDR strings. Empty list means allow all.
        """
        settings_row = await self._get_row()
        if settings_row is None:
            return []
        return list(settings_row.attendance_allowed_networks or [])

    async def set_attendance_allowed_networks(self, networks: list[str]) -> list[str]:
        """Replace the entire attendance_allowed_networks list.

        Args:
            networks: The new list of CIDR strings.

        Returns:
            The persisted list of networks.

        Raises:
            ValueError: If any network is invalid or exceeds the limit.
        """
        normalized = self._normalize_and_validate_networks(networks)
        settings_row = await self._get_row()
        if settings_row is None:
            settings_row = OrganizationSettings(
                timezone=self.default_timezone,
                attendance_allowed_networks=normalized,
            )
        else:
            settings_row.attendance_allowed_networks = normalized
        self.session.add(settings_row)
        await self.session.flush()
        return list(settings_row.attendance_allowed_networks)

    async def add_networks(self, networks: list[str]) -> list[str]:
        """Add one or more CIDRs to the attendance allowlist (set semantics).

        Args:
            networks: CIDRs to add.

        Returns:
            The updated full list of allowed networks.

        Raises:
            ValueError: If any CIDR is invalid, duplicate, or the list
                would exceed the limit.
        """
        new_normalized = self._normalize_and_validate_networks(networks)
        current = await self.get_attendance_allowed_networks()
        current_set = set(current)
        duplicates = [n for n in new_normalized if n in current_set]
        if duplicates:
            raise ValueError(f"Networks already allowed: {', '.join(duplicates)}")
        combined = current + new_normalized
        if len(combined) > self._MAX_NETWORKS:
            raise ValueError(
                f"Too many networks (max {self._MAX_NETWORKS}, would have {len(combined)})"
            )
        return await self.set_attendance_allowed_networks(combined)

    async def remove_network(self, cidr: str) -> list[str]:
        """Remove a single CIDR from the attendance allowlist.

        Args:
            cidr: The CIDR string to remove.

        Returns:
            The updated full list of allowed networks.

        Raises:
            ValueError: If the CIDR is not in the current list.
        """
        normalized = cidr.strip()
        current = await self.get_attendance_allowed_networks()
        if normalized not in current:
            raise ValueError(f"CIDR not found: {normalized}")
        updated = [n for n in current if n != normalized]
        return await self.set_attendance_allowed_networks(updated)

    def _normalize_and_validate_networks(self, networks: list[str]) -> list[str]:
        """Normalize and validate a list of CIDR strings.

        Plain IPv4 addresses (e.g. ``192.168.1.10``) are automatically
        converted to ``/32`` CIDR notation.

        Args:
            networks: Raw CIDR or plain-IPv4 strings from the caller.

        Returns:
            A deduplicated list of normalized, validated CIDR strings.

        Raises:
            ValueError: If any entry fails validation or the list exceeds
                the maximum allowed count.
        """
        import ipaddress as _ip

        if len(networks) > self._MAX_NETWORKS:
            raise ValueError(f"Too many networks (max {self._MAX_NETWORKS})")
        normalized: list[str] = []
        seen: set[str] = set()
        for n in networks:
            nn = n.strip()
            # Try plain IP first → normalize to /32
            try:
                addr = _ip.ip_address(nn)
                nn = f"{addr}/32"
            except ValueError:
                pass
            if not self._CIDR_RE.match(nn):
                raise ValueError(f"Invalid CIDR: {n!r}")
            if nn in seen:
                raise ValueError(f"Duplicate CIDR: {n!r}")
            seen.add(nn)
            normalized.append(nn)
        return normalized
