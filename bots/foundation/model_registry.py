"""Model metadata lookups (pricing, capabilities, provider discounts).

Model data now lives on ``bots.foundation.models.Model``. ``MODEL_REGISTRY``
and ``get_model_info`` are kept for existing callers and are derived from that
enum, so there is a single place to add or change a model.
"""

from typing import Any, Dict, Optional

from bots.foundation.models import Model

# Derived view: {model_id: info_dict}. "Latest" shortcuts are excluded because
# they have no fixed pricing until resolved to a concrete model.
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {m.value: m.get_info() for m in Model if not m.is_latest_shortcut}

# Provider-specific discount configurations
PROVIDER_DISCOUNTS = {
    "anthropic": {
        "cache_discount": 0.90,  # 90% savings on cached tokens
        "batch_discount": 0.50,  # 50% on both input and output
        "cache_creation_premium": 1.25,  # 25% premium for cache creation
    },
    "openai": {
        "cache_discount": 0.50,  # 50% savings on cached input tokens
        "batch_discount": 0.50,  # 50% on both input and output
    },
    "google": {
        "cache_discount": 0.75,  # 75% savings on cached tokens
        "batch_discount": 0.50,  # 50% on both input and output
    },
}


def get_model_info(model: str) -> Optional[Dict[str, Any]]:
    """Get complete information for a model by name.

    Args:
        model: Model ID string or Model member

    Returns:
        Dictionary with model information, or None if not found
    """
    if isinstance(model, Model):
        model = model.value
    return MODEL_REGISTRY.get(model)


def get_provider_discounts(provider: str) -> Dict[str, float]:
    """Get discount configuration for a provider.

    Args:
        provider: Provider name (anthropic, openai, google)

    Returns:
        Dictionary with discount configurations
    """
    return PROVIDER_DISCOUNTS.get(provider, {})
