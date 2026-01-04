"""
Cost calculation utilities for LLM API usage.

Provides accurate cost tracking for all supported providers (Anthropic, OpenAI, Google)
based on current pricing. Uses the unified model registry for all model information.

This module is critical for monetization strategy and cost tracking.
"""

import logging
from typing import Optional

# Import from the unified model registry
from bots.foundation.model_registry import (
    MODEL_REGISTRY,
    get_model_info,
    get_provider_discounts,
)

logger = logging.getLogger(__name__)


def normalize_provider(provider: str) -> str:
    """Normalize provider name to canonical form.

    Args:
        provider: Provider name (case-insensitive, accepts common aliases)

    Returns:
        Normalized provider name ("anthropic", "openai", or "google")

    Raises:
        ValueError: If provider is not supported or empty
    """
    # Check for empty provider first
    if not provider or not provider.strip():
        raise ValueError("Provider cannot be empty")

    provider_map = {
        "anthropic": "anthropic",
        "claude": "anthropic",
        "openai": "openai",
        "gpt": "openai",
        "google": "google",
        "gemini": "google",
    }

    provider_lower = provider.lower().strip()

    normalized = provider_map.get(provider_lower)
    if normalized is None:
        supported = list(set(provider_map.values()))
        raise ValueError(f"Unsupported provider: {provider}. Supported providers: {supported}")

    return normalized


def normalize_model(provider: str, model: str) -> str:
    """Normalize model name to match registry keys.

    Args:
        provider: Normalized provider name
        model: Raw model name from API response

    Returns:
        Normalized model name that matches MODEL_REGISTRY keys

    Raises:
        ValueError: If model cannot be matched to any known model
    """
    model_lower = model.lower()

    # Direct match
    if model_lower in MODEL_REGISTRY:
        return model_lower

    # Try common variations
    variations = [
        model_lower,
        model_lower.replace(".", "-"),
        model_lower.replace("-", "."),
    ]

    for variant in variations:
        if variant in MODEL_REGISTRY:
            return variant

    # Try to find a match by checking models for this provider
    provider_models = [k for k, v in MODEL_REGISTRY.items() if v.get("provider") == provider]

    for known_model in provider_models:
        if known_model == model_lower:
            return known_model
        # Use separator-aware prefix matching to avoid ambiguous matches
        # (e.g., "gpt-4" should not match "gpt-4o")
        if known_model.startswith(model_lower + "-") or model_lower.startswith(known_model + "-"):
            return known_model

    # Model not found - raise error
    raise ValueError(f"Unknown model: {model} for provider: {provider}. Available models: {provider_models}")


