"""Regression tests for Organization AI Configuration route registration."""

from src.modules.identity.api.admin_router import admin_router


def test_core_organization_ai_config_routes_are_registered() -> None:
    """Both reading and replacing the shared configuration must be reachable."""
    registered = {
        (method, route.path) for route in admin_router.routes for method in (route.methods or set())
    }

    assert ("GET", "/api/admin/organization/ai-config") in registered
    assert ("PUT", "/api/admin/organization/ai-config") in registered
    assert (
        "PUT",
        "/api/admin/organization/ai-config/classification-rollout",
    ) in registered
    assert (
        "GET",
        "/api/admin/organization/ai-config/classification-rollout/telemetry",
    ) in registered
    assert (
        "POST",
        "/api/admin/organization/ai-config/classification-rollout/rollback",
    ) in registered
