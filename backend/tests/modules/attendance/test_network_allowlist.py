"""Tests for attendance network allowlist."""

import pytest

from src.modules.attendance.domain.exceptions import InvalidCidrError
from src.modules.attendance.domain.value_objects import (
    AttendanceNetworkConfig,
    CidrRange,
)


class TestCidrRange:
    """Tests for CidrRange value object."""

    def test_create_valid_cidr_24(self):
        """Test creating a /24 CIDR."""
        cidr = CidrRange.create("192.168.1.0/24")
        assert str(cidr) == "192.168.1.0/24"

    def test_create_valid_cidr_32(self):
        """Test creating a /32 single IP."""
        cidr = CidrRange.create("10.0.0.1/32")
        assert str(cidr) == "10.0.0.1/32"

    def test_create_normalizes_to_canonical(self):
        """Test that CIDR is normalized to canonical form."""
        cidr = CidrRange.create("192.168.1.0/24")
        assert str(cidr) == "192.168.1.0/24"

    def test_create_invalid_prefix(self):
        """Test that invalid prefix raises error."""
        with pytest.raises(InvalidCidrError):
            CidrRange.create("192.168.1.0/33")

    def test_create_invalid_ip(self):
        """Test that invalid IP raises error."""
        with pytest.raises(InvalidCidrError):
            CidrRange.create("256.1.1.1/24")

    def test_create_ipv6_rejected(self):
        """Test that IPv6 is rejected (MVP only IPv4)."""
        with pytest.raises(InvalidCidrError):
            CidrRange.create("2001:db8::1/32")

    def test_create_invalid_format(self):
        """Test that invalid format raises error."""
        with pytest.raises(InvalidCidrError):
            CidrRange.create("not-a-cidr")

    def test_contains_ip_within_range(self):
        """Test IP within CIDR returns True."""
        cidr = CidrRange.create("192.168.1.0/24")
        assert cidr.contains("192.168.1.50") is True

    def test_contains_ip_outside_range(self):
        """Test IP outside CIDR returns False."""
        cidr = CidrRange.create("192.168.1.0/24")
        assert cidr.contains("192.168.2.1") is False


class TestAttendanceNetworkConfig:
    """Tests for AttendanceNetworkConfig value object."""

    def test_empty_config_allows_all(self):
        """Test that empty config allows all IPs."""
        config = AttendanceNetworkConfig.empty()
        assert config.is_ip_allowed("192.168.1.1") is True
        assert config.is_ip_allowed("10.0.0.1") is True

    def test_single_network_allows_matching_ip(self):
        """Test that config with network allows matching IP."""
        config = AttendanceNetworkConfig.from_cidr_strings(["192.168.1.0/24"])
        assert config.is_ip_allowed("192.168.1.50") is True

    def test_single_network_rejects_non_matching_ip(self):
        """Test that config rejects non-matching IP."""
        config = AttendanceNetworkConfig.from_cidr_strings(["192.168.1.0/24"])
        assert config.is_ip_allowed("192.168.2.1") is False

    def test_multiple_networks(self):
        """Test config with multiple networks."""
        config = AttendanceNetworkConfig.from_cidr_strings([
            "192.168.1.0/24",
            "10.0.0.0/8",
        ])
        assert config.is_ip_allowed("192.168.1.50") is True
        assert config.is_ip_allowed("10.1.2.3") is True
        assert config.is_ip_allowed("172.16.0.1") is False

    def test_to_cidr_strings(self):
        """Test conversion to string list."""
        config = AttendanceNetworkConfig.from_cidr_strings([
            "192.168.1.0/24",
            "10.0.0.0/8",
        ])
        assert config.to_cidr_strings() == ["192.168.1.0/24", "10.0.0.0/8"]

    def test_from_cidr_strings_invalid(self):
        """Test that invalid CIDR in list raises error."""
        with pytest.raises(InvalidCidrError):
            AttendanceNetworkConfig.from_cidr_strings(["192.168.1.0/33"])

    def test_len(self):
        """Test len returns network count."""
        config = AttendanceNetworkConfig.from_cidr_strings([
            "192.168.1.0/24",
            "10.0.0.0/8",
        ])
        assert len(config) == 2

    def test_bool_empty(self):
        """Test bool returns False for empty."""
        config = AttendanceNetworkConfig.empty()
        assert bool(config) is False

    def test_bool_not_empty(self):
        """Test bool returns True for non-empty."""
        config = AttendanceNetworkConfig.from_cidr_strings(["192.168.1.0/24"])
        assert bool(config) is True

    def test_boundary_cidr_32_single_ip(self):
        """Test /32 CIDR allows only exact IP."""
        config = AttendanceNetworkConfig.from_cidr_strings(["192.168.1.100/32"])
        assert config.is_ip_allowed("192.168.1.100") is True
        assert config.is_ip_allowed("192.168.1.101") is False
