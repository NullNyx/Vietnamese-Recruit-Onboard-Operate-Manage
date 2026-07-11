"""Unit tests for DomainGateService.

Tests the email domain gating logic that controls whether a user's
email domain is permitted by the Organization's allowed_domains list.
"""

from __future__ import annotations

import pytest

from src.modules.identity.application.domain_gate_service import DomainGateService


class FakeOrgSettingsRepo:
    """Minimal fake repository for DomainGateService tests."""

    def __init__(self, allowed_domains: list[str] | None = None) -> None:
        self._domains = allowed_domains or []

    async def get_allowed_domains(self) -> list[str]:
        return list(self._domains)


@pytest.fixture
def empty_repo() -> FakeOrgSettingsRepo:
    """Repository returning an empty allowed_domains list."""
    return FakeOrgSettingsRepo(allowed_domains=[])


@pytest.fixture
def restricted_repo() -> FakeOrgSettingsRepo:
    """Repository returning a restricted allowed_domains list."""
    return FakeOrgSettingsRepo(allowed_domains=["company.vn", "subsidiary.vn"])


@pytest.mark.asyncio
async def test_empty_list_allows_all(empty_repo: FakeOrgSettingsRepo) -> None:
    """When allowed_domains is empty, all emails should pass."""
    service = DomainGateService(org_settings_repository=empty_repo)
    assert await service.is_email_allowed("user@any-domain.com") is True
    assert await service.is_email_allowed("admin@gmail.com") is True
    assert await service.is_email_allowed("test@outlook.vn") is True


@pytest.mark.asyncio
async def test_matching_domain_passes(restricted_repo: FakeOrgSettingsRepo) -> None:
    """Emails with a matching domain should pass."""
    service = DomainGateService(org_settings_repository=restricted_repo)
    assert await service.is_email_allowed("user@company.vn") is True
    assert await service.is_email_allowed("hr@subsidiary.vn") is True


@pytest.mark.asyncio
async def test_non_matching_domain_blocked(restricted_repo: FakeOrgSettingsRepo) -> None:
    """Emails with a non-matching domain should be blocked."""
    service = DomainGateService(org_settings_repository=restricted_repo)
    assert await service.is_email_allowed("user@gmail.com") is False
    assert await service.is_email_allowed("test@other.vn") is False


@pytest.mark.asyncio
async def test_case_insensitive(restricted_repo: FakeOrgSettingsRepo) -> None:
    """Domain matching should be case-insensitive."""
    service = DomainGateService(org_settings_repository=restricted_repo)
    assert await service.is_email_allowed("User@Company.VN") is True
    assert await service.is_email_allowed("HR@SUBSIDIARY.VN") is True
    assert await service.is_email_allowed("test@GMAIL.COM") is False


@pytest.mark.asyncio
async def test_malformed_email_no_at(restricted_repo: FakeOrgSettingsRepo) -> None:
    """Emails without @ should be blocked."""
    service = DomainGateService(org_settings_repository=restricted_repo)
    assert await service.is_email_allowed("invalid-email") is False
    assert await service.is_email_allowed("") is False
