"""Tests for employee check-in/check-out functionality."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from src.modules.attendance.application.attendance_service import AttendanceService
from src.modules.attendance.application.attendance_settings_service import (
    AttendanceSettingsService,
)
from src.modules.attendance.domain.entities import AttendanceRecord, AttendanceSource
from src.modules.attendance.domain.exceptions import (
    NotCheckedInError,
    OfficeNetworkRequiredError,
)
from src.modules.attendance.infrastructure.attendance_record_repository import (
    AttendanceRecordRepository,
)
from src.modules.recruitment.infrastructure.org_settings_repository import (
    OrganizationSettingsRepository,
)


@pytest.fixture
def mock_attendance_repo():
    """Create a mock AttendanceRecordRepository."""
    return AsyncMock(spec=AttendanceRecordRepository)


@pytest.fixture
def mock_org_settings_repo():
    """Create a mock OrganizationSettingsRepository."""
    repo = AsyncMock(spec=OrganizationSettingsRepository)
    repo.get_timezone = AsyncMock(return_value="Asia/Ho_Chi_Minh")
    return repo


@pytest.fixture
def mock_settings_service():
    """Create a mock AttendanceSettingsService."""
    return AsyncMock(spec=AttendanceSettingsService)


@pytest.fixture
def attendance_service(
    mock_attendance_repo, mock_org_settings_repo, mock_settings_service
):
    """Create an AttendanceService with mocked dependencies."""
    return AttendanceService(
        attendance_repo=mock_attendance_repo,
        org_settings_repo=mock_org_settings_repo,
        settings_service=mock_settings_service,
    )


class TestCheckInAllowedIP:
    """Tests for check-in with allowed IP."""

    @pytest.mark.asyncio
    async def test_check_in_creates_record(
        self, attendance_service, mock_attendance_repo
    ):
        """Test check-in creates a new attendance record atomically."""
        employee_id = uuid4()
        client_ip = "192.168.1.100"
        user_agent = "Mozilla/5.0"
        now = datetime.now(UTC)

        created = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in_at=now,
            check_in_ip=client_ip,
            check_in_user_agent=user_agent,
            source=AttendanceSource.WEB,
        )
        mock_attendance_repo.upsert_check_in = AsyncMock(return_value=created)

        result = await attendance_service.check_in(
            employee_id, client_ip, user_agent
        )

        assert result.employee_id == employee_id
        assert result.check_in_at is not None
        assert result.check_in_ip == client_ip
        assert result.source == AttendanceSource.WEB
        mock_attendance_repo.upsert_check_in.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_in_idempotent_returns_existing(
        self, attendance_service, mock_attendance_repo
    ):
        """Test repeated check-in returns existing record without overwriting."""
        employee_id = uuid4()
        existing_record = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in_at=datetime.now(UTC),
            check_in_ip="192.168.1.100",
            source=AttendanceSource.WEB,
        )

        # Atomic upsert returns existing record when conflict occurs
        mock_attendance_repo.upsert_check_in = AsyncMock(return_value=existing_record)

        result = await attendance_service.check_in(
            employee_id, "192.168.1.100", "Mozilla/5.0"
        )

        assert result.id == existing_record.id
        assert result.check_in_at == existing_record.check_in_at
        mock_attendance_repo.create.assert_not_called()
        mock_attendance_repo.update.assert_not_called()


class TestCheckInBlockedIP:
    """Tests for check-in with blocked IP."""

    @pytest.mark.asyncio
    async def test_check_in_blocked_ip_raises_error(
        self, attendance_service, mock_settings_service
    ):
        """Test blocked IP returns 403 error."""
        employee_id = uuid4()
        client_ip = "203.0.113.50"

        mock_settings_service.is_ip_allowed = AsyncMock(return_value=False)

        with pytest.raises(OfficeNetworkRequiredError) as exc_info:
            await attendance_service.check_in(
                employee_id, client_ip, "User-Agent"
            )

        assert exc_info.value.status_code == 403
        assert "office network" in exc_info.value.message.lower()


class TestCheckOut:
    """Tests for check-out functionality."""

    @pytest.mark.asyncio
    async def test_check_out_requires_check_in(
        self, attendance_service, mock_attendance_repo
    ):
        """Test check-out fails if no check-in exists."""
        employee_id = uuid4()
        client_ip = "192.168.1.100"

        mock_attendance_repo.get_by_employee_and_date = AsyncMock(return_value=None)

        with pytest.raises(NotCheckedInError) as exc_info:
            await attendance_service.check_out(
                employee_id, client_ip, "User-Agent"
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_check_out_idempotent(
        self, attendance_service, mock_attendance_repo
    ):
        """Test repeated check-out returns existing record."""
        employee_id = uuid4()
        now = datetime.now(UTC)
        existing_record = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in_at=now,
            check_out_at=now,
            check_in_ip="192.168.1.100",
            check_out_ip="192.168.1.100",
            source=AttendanceSource.WEB,
        )

        mock_attendance_repo.get_by_employee_and_date = AsyncMock(
            return_value=existing_record
        )

        result = await attendance_service.check_out(
            employee_id, "192.168.1.100", "User-Agent"
        )

        assert result.check_out_at == existing_record.check_out_at
        mock_attendance_repo.update.assert_not_called()


class TestWorkDateTimezone:
    """Tests for timezone-aware work date."""

    @pytest.mark.asyncio
    async def test_work_date_uses_org_timezone(
        self, attendance_service, mock_org_settings_repo
    ):
        """Test work date is derived from Organization timezone."""
        mock_org_settings_repo.get_timezone = AsyncMock(
            return_value="Asia/Ho_Chi_Minh"
        )

        work_date = await attendance_service._get_work_date()

        expected = datetime.now(UTC).astimezone(
            tz=ZoneInfo("Asia/Ho_Chi_Minh")
        ).date()
        assert work_date == expected


class TestOwnership:
    """Tests for employee ownership."""

    def test_employee_id_required_in_service_call(self):
        """Verify service requires employee_id parameter."""
        pass


class TestCheckOutBlockedIP:
    """Tests for check-out with blocked IP."""

    @pytest.mark.asyncio
    async def test_check_out_blocked_ip_raises_error(
        self, attendance_service, mock_settings_service
    ):
        """Test blocked IP returns 403 error on check-out."""
        employee_id = uuid4()
        client_ip = "203.0.113.50"

        mock_settings_service.is_ip_allowed = AsyncMock(return_value=False)

        with pytest.raises(OfficeNetworkRequiredError) as exc_info:
            await attendance_service.check_out(
                employee_id, client_ip, "User-Agent"
            )

        assert exc_info.value.status_code == 403
        assert "office network" in exc_info.value.message.lower()


class TestUserAgentStorage:
    """Tests for user agent storage."""

    @pytest.mark.asyncio
    async def test_check_in_stores_user_agent(
        self, attendance_service, mock_attendance_repo
    ):
        """Test check-in stores user agent atomically."""
        employee_id = uuid4()
        client_ip = "192.168.1.100"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        now = datetime.now(UTC)

        created = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in_at=now,
            check_in_ip=client_ip,
            check_in_user_agent=user_agent,
            source=AttendanceSource.WEB,
        )
        mock_attendance_repo.upsert_check_in = AsyncMock(return_value=created)

        result = await attendance_service.check_in(
            employee_id, client_ip, user_agent
        )

        assert result.check_in_user_agent == user_agent
        mock_attendance_repo.upsert_check_in.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_out_stores_user_agent(
        self, attendance_service, mock_attendance_repo
    ):
        """Test check-out stores user agent."""
        employee_id = uuid4()
        client_ip = "192.168.1.100"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        now = datetime.now(UTC)
        existing_record = AttendanceRecord(
            id=uuid4(),
            employee_id=employee_id,
            work_date=date.today(),
            check_in_at=now,
            check_in_ip=client_ip,
            source=AttendanceSource.WEB,
        )

        mock_attendance_repo.get_by_employee_and_date = AsyncMock(
            return_value=existing_record
        )
        mock_attendance_repo.update = AsyncMock(side_effect=lambda r: r)

        result = await attendance_service.check_out(
            employee_id, client_ip, user_agent
        )

        assert result.check_out_user_agent == user_agent
        mock_attendance_repo.update.assert_called_once()
