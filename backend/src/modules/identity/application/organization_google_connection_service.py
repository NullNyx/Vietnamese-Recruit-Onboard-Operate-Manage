from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from urllib.parse import urlencode
from uuid import uuid4

import httpx

from src.modules.identity.application.audit_service import AuditService
from src.modules.identity.domain.entities import AuditActionType, OrganizationGoogleConnection, User
from src.modules.identity.domain.exceptions import DomainAccessDeniedError, GoogleAuthError, InvalidStateError
from src.modules.identity.infrastructure.connection_state_repository import OrganizationGoogleConnectionRepository
from src.modules.identity.infrastructure.crypto_utils import CryptoUtils
from src.modules.identity.infrastructure.jwt_utils import JWTUtils
from src.modules.identity.infrastructure.oauth_config_repository import OAuthConfigRepository
from src.modules.identity.infrastructure.oauth_grant_repository import OAuthGrantRepository
from src.modules.recruitment.infrastructure.org_settings_repository import OrganizationSettingsRepository

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
REQUIRED_SCOPES = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
]


@dataclass
class OrganizationGoogleConnectionResponse:
    status: str
    email: str | None = None
    has_secret: bool = False
    redirect_url: str | None = None


class OrganizationGoogleConnectionService:
    def __init__(
        self,
        *,
        connection_repo: OrganizationGoogleConnectionRepository,
        oauth_config_repo: OAuthConfigRepository,
        oauth_grant_repo: OAuthGrantRepository,
        audit_service: AuditService,
        crypto: CryptoUtils,
        state_jwt: JWTUtils,
        org_settings_repo: OrganizationSettingsRepository,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._connection_repo = connection_repo
        self._oauth_config_repo = oauth_config_repo
        self._oauth_grant_repo = oauth_grant_repo
        self._audit_service = audit_service
        self._crypto = crypto
        self._state_jwt = state_jwt
        self._org_settings_repo = org_settings_repo
        self._http_client = http_client

    def _state_hash(self, state: str) -> str:
        return sha256(state.encode("utf-8")).hexdigest()

    async def get_status(self) -> OrganizationGoogleConnectionResponse:
        current = await self._connection_repo.get_singleton()
        if current is None:
            return OrganizationGoogleConnectionResponse(status="disconnected")
        return OrganizationGoogleConnectionResponse(
            status=current.status,
            email=current.email,
            has_secret=bool(current.client_secret_enc),
        )

    async def initiate(self, hr: User) -> OrganizationGoogleConnectionResponse:
        config = await self._oauth_config_repo.get_active()
        if config is None:
            raise GoogleAuthError("Google OAuth config missing")
        state_nonce = str(uuid4())
        session_id = str(getattr(hr, "session_id", hr.id))
        state = self._state_jwt.create_state_token({"nonce": state_nonce, "hr_id": str(hr.id), "session_id": session_id})
        current = await self._connection_repo.get_singleton()
        await self._connection_repo.upsert_singleton(
            OrganizationGoogleConnection(
                status=current.status if current else "disconnected",
                email=current.email if current else None,
                google_sub=current.google_sub if current else None,
                email_domain=current.email_domain if current else None,
                selected_calendar_id=current.selected_calendar_id if current else None,
                credential_format_version=current.credential_format_version if current else 1,
                credential_key_version=current.credential_key_version if current else 1,
                access_token_enc=current.access_token_enc if current else None,
                refresh_token_enc=current.refresh_token_enc if current else None,
                client_secret_enc=current.client_secret_enc if current else None,
                oauth_state_hash=self._state_hash(state),
                oauth_state_nonce=state_nonce,
                oauth_state_session_id=session_id,
                oauth_state_expires_at=datetime.now(UTC) + timedelta(minutes=10),
                token_expires_at=current.token_expires_at if current else None,
                connected_by_user_id=current.connected_by_user_id if current else None,
            )
        )
        params = urlencode(
            {
                "client_id": config.client_id,
                "redirect_uri": config.redirect_uri,
                "response_type": "code",
                "scope": " ".join(REQUIRED_SCOPES),
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
                "include_granted_scopes": "false",
            }
        )
        return OrganizationGoogleConnectionResponse(status="disconnected", redirect_url=f"{GOOGLE_AUTH_URL}?{params}")

    async def callback(self, *, hr: User, state: str, code: str) -> OrganizationGoogleConnectionResponse:
        payload = self._state_jwt.verify_state_token(state)
        current = await self._connection_repo.get_singleton()
        if current is None or current.oauth_state_hash != self._state_hash(state):
            raise InvalidStateError()
        if payload.get("hr_id") != str(hr.id) or payload.get("session_id") != str(getattr(hr, "session_id", hr.id)):
            raise InvalidStateError()
        if current.oauth_state_expires_at and current.oauth_state_expires_at < datetime.now(UTC):
            raise InvalidStateError()
        await self._connection_repo.upsert_singleton(
            OrganizationGoogleConnection(
                status=current.status,
                email=current.email,
                google_sub=current.google_sub,
                email_domain=current.email_domain,
                selected_calendar_id=current.selected_calendar_id,
                credential_format_version=current.credential_format_version,
                credential_key_version=current.credential_key_version,
                access_token_enc=current.access_token_enc,
                refresh_token_enc=current.refresh_token_enc,
                client_secret_enc=current.client_secret_enc,
                oauth_state_hash=None,
                oauth_state_nonce=None,
                oauth_state_session_id=None,
                oauth_state_expires_at=None,
                token_expires_at=current.token_expires_at,
                connected_by_user_id=current.connected_by_user_id,
            )
        )
        config = await self._oauth_config_repo.get_active()
        if config is None:
            raise GoogleAuthError("Google OAuth config missing")
        client_secret = self._crypto.decrypt(config.client_secret_enc)
        token = await self._http_client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": config.client_id,
                "client_secret": client_secret,
                "redirect_uri": config.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token.status_code != 200:
            raise GoogleAuthError("OAuth token exchange failed")
        data = token.json()
        granted = set(str(data.get("scope", "")).split())
        if not set(REQUIRED_SCOPES).issubset(granted):
            raise GoogleAuthError("Missing required Google scopes")
        userinfo = await self._http_client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        if userinfo.status_code != 200:
            raise GoogleAuthError("Google identity verification failed")
        profile = userinfo.json()
        email = profile.get("email")
        hd = profile.get("hd")
        if not email or not hd:
            raise DomainAccessDeniedError()
        domains = await self._org_settings_repo.get_allowed_domains()
        if domains and hd.lower() not in {d.lower() for d in domains}:
            raise DomainAccessDeniedError()
        refresh_token = data.get("refresh_token")
        if current and current.refresh_token_enc and refresh_token is None:
            refresh_token = self._crypto.decrypt(current.refresh_token_enc)
        connection = OrganizationGoogleConnection(
            status="connected",
            email=email,
            google_sub=profile.get("sub"),
            email_domain=hd,
            selected_calendar_id=current.selected_calendar_id if current else None,
            credential_format_version=1,
            credential_key_version=1,
            access_token_enc=self._crypto.encrypt(data["access_token"]),
            refresh_token_enc=self._crypto.encrypt(refresh_token) if refresh_token else current.refresh_token_enc if current else None,
            client_secret_enc=config.client_secret_enc,
            token_expires_at=datetime.now(UTC) + timedelta(seconds=int(data.get("expires_in", 3600))),
            connected_by_user_id=hr.id,
        )
        await self._connection_repo.upsert_singleton(connection)
        await self._audit_service.log_action(
            admin=hr,
            action_type=AuditActionType.ORG_GOOGLE_CONNECT,
            details={"email": email, "result": "connected"},
        )
        return OrganizationGoogleConnectionResponse(status="connected", email=email, has_secret=True)

    async def disconnect(self, hr: User) -> OrganizationGoogleConnectionResponse:
        current = await self._connection_repo.get_singleton()
        if current and current.refresh_token_enc:
            try:
                await self._http_client.post(
                    GOOGLE_REVOKE_URL,
                    data={"token": self._crypto.decrypt(current.refresh_token_enc)},
                )
            except Exception:
                pass
        await self._connection_repo.disconnect()
        await self._audit_service.log_action(
            admin=hr,
            action_type=AuditActionType.ORG_GOOGLE_DISCONNECT,
            details={"result": "disconnected"},
        )
        return OrganizationGoogleConnectionResponse(status="disconnected")
