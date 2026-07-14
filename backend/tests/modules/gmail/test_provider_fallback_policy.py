from src.modules.gmail.application.provider_fallback import ProviderFallbackPolicy


def test_fallback_requires_privacy_and_quality_compatibility() -> None:
    assert not ProviderFallbackPolicy(
        "backup", same_privacy_boundary=False, quality_floor_met=True
    ).allows()
    assert not ProviderFallbackPolicy(
        "backup", same_privacy_boundary=True, quality_floor_met=False
    ).allows()
    assert ProviderFallbackPolicy(
        "backup", same_privacy_boundary=True, quality_floor_met=True
    ).allows()
    assert not ProviderFallbackPolicy(
        None, same_privacy_boundary=True, quality_floor_met=True
    ).allows()
