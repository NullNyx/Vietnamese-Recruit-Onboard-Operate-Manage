"""Value objects for Attendance network configuration."""

import ipaddress
from dataclasses import dataclass

from src.modules.attendance.domain.exceptions import InvalidCidrError


MAX_NETWORKS = 20


@dataclass(frozen=True)
class CidrRange:
    """Represents a CIDR network range for office network allowlist.

    Validates and stores a CIDR notation (e.g., "192.168.1.0/24").
    IPv4 only for MVP - IPv6 is out of scope per ADR-0010.

    Attributes:
        cidr: The CIDR notation string (e.g., "192.168.1.0/24").
        network: The validated ipaddress.Network object.
    """

    cidr: str
    network: ipaddress.IPv4Network

    def __post_init__(self) -> None:
        # Normalize the CIDR string
        object.__setattr__(self, 'cidr', str(self.network))

    @classmethod
    def create(cls, cidr: str) -> "CidrRange":
        """Create a CidrRange from a CIDR string.

        Args:
            cidr: CIDR notation (e.g., "192.168.1.0/24" or "10.0.0.1/32").

        Returns:
            A validated CidrRange instance.

        Raises:
            InvalidCidrError: If the CIDR format is invalid.
        """
        normalized = cidr.strip()
        try:
            net = ipaddress.ip_network(normalized, strict=False)
        except ValueError as e:
            raise InvalidCidrError(cidr) from e

        # IPv4 only for MVP
        if isinstance(net, ipaddress.IPv6Network):
            raise InvalidCidrError(cidr)

        return cls(cidr=str(net), network=net)

    def contains(self, ip: str) -> bool:
        """Check if an IP address is within this CIDR range.

        Args:
            ip: IP address string to check.

        Returns:
            True if the IP is within the network range, False otherwise.
        """
        try:
            addr = ipaddress.ip_address(ip)
            return addr in self.network
        except ValueError:
            return False

    def __str__(self) -> str:
        return self.cidr


@dataclass
class AttendanceNetworkConfig:
    """Configuration for office network allowlist.

    Contains a list of allowed CIDR ranges for attendance check-in/out.
    If the list is empty, all IPs are allowed (no gate).

    Attributes:
        networks: List of CidrRange objects.
    """

    networks: list[CidrRange]

    @classmethod
    def from_cidr_strings(cls, cidrs: list[str]) -> "AttendanceNetworkConfig":
        """Create config from a list of CIDR strings.

        Args:
            cidrs: List of CIDR notation strings.

        Returns:
            An AttendanceNetworkConfig instance.

        Raises:
            InvalidCidrError: If any CIDR is invalid.
        """
        networks = [CidrRange.create(c) for c in cidrs]
        return cls(networks=networks)

    @classmethod
    def empty(cls) -> "AttendanceNetworkConfig":
        """Create an empty config (allows all IPs)."""
        return cls(networks=[])

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if an IP is allowed based on this config.

        Empty config means allow all (per ADR-0010 behavior).

        Args:
            ip: IP address string to check.

        Returns:
            True if the IP is allowed, False otherwise.
        """
        if not self.networks:
            return True

        for network in self.networks:
            if network.contains(ip):
                return True
        return False

    def to_cidr_strings(self) -> list[str]:
        """Convert config to list of CIDR strings."""
        return [str(n) for n in self.networks]

    def __len__(self) -> int:
        return len(self.networks)

    def __bool__(self) -> bool:
        return bool(self.networks)
