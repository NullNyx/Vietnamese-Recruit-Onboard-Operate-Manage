import pytest

from src.modules.attendance.api.router import get_client_ip


class MockClient:
    def __init__(self, host):
        self.host = host


class MockRequest:
    def __init__(self, headers, client_host):
        self.headers = headers
        self.client = MockClient(client_host)


@pytest.mark.asyncio
async def test_get_client_ip_no_forwarded():
    req = MockRequest({}, "192.168.1.1")
    assert await get_client_ip(req) == "192.168.1.1"


@pytest.mark.asyncio
async def test_get_client_ip_spoofed():
    # Trusted proxy 127.0.0.1 passes X-Forwarded-For: "spoofed_ip, real_ip"
    req = MockRequest({"x-forwarded-for": "1.2.3.4, 203.0.113.1"}, "127.0.0.1")
    assert await get_client_ip(req) == "203.0.113.1"


@pytest.mark.asyncio
async def test_get_client_ip_untrusted_proxy():
    # Untrusted proxy, should ignore X-Forwarded-For
    req = MockRequest({"x-forwarded-for": "1.2.3.4, 203.0.113.1"}, "192.168.1.100")
    assert await get_client_ip(req) == "192.168.1.100"


@pytest.mark.asyncio
async def test_get_client_ip_multiple_proxies():
    # Trusted proxy 127.0.0.1, real IP is 203.0.113.1, spoofed is 1.2.3.4
    req = MockRequest({"x-forwarded-for": "1.2.3.4, 203.0.113.1, ::1"}, "127.0.0.1")
    assert await get_client_ip(req) == "203.0.113.1"


@pytest.mark.asyncio
async def test_get_client_ip_all_trusted():
    req = MockRequest({"x-forwarded-for": "127.0.0.1, ::1"}, "127.0.0.1")
    assert await get_client_ip(req) == "127.0.0.1"
