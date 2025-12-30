"""
Unified model registry for all supported LLM models.

This module serves as the single source of truth for:
- Model identifiers and enums
- Pricing information
- Model capabilities and limits
- Provider mappings

All model-related configuration should be maintained here to ensure
consistency across the framework.
"""

from enum import Enum
from typing import Any, Dict, Optional


class Engines(str, Enum):
    """Enum class representing different AI model engines."""

    # OpenAI GPT-3.5 Models
    GPT35TURBO = "gpt-3.5-turbo"
    GPT35TURBO_16K = "gpt-3.5-turbo-16k"
    GPT35TURBO_0125 = "gpt-3.5-turbo-0125"
    GPT35TURBO_INSTRUCT = "gpt-3.5-turbo-instruct"

    # OpenAI GPT-4 Models
    GPT4 = "gpt-4"
    GPT41 = "gpt-4.1"
    GPT4_0613 = "gpt-4-0613"
    GPT4_32K = "gpt-4-32k"
    GPT4_32K_0613 = "gpt-4-32k-0613"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"

    # OpenAI GPT-5.2 Models (Released Dec 11, 2025)
    GPT52_INSTANT = "gpt-5.2-instant"
    GPT52_THINKING = "gpt-5.2-thinking"
    GPT52_PRO = "gpt-5.2-pro"

    # Anthropic Claude 3 Haiku Models
    CLAUDE3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE35_HAIKU = "claude-3-5-haiku-latest"
    CLAUDE45_HAIKU = "claude-haiku-4-5-20251015"

    # Anthropic Claude Sonnet Models
    CLAUDE37_SONNET_20250219 = "claude-3-7-sonnet-20250219"
    CLAUDE4_SONNET = "claude-sonnet-4-20250514"
    CLAUDE45_SONNET = "claude-sonnet-4-5-20250929"

    # Anthropic Claude Opus Models
    CLAUDE4_OPUS = "claude-opus-4-20250514"
    CLAUDE41_OPUS = "claude-opus-4-1-20250805"
    CLAUDE45_OPUS = "claude-opus-4-5-20251101"

    # Google Gemini 1.5 Models
    GEMINI15_PRO = "gemini-1.5-pro"
    GEMINI15_FLASH = "gemini-1.5-flash"

    # Google Gemini 2.0 Models
    GEMINI20_FLASH = "gemini-2.0-flash"

    # Google Gemini 2.5 Models
    GEMINI25_FLASH = "gemini-2.5-flash"
    GEMINI25_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI25_PRO = "gemini-2.5-pro"

    # Google Gemini 3 Models (Released Nov-Dec 2025)
    GEMINI3_FLASH = "gemini-3-flash-preview"
    GEMINI3_PRO = "gemini-3-pro-preview"

    @staticmethod
    def get(name: str) -> Optional["Engines"]:
        """Retrieve an Engines enum member by its string value."""
        for engine in Engines:
            if engine.value == name:
                return engine
        return None

    def get_info(self) -> dict:
        """Get complete information about this model."""
        return MODEL_REGISTRY.get(
            self.value,
            {
                "provider": "unknown",
                "intelligence": 2,
                "max_tokens": 4096,
                "cost_input": 0.0,
                "cost_output": 0.0,
            },
        )


