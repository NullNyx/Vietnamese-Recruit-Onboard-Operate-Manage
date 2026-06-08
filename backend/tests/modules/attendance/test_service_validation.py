"""Tests for AttendanceSettingsService validation logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.modules.attendance.application.attendance_settings_service import (
    AttendanceSettingsService,
)
from src.modules.attendance.domain.exceptions import (
    DuplicateCidrError,
    InvalidCidrError,
    TooManyNetworksError,
)


class TestAttendanceSettingsService:
    """Tests for AttendanceSettingsService validation."""

    def setup_method(self):
        self.mock_repo = AsyncMock()
        self.service = AttendanceSettingsService(self.mock_repo)

    def test_validate_networks_empty_list(self):
        """Empty list should pass validation."""
        self.service._validate_networks([])

    def test_validate_networks_valid_single(self):
        """Valid single CIDR should pass."""
        self.service._validate_networks(["192.168.1.0/24"])

    def test_validate_networks_valid_multiple(self):
        """Multiple valid CIDRs should pass."""
        self.service._validate_networks(["192.168.1.0/24", "10.0.0.0/8"])

    def test_validate_networks_invalid_format(self):
        """Invalid CIDR should raise error."""
        with pytest.raises(InvalidCidrError):
            self.service._validate_networks(["invalid-cidr"])

    def test_validate_networks_invalid_prefix(self):
        """Invalid prefix /33 should raise error."""
        with pytest.raises(InvalidCidrError):
            self.service._validate_networks(["192.168.1.0/33"])

    def test_validate_networks_invalid_ip(self):
        """Invalid IP should raise error."""
        with pytest.raises(InvalidCidrError):
            self.service._validate_networks(["256.1.1.1/24"])

    def test_validate_networks_too_many(self):
        """More than 20 networks should raise error."""
        networks = [f"10.0.{i}.0/24" for i in range(21)]
        with pytest.raises(TooManyNetworksError):
            self.service._validate_networks(networks)

    def test_validate_networks_exactly_20(self):
        """Exactly 20 networks should pass."""
        networks = [f"10.0.{i}.0/24" for i in range(20)]
        self.service._validate_networks(networks)

    def test_validate_networks_duplicate(self):
        """Duplicate CIDR should raise error."""
        with pytest.raises(DuplicateCidrError):
            self.service._validate_networks(["192.168.1.0/24", "192.168.1.0/24"])

    @pytest.mark.asyncio
    async def test_get_allowed_networks(self):
        """Test getting networks from repo."""
        self.mock_repo.get_attendance_allowed_networks.return_value = ["192.168.1.0/24"]
        result = await self.service.get_allowed_networks()
        assert result == ["192.168.1.0/24"]

    @pytest.mark.asyncio
    async def test_get_allowed_networks_empty(self):
        """Test getting empty networks."""
        self.mock_repo.get_attendance_allowed_networks.return_value = []
        result = await self.service.get_allowed_networks()
        assert result == []

    @pytest.mark.asyncio
    async def test_is_ip_allowed_empty_config(self):
        """Test is_ip_allowed with empty config returns True."""
        self.mock_repo.get_attendance_allowed_networks.return_value = []
        result = await self.service.is_ip_allowed("192.168.1.1")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_ip_allowed_matching_ip(self):
        """Test is_ip_allowed with matching IP returns True."""
        self.mock_repo.get_attendance_allowed_networks.return_value = ["192.168.1.0/24"]
        result = await self.service.is_ip_allowed("192.168.1.50")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_ip_allowed_non_matching_ip(self):
        """Test is_ip_allowed with non-matching IP returns False."""
        self.mock_repo.get_attendance_allowed_networks.return_value = ["192.168.1.0/24"]
        result = await self.service.is_ip_allowed("192.168.2.1")
        assert result is False

    @pytest.mark.asyncio
    async def test_add_networks_calls_repo(self):
        """Test adding networks calls repository."""
        self.mock_repo.add_networks.return_value = ["192.168.1.0/24", "10.0.0.0/8"]
        result = await self.service.add_networks(["192.168.1.0/24", "10.0.0.0/8"])
        self.mock_repo.add_networks.assert_called_once()
        assert len(result) == 2
