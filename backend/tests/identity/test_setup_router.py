"""Unit tests for the setup router."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.modules.identity.api.setup_router import setup_router, get_org_settings_repo
from src.modules.identity.container import get_setup_service


class FakeSetupService:
    def __init__(self, is_valid: bool = True):
        self.is_valid = is_valid

    async def verify_setup_token(self, token: str) -> bool:
        return self.is_valid and token == "VALID-TOKEN"

    async def is_setup_completed(self) -> bool:
        return False

    async def lock_setup(self) -> None:
        self.locked = True


class FakeOrganizationSettingsRepository:
    def __init__(self):
        self.timezone = None
        self.domains = []

    async def set_timezone(self, timezone: str) -> str:
        if timezone == "INVALID":
            raise ValueError("Invalid timezone")
        self.timezone = timezone
        return timezone

    async def set_allowed_domains(self, domains: list[str]) -> list[str]:
        if "INVALID" in domains:
            raise ValueError("Invalid domain")
        self.domains = domains
        return domains


@pytest.fixture
def fake_setup_service() -> FakeSetupService:
    return FakeSetupService()


@pytest.fixture
def fake_org_repo() -> FakeOrganizationSettingsRepository:
    return FakeOrganizationSettingsRepository()


from src.modules.identity.container import get_whitelist_manager, get_oauth_config_manager

class FakeWhitelistManager:
    async def add_entry(self, value: str, admin=None):
        return True

class FakeOAuthConfigManager:
    async def update_config(self, client_id: str, client_secret: str, redirect_uri: str, admin=None):
        return True

@pytest.fixture
def fake_whitelist_manager() -> FakeWhitelistManager:
    return FakeWhitelistManager()

@pytest.fixture
def fake_oauth_manager() -> FakeOAuthConfigManager:
    return FakeOAuthConfigManager()


@pytest.fixture
def app(
    fake_setup_service: FakeSetupService, 
    fake_org_repo: FakeOrganizationSettingsRepository,
    fake_whitelist_manager: FakeWhitelistManager,
    fake_oauth_manager: FakeOAuthConfigManager,
) -> FastAPI:
    app = FastAPI()
    app.include_router(setup_router)

    app.dependency_overrides[get_setup_service] = lambda: fake_setup_service
    app.dependency_overrides[get_org_settings_repo] = lambda: fake_org_repo
    app.dependency_overrides[get_whitelist_manager] = lambda: fake_whitelist_manager
    app.dependency_overrides[get_oauth_config_manager] = lambda: fake_oauth_manager

    return app


@pytest.mark.asyncio
async def test_verify_token_success(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/setup/verify", json={"token": "VALID-TOKEN"})
    
    assert response.status_code == 200
    assert "setup_session" in response.cookies
    assert response.json() == {"message": "Token verified successfully"}


@pytest.mark.asyncio
async def test_verify_token_failure(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/setup/verify", json={"token": "INVALID-TOKEN"})
    
    assert response.status_code == 401
    assert "setup_session" not in response.cookies


@pytest.mark.asyncio
async def test_setup_endpoints_require_session(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/setup/organization", json={"timezone": "Asia/Ho_Chi_Minh"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_setup_organization_success(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    # Using the valid dummy cookie
    async with AsyncClient(transport=transport, base_url="http://test", cookies={"setup_session": "valid_session_dummy"}) as client:
        response = await client.post("/api/setup/organization", json={"timezone": "Asia/Ho_Chi_Minh"})
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_setup_domains_success(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", cookies={"setup_session": "valid_session_dummy"}) as client:
        response = await client.post("/api/setup/domains", json={"domains": ["nullnyx.com"]})
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_setup_whitelist_success(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", cookies={"setup_session": "valid_session_dummy"}) as client:
        response = await client.post("/api/setup/whitelist", json={"emails": ["admin@nullnyx.com"]})
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_setup_oauth_success(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", cookies={"setup_session": "valid_session_dummy"}) as client:
        response = await client.post("/api/setup/oauth", json={"client_id": "id", "client_secret": "secret", "redirect_uri": "http://localhost/callback"})
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_setup_lock_success(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", cookies={"setup_session": "valid_session_dummy"}) as client:
        response = await client.post("/api/setup/lock")
        assert response.status_code == 200
        cookies_header = response.headers.get("set-cookie", "")
        assert "setup_session" in cookies_header
        assert "max-age=0" in cookies_header.lower() or "expires=" in cookies_header.lower()
        assert response.json() == {"message": "System setup is now locked and complete"}