def get_model_pricing(provider: str, model: str) -> dict:
    """Get pricing information for a specific model.

    Args:
        provider: Normalized provider name
        model: Normalized model name

    Returns:
        Dict with 'cost_input' and 'cost_output' pricing per 1M tokens

    Raises:
        ValueError: If model pricing not found
    """
    model_info = get_model_info(model)
    if model_info is None:
        provider_models = [k for k, v in MODEL_REGISTRY.items() if v.get("provider") == provider]
        raise ValueError(f"No pricing data for model: {model} (provider: {provider}). " f"Available models: {provider_models}")

    if model_info.get("provider") != provider:
        raise ValueError(f"Model {model} belongs to provider {model_info.get('provider')}, not {provider}")

    return {
        "input": model_info.get("cost_input", 0.0),
        "output": model_info.get("cost_output", 0.0),
    }


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
        input_tokens: Number of input tokens (non-cached when using new API, total when using deprecated cached_tokens)
        output_tokens: Number of output tokens
        cached_tokens: DEPRECATED - use cache_read_tokens instead. Represents portion of input_tokens that are cached.
                      For backward compatibility with old API where input_tokens included cached tokens.
        cache_creation_tokens: Number of tokens used to create cache (Anthropic prompt caching)
        cache_read_tokens: Number of tokens read from cache (Anthropic prompt caching)
        is_batch: Whether this is a batch API call (50% discount)

    Returns:
        Total cost in USD

    Raises:
        ValueError: If provider or model is invalid

    Examples:
        >>> # Basic usage
        >>> calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1000, 500)
        0.00465

        >>> # With caching (new API)
        >>> calculate_cost("anthropic", "claude-3-5-sonnet-latest",
        ...               input_tokens=1000, output_tokens=500,
        ...               cache_creation_tokens=500, cache_read_tokens=500)
        0.003825

        >>> # With caching (old API - deprecated)
        >>> calculate_cost("anthropic", "claude-3-5-sonnet-latest",
        ...               input_tokens=1500, output_tokens=500,
        ...               cached_tokens=500)
        0.003825

        >>> # Batch API
        >>> calculate_cost("anthropic", "claude-3-5-sonnet-latest",
        ...               1000, 500, is_batch=True)
        0.002325
    """
    # Validate token counts are non-negative
    input_tokens = max(0, input_tokens)
    output_tokens = max(0, output_tokens)
    cached_tokens = max(0, cached_tokens)
    cache_creation_tokens = max(0, cache_creation_tokens)
    cache_read_tokens = max(0, cache_read_tokens)

    # Handle deprecated cached_tokens parameter
    # Old API: input_tokens includes cached tokens, cached_tokens is the portion that's cached
    # New API: input_tokens is non-cached, cache_read_tokens is additional cached tokens
    if cached_tokens > 0 and cache_read_tokens == 0:
        cache_read_tokens = cached_tokens
        # Subtract cached tokens from input_tokens for old API compatibility
        input_tokens = input_tokens - cached_tokens

    # Normalize inputs
    try:
        provider = normalize_provider(provider)
        model = normalize_model(provider, model)  # Fixed: correct argument order
    except ValueError as e:
        logger.error(f"Error normalizing provider/model: {e}")
        raise

    # Get pricing
    try:
        pricing = get_model_pricing(provider, model)
    except ValueError as e:
        logger.error(f"Error getting pricing: {e}")
        raise

    # Calculate base costs (per 1M tokens, convert to actual cost)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    # Add cache costs if applicable
    cache_cost = 0.0
    if cache_creation_tokens > 0 or cache_read_tokens > 0:
        discounts = get_provider_discounts(provider)
        cache_discount = discounts.get("cache_discount", 0.9)  # Default 90% discount

        if cache_creation_tokens > 0:
            # Cache creation costs same as regular input
            cache_cost += (cache_creation_tokens / 1_000_000) * pricing["input"]

        if cache_read_tokens > 0:
            # Cache reads get discount
            cache_cost += (cache_read_tokens / 1_000_000) * pricing["input"] * cache_discount

    # Apply batch discount if applicable
    total_cost = input_cost + output_cost + cache_cost
    if is_batch:
        discounts = get_provider_discounts(provider)
        batch_discount = discounts.get("batch_discount", 0.5)  # Default 50% discount
        total_cost *= batch_discount

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
        >>> # Returns all anthropic models from registry

        >>> info = get_pricing_info("anthropic", "claude-3-5-sonnet-latest")
        >>> info
        {'cost_input': 3.0, 'cost_output': 15.0, ...}
    """
    if provider is None and model is None:
        # Return all models with their pricing
        return MODEL_REGISTRY

    if provider is not None:
        try:
            provider = normalize_provider(provider)
            # Get all models for this provider
            provider_models = {k: v for k, v in MODEL_REGISTRY.items() if v.get("provider") == provider}

            if model is None:
                return provider_models

            # Get specific model pricing
            try:
                model = normalize_model(provider, model)  # Fixed: correct argument order
                return get_model_info(model)
            except ValueError:
                return None

        except ValueError:
            return {} if model is None else None

    # If only model is provided (no provider)
    if model is not None:
        return get_model_info(model)

    return {}


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
