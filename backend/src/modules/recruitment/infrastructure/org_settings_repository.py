"""Repository for Organization settings (single-row company configuration).

Provides async access to the single ``OrganizationSettings`` row, which holds
the canonical IANA timezone used to interpret and render interview times on
Google Calendar events. On first access the configured default timezone is
seeded and persisted, enforcing single-row semantics. Timezone strings are
validated against ``zoneinfo.available_timezones()`` whenever they are written.

Requirements: 11.1, 11.2
"""

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
