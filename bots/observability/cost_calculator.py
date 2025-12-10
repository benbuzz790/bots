"""
Cost calculation utilities for LLM API usage.

Provides accurate cost tracking for all supported providers (Anthropic, OpenAI, Google)
based on current pricing as of October 2025. Supports special pricing features like
caching and batch API discounts.

This module is critical for monetization strategy and cost tracking.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pricing data as of October 9, 2025
# All prices in USD per 1 million tokens
PRICING_DATA = {
    "last_updated": "2025-10-09",
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
        "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-opus-4-20250514": {"input": 20.00, "output": 80.00},
        "claude-opus-4-latest": {"input": 20.00, "output": 80.00},
        "claude-sonnet-4-20250514": {"input": 5.00, "output": 25.00},
        "claude-sonnet-4-latest": {"input": 5.00, "output": 25.00},
        "claude-3-7-sonnet-latest": {"input": 3.00, "output": 15.00},
        "claude-sonnet-4-5-20250929": {"input": 5.00, "output": 25.00},
        # Cache discount: 90% savings on cached tokens
        "cache_discount": 0.90,
        # Batch API discount: 50% on both input and output
        "batch_discount": 0.50,
    },
    "openai": {
        "gpt-4o": {"input": 3.00, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-32k": {"input": 60.00, "output": 120.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "gpt-3.5-turbo-16k": {"input": 3.00, "output": 4.00},
        # Cache discount: 50% savings on cached input tokens
        "cache_discount": 0.50,
        # Batch API discount: 50% on both input and output
        "batch_discount": 0.50,
    },
    "google": {
        "gemini-2.5-pro": {"input": 1.25, "output": 10.00},  # ≤200K tokens
        "gemini-2.5-pro-long": {"input": 2.50, "output": 15.00},  # >200K tokens
        "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
        "gemini-2.0-flash": {"input": 0.15, "output": 0.60},
        "gemini-2.0-pro": {"input": 1.25, "output": 10.00},  # Experimental
        "gemini-1.5-pro": {"input": 1.25, "output": 10.00},
        "gemini-1.5-flash": {"input": 0.30, "output": 2.50},
        # Cache discount: 75% savings on cached tokens
        "cache_discount": 0.75,
        # Batch API discount: 50% on both input and output
        "batch_discount": 0.50,
    },
}
pass  # Cache creation premium: 25% markup on cache write tokens


def normalize_provider(provider: str) -> str:
    """Normalize provider name to canonical form.

    Args:
        provider: Provider name (case-insensitive, accepts common aliases)

    Returns:
        Normalized provider name ("anthropic", "openai", or "google")

    Raises:
        ValueError: If provider is not supported
    """
    provider_map = {
        "anthropic": "anthropic",
        "claude": "anthropic",
        "openai": "openai",
        "gpt": "openai",
        "google": "google",
        "gemini": "google",
    }

    provider_lower = provider.lower()

    normalized = provider_map.get(provider_lower)
    if normalized is None:
        supported = list(set(provider_map.values()))
        raise ValueError(f"Unsupported provider: {provider}. Supported providers: {supported}")

    return normalized


def normalize_model(model: str, provider: str) -> str:
    """Normalize model name to match pricing data keys.

    Args:
        model: Model name
        provider: Normalized provider name

    Returns:
        Normalized model name that matches PRICING_DATA keys

    Raises:
        ValueError: If model is empty or invalid
    """
    if not model:
        raise ValueError("Model cannot be empty")

    model_lower = model.lower().strip()

    # Get pricing data for provider
    provider_pricing = PRICING_DATA.get(provider, {})

    # Check for exact match first
    if model_lower in provider_pricing:
        return model_lower

    # Try to find a match by checking if model name contains a known model
    for known_model in provider_pricing.keys():
        if known_model in ["cache_discount", "batch_discount"]:
            continue
        if known_model in model_lower or model_lower in known_model:
            return known_model

    # Model not found - raise error
    available_models = [k for k in provider_pricing.keys() if k not in ["cache_discount", "batch_discount"]]
    raise ValueError(f"Unknown model: {model} for provider: {provider}. Available models: {available_models}")


def get_model_pricing(provider: str, model: str) -> dict:
    """Get pricing information for a specific model.

    Args:
        provider: Normalized provider name
        model: Normalized model name

    Returns:
        Dict with 'input' and 'output' pricing per 1M tokens

    Raises:
        ValueError: If model pricing not found
    """
    provider_pricing = PRICING_DATA.get(provider)
    if provider_pricing is None:
        raise ValueError(f"No pricing data for provider: {provider}")

    model_pricing = provider_pricing.get(model)
    if model_pricing is None or not isinstance(model_pricing, dict) or "input" not in model_pricing:
        # Try to find a fallback model for the provider
        available_models = [k for k in provider_pricing.keys() if k not in ["cache_discount", "batch_discount"]]
        raise ValueError(
            f"No pricing data for model: {model} (provider: {provider}). " f"Available models: {available_models}"
        )

    return model_pricing


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
    is_batch: bool = False,
) -> float:
    """Calculate the cost of an LLM API call in USD.

    This function provides accurate cost calculation for all supported providers,
    including special pricing features like caching and batch API discounts.

    Args:
        provider: Provider name ("anthropic", "openai", "google", or common aliases)
        model: Model name (e.g., "claude-3-5-sonnet-latest", "gpt-4o")
        input_tokens: Number of input tokens (non-cached)
        output_tokens: Number of output tokens
        cached_tokens: DEPRECATED - use cache_read_tokens instead (default: 0)
        cache_creation_tokens: Number of tokens written to cache (charged at premium, default: 0)
        cache_read_tokens: Number of tokens read from cache (charged at discount, default: 0)
        is_batch: Whether this is a batch API request (default: False)

    Returns:
        Cost in USD (float)

    Raises:
        ValueError: If inputs are invalid or provider/model not supported

    Examples:
        >>> calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1000, 500)
        0.0105  # $3/1M input + $15/1M output

        >>> calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1000, 500, cache_read_tokens=500)
        0.00825  # 1000 regular + 500 cached (0.1x) input + 500 output

        >>> calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1000, 500, cache_creation_tokens=500)
        0.012375  # 1000 regular + 500 cache creation (1.25x) input + 500 output
    """
    # Handle deprecated cached_tokens parameter
    if cached_tokens > 0 and cache_read_tokens == 0:
        cache_read_tokens = cached_tokens

    # Input validation
    if input_tokens < 0:
        raise ValueError(f"Token counts cannot be negative: input_tokens={input_tokens}")
    if output_tokens < 0:
        raise ValueError(f"Token counts cannot be negative: output_tokens={output_tokens}")
    if cache_creation_tokens < 0:
        raise ValueError(f"Token counts cannot be negative: cache_creation_tokens={cache_creation_tokens}")
    if cache_read_tokens < 0:
        raise ValueError(f"Token counts cannot be negative: cache_read_tokens={cache_read_tokens}")

    # Normalize inputs
    try:
        provider = normalize_provider(provider)
        model = normalize_model(model, provider)
    except ValueError as e:
        logger.error(f"Error normalizing provider/model: {e}")
        raise

    # Get pricing
    try:
        pricing = get_model_pricing(provider, model)
    except ValueError as e:
        logger.error(f"Error getting pricing: {e}")
        raise

    input_price_per_million = pricing["input"]
    output_price_per_million = pricing["output"]

    # Calculate input cost (regular tokens at full price)
    input_cost = (input_tokens / 1_000_000) * input_price_per_million

    # Calculate cache creation cost (with premium for Anthropic)
    if cache_creation_tokens > 0:
        provider_pricing = PRICING_DATA[provider]
        cache_creation_premium = provider_pricing.get("cache_creation_premium", 1.0)
        cache_creation_price_per_million = input_price_per_million * cache_creation_premium
        cache_creation_cost = (cache_creation_tokens / 1_000_000) * cache_creation_price_per_million
        input_cost += cache_creation_cost

    # Calculate cache read cost (with discount)
    if cache_read_tokens > 0:
        provider_pricing = PRICING_DATA[provider]
        cache_discount = provider_pricing.get("cache_discount", 0.0)
        cached_price_per_million = input_price_per_million * (1 - cache_discount)
        cached_cost = (cache_read_tokens / 1_000_000) * cached_price_per_million
        input_cost += cached_cost

    # Calculate output cost
    output_cost = (output_tokens / 1_000_000) * output_price_per_million

    # Total cost
    total_cost = input_cost + output_cost

    # Apply batch discount if applicable
    if is_batch:
        provider_pricing = PRICING_DATA[provider]
        batch_discount = provider_pricing.get("batch_discount", 0.0)
        total_cost = total_cost * (1 - batch_discount)

    # Validation: warn if cost seems unusually high
    if total_cost > 1.0:
        total_input = input_tokens + cache_creation_tokens + cache_read_tokens
        logger.warning(
            f"Unusually high API cost: ${total_cost:.4f} for " f"{total_input} input + {output_tokens} output tokens"
        )

    return total_cost


def get_pricing_info(provider: Optional[str] = None, model: Optional[str] = None) -> dict:
    """Get pricing information for providers and models.

    Args:
        provider: Optional provider name. If None, returns all pricing data.
        model: Optional model name. If provided, returns pricing for specific model.

    Returns:
        Pricing data dictionary

    Examples:
        >>> info = get_pricing_info("anthropic")
        >>> info["claude-3-5-sonnet-latest"]
        {'input': 3.0, 'output': 15.0}

        >>> info = get_pricing_info("anthropic", "claude-3-5-sonnet-latest")
        >>> info
        {'input': 3.0, 'output': 15.0}
    """
    if provider is None:
        return PRICING_DATA

    try:
        provider = normalize_provider(provider)
        provider_data = PRICING_DATA.get(provider, {})

        if model is None:
            return provider_data

        # Get specific model pricing
        try:
            model = normalize_model(model, provider)
            return get_model_pricing(provider, model)
        except ValueError:
            return None

    except ValueError:
        return {} if model is None else None


def estimate_cost_from_text(
    provider: str,
    model: str,
    input_text: str,
    output_text: str,
    chars_per_token: float = 4.0,
) -> float:
    """Estimate cost from text strings (rough approximation).

    Uses character count / chars_per_token to estimate token count.
    This is a rough approximation - actual tokenization varies by model.

    Args:
        provider: Provider name
        model: Model name
        input_text: Input text string
        output_text: Output text string
        chars_per_token: Average characters per token (default: 4.0)

    Returns:
        Estimated cost in USD

    Note:
        This is an approximation. For accurate costs, use actual token counts
        from API responses.
    """
    if chars_per_token <= 0:
        raise ValueError(f"chars_per_token must be positive: {chars_per_token}")

    input_tokens = int(len(input_text) / chars_per_token)
    output_tokens = int(len(output_text) / chars_per_token)

    return calculate_cost(provider, model, input_tokens, output_tokens)
