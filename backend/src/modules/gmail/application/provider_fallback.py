"""Privacy-aware provider fallback decisions for AI Automation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderFallbackPolicy:
    """Policy supplied by Organization AI Configuration, not by the model."""

    fallback_provider: str | None = None
    same_privacy_boundary: bool = False
    quality_floor_met: bool = False

    def allows(self) -> bool:
        """Allow fallback only when both privacy and quality guardrails hold."""
        return bool(
            self.fallback_provider and self.same_privacy_boundary and self.quality_floor_met
        )
