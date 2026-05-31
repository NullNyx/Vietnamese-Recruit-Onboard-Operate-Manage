"""Onboarding module configuration.

Loads onboarding module settings from environment variables with the
ONBOARDING_ prefix. The shared database and Redis connection URLs are not
redefined here; instead they are reused from the identity module's
``AuthSettings`` (the ``AUTH_DATABASE_URL`` / ``AUTH_REDIS_URL`` env vars) so
there is a single source of truth for the shared infrastructure connections.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.modules.identity.container import get_settings as get_auth_settings


class OnboardingSettings(BaseSettings):
    """Onboarding module configuration loaded from environment variables.

    Module-specific settings are prefixed with ``ONBOARDING_``. For example,
    ``list_page_size_max`` maps to ``ONBOARDING_LIST_PAGE_SIZE_MAX``.

    The shared ``database_url`` and ``redis_url`` are exposed as read-only
    properties that delegate to the identity module's ``AuthSettings`` (the
    cached ``AUTH_DATABASE_URL`` / ``AUTH_REDIS_URL`` values), keeping a single
    source of truth for the shared PostgreSQL and Redis connections.

    Attributes:
        list_page_size_max: Maximum number of OnboardingProcess records returned
            per list response (the pagination cap, see Requirement 6.2).
    """

    model_config = SettingsConfigDict(env_prefix="ONBOARDING_")

    # Pagination cap for the OnboardingProcess list endpoint (R6.2).
    list_page_size_max: int = Field(default=50, gt=0)

    @property
    def database_url(self) -> str:
        """Shared PostgreSQL connection URL reused from ``AuthSettings``.

        Returns:
            The ``AUTH_DATABASE_URL`` value loaded by the identity module.
        """
        return get_auth_settings().database_url

    @property
    def redis_url(self) -> str:
        """Shared Redis connection URL reused from ``AuthSettings``.

        Returns:
            The ``AUTH_REDIS_URL`` value loaded by the identity module.
        """
        return get_auth_settings().redis_url