# Unified model registry with all model information
# Intelligence: 1 star (fast/cheap), 2 stars (balanced), 3 stars (most capable)
# Costs are per 1 million tokens (USD)
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Anthropic Claude Models
    "claude-3-haiku-20240307": {
        "provider": "anthropic",
        "intelligence": 1,
        "max_tokens": 4096,
        "cost_input": 0.25,
        "cost_output": 1.25,
    },
    "claude-3-5-haiku-latest": {
        "provider": "anthropic",
        "intelligence": 1,
        "max_tokens": 8192,
        "cost_input": 0.80,
        "cost_output": 4.00,
    },
    "claude-haiku-4-5-20251015": {
        "provider": "anthropic",
        "intelligence": 1,
        "max_tokens": 64000,
        "cost_input": 1.00,
        "cost_output": 5.00,
    },
    "claude-3-7-sonnet-20250219": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 3.00,
        "cost_output": 15.00,
    },
    "claude-sonnet-4-20250514": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 64000,
        "cost_input": 3.00,
        "cost_output": 15.00,
    },
    "claude-sonnet-4-5-20250929": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 64000,
        "cost_input": 3.00,
        "cost_output": 15.00,
    },
    "claude-opus-4-20250514": {
        "provider": "anthropic",
        "intelligence": 3,
        "max_tokens": 64000,
        "cost_input": 15.00,
        "cost_output": 75.00,
    },
    "claude-opus-4-1-20250805": {
        "provider": "anthropic",
        "intelligence": 3,
        "max_tokens": 64000,
        "cost_input": 15.00,
        "cost_output": 75.00,
    },
    "claude-opus-4-5-20251101": {
        "provider": "anthropic",
        "intelligence": 3,
        "max_tokens": 64000,
        "cost_input": 5.00,
        "cost_output": 25.00,
    },
    # Legacy Anthropic models (for backward compatibility)
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 3.00,
        "cost_output": 15.00,
    },
    "claude-3-5-sonnet-latest": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 3.00,
        "cost_output": 15.00,
    },
    "claude-3-5-haiku-20241022": {
        "provider": "anthropic",
        "intelligence": 1,
        "max_tokens": 8192,
        "cost_input": 0.80,
        "cost_output": 4.00,
    },
    "claude-3-opus-20240229": {
        "provider": "anthropic",
        "intelligence": 3,
        "max_tokens": 4096,
        "cost_input": 15.00,
        "cost_output": 75.00,
    },
    "claude-3-sonnet-20240229": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 4096,
        "cost_input": 3.00,
        "cost_output": 15.00,
    },
    "claude-opus-4-latest": {
        "provider": "anthropic",
        "intelligence": 3,
        "max_tokens": 64000,
        "cost_input": 20.00,
        "cost_output": 80.00,
    },
    "claude-sonnet-4-latest": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 64000,
        "cost_input": 5.00,
        "cost_output": 25.00,
    },
    "claude-3-7-sonnet-latest": {
        "provider": "anthropic",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 3.00,
        "cost_output": 15.00,
    },
    # OpenAI GPT Models
    "gpt-3.5-turbo": {
        "provider": "openai",
        "intelligence": 1,
        "max_tokens": 4096,
        "cost_input": 0.50,
        "cost_output": 1.50,
    },
    "gpt-3.5-turbo-16k": {
        "provider": "openai",
        "intelligence": 1,
        "max_tokens": 16384,
        "cost_input": 3.00,
        "cost_output": 4.00,
    },
    "gpt-3.5-turbo-0125": {
        "provider": "openai",
        "intelligence": 1,
        "max_tokens": 4096,
        "cost_input": 0.50,
        "cost_output": 1.50,
    },
    "gpt-3.5-turbo-instruct": {
        "provider": "openai",
        "intelligence": 1,
        "max_tokens": 4096,
        "cost_input": 1.50,
        "cost_output": 2.00,
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "intelligence": 1,
        "max_tokens": 16384,
        "cost_input": 0.15,
        "cost_output": 0.60,
    },
    "gpt-4": {
        "provider": "openai",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 30.00,
        "cost_output": 60.00,
    },
    "gpt-4.1": {
        "provider": "openai",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 30.00,
        "cost_output": 60.00,
    },
    "gpt-4-0613": {
        "provider": "openai",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 30.00,
        "cost_output": 60.00,
    },
    "gpt-4o": {
        "provider": "openai",
        "intelligence": 2,
        "max_tokens": 16384,
        "cost_input": 2.50,
        "cost_output": 10.00,
    },
    "gpt-4-32k": {
        "provider": "openai",
        "intelligence": 3,
        "max_tokens": 32768,
        "cost_input": 60.00,
        "cost_output": 120.00,
    },
    "gpt-4-32k-0613": {
        "provider": "openai",
        "intelligence": 3,
        "max_tokens": 32768,
        "cost_input": 60.00,
        "cost_output": 120.00,
    },
    "gpt-5.2-instant": {
        "provider": "openai",
        "intelligence": 2,
        "max_tokens": 128000,
        "cost_input": 1.75,
        "cost_output": 14.00,
    },
    "gpt-5.2-thinking": {
        "provider": "openai",
        "intelligence": 3,
        "max_tokens": 128000,
        "cost_input": 1.75,
        "cost_output": 14.00,
    },
    "gpt-5.2-pro": {
        "provider": "openai",
        "intelligence": 3,
        "max_tokens": 128000,
        "cost_input": 1.75,
        "cost_output": 14.00,
    },
    # Legacy OpenAI models (for backward compatibility)
    "gpt-4-turbo": {
        "provider": "openai",
        "intelligence": 2,
        "max_tokens": 128000,
        "cost_input": 10.00,
        "cost_output": 30.00,
    },
    # Google Gemini Models
    "gemini-1.5-pro": {
        "provider": "google",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 1.25,
        "cost_output": 10.00,
    },
    "gemini-1.5-flash": {
        "provider": "google",
        "intelligence": 1,
        "max_tokens": 8192,
        "cost_input": 0.075,
        "cost_output": 0.30,
    },
    "gemini-2.0-flash": {
        "provider": "google",
        "intelligence": 1,
        "max_tokens": 8192,
        "cost_input": 0.10,
        "cost_output": 0.40,
    },
    "gemini-2.5-flash": {
        "provider": "google",
        "intelligence": 1,
        "max_tokens": 8192,
        "cost_input": 0.15,
        "cost_output": 0.60,
    },
    "gemini-2.5-flash-lite": {
        "provider": "google",
        "intelligence": 1,
        "max_tokens": 8192,
        "cost_input": 0.10,
        "cost_output": 0.40,
    },
    "gemini-2.5-pro": {
        "provider": "google",
        "intelligence": 2,
        "max_tokens": 65536,
        "cost_input": 1.25,  # For ≤200K context
        "cost_output": 10.00,  # For ≤200K context
        # Note: 2x pricing for >200K context
    },
    "gemini-3-flash-preview": {
        "provider": "google",
        "intelligence": 1,
        "max_tokens": 64000,
        "cost_input": 0.50,
        "cost_output": 3.00,
    },
    "gemini-3-pro-preview": {
        "provider": "google",
        "intelligence": 3,
        "max_tokens": 64000,
        "cost_input": 2.00,  # For ≤200K context
        "cost_output": 12.00,  # For ≤200K context
        # Note: 2x pricing for >200K context
    },
    # Legacy Google models (for backward compatibility)
    "gemini-2.5-pro-long": {
        "provider": "google",
        "intelligence": 2,
        "max_tokens": 65536,
        "cost_input": 2.50,  # >200K context pricing
        "cost_output": 15.00,  # >200K context pricing
    },
    "gemini-2.0-pro": {
        "provider": "google",
        "intelligence": 2,
        "max_tokens": 8192,
        "cost_input": 1.25,
        "cost_output": 10.00,
    },
}

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
        model: Model name or Engines enum value

    Returns:
        Dictionary with model information or None if not found
    """
    if isinstance(model, Engines):
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
