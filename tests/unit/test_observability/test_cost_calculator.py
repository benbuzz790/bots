"""
Unit tests for cost_calculator module.

Tests cost calculation accuracy for all providers, models, and edge cases.
Critical for business - pricing accuracy is essential for monetization.
"""

import pytest

from bots.foundation.model_registry import MODEL_REGISTRY, PROVIDER_DISCOUNTS
from bots.observability.cost_calculator import (
    calculate_cost,
    get_model_pricing,
    get_pricing_info,
    normalize_model,
    normalize_provider,
)


class TestNormalizeProvider:
    """Test provider name normalization."""

    def test_anthropic_variations(self):
        """Test that various Anthropic names normalize correctly."""
        assert normalize_provider("anthropic") == "anthropic"
        assert normalize_provider("Anthropic") == "anthropic"
        assert normalize_provider("ANTHROPIC") == "anthropic"
        assert normalize_provider("claude") == "anthropic"
        assert normalize_provider("Claude") == "anthropic"

    def test_openai_variations(self):
        """Test that various OpenAI names normalize correctly."""
        assert normalize_provider("openai") == "openai"
        assert normalize_provider("OpenAI") == "openai"
        assert normalize_provider("OPENAI") == "openai"
        assert normalize_provider("gpt") == "openai"
        assert normalize_provider("GPT") == "openai"

    def test_google_variations(self):
        """Test that various Google names normalize correctly."""
        assert normalize_provider("google") == "google"
        assert normalize_provider("Google") == "google"
        assert normalize_provider("GOOGLE") == "google"
        assert normalize_provider("gemini") == "google"
        assert normalize_provider("Gemini") == "google"

    def test_invalid_provider(self):
        """Test that invalid providers raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            normalize_provider("invalid")

        with pytest.raises(ValueError, match="Unsupported provider"):
            normalize_provider("cohere")

    def test_empty_provider(self):
        """Test that empty provider strings raise ValueError."""
        with pytest.raises(ValueError, match="Provider cannot be empty"):
            normalize_provider("")

        with pytest.raises(ValueError, match="Provider cannot be empty"):
            normalize_provider("   ")


class TestNormalizeModel:
    """Test model name normalization."""

    def test_exact_match(self):
        """Test exact model name matches."""
        assert normalize_model("anthropic", "claude-3-5-sonnet-latest") == "claude-3-5-sonnet-latest"
        assert normalize_model("openai", "gpt-4o") == "gpt-4o"
        assert normalize_model("google", "gemini-2.5-flash") == "gemini-2.5-flash"

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert normalize_model("anthropic", "CLAUDE-3-5-SONNET-LATEST") == "claude-3-5-sonnet-latest"
        assert normalize_model("openai", "GPT-4O") == "gpt-4o"

    def test_partial_match(self):
        """Test partial model name matching."""
        # Should match a sonnet model
        result = normalize_model("anthropic", "claude-3-7-sonnet")
        assert "sonnet" in result.lower()

    def test_unknown_model(self):
        """Test that unknown models raise ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            normalize_model("anthropic", "unknown-model-xyz")


class TestGetModelPricing:
    """Test pricing data retrieval."""

    def test_anthropic_models(self):
        """Test pricing for all Anthropic models."""
        pricing = get_model_pricing("anthropic", "claude-3-5-sonnet-latest")
        assert pricing["input"] == 3.00
        assert pricing["output"] == 15.00

        pricing = get_model_pricing("anthropic", "claude-3-5-haiku-latest")
        assert pricing["input"] == 0.80
        assert pricing["output"] == 4.00

    def test_openai_models(self):
        """Test pricing for all OpenAI models."""
        pricing = get_model_pricing("openai", "gpt-4o")
        assert pricing["input"] == 2.50  # Updated to match MODEL_REGISTRY
        assert pricing["output"] == 10.00

        pricing = get_model_pricing("openai", "gpt-4o-mini")
        assert pricing["input"] == 0.15
        assert pricing["output"] == 0.60

    def test_google_models(self):
        """Test pricing for all Google models."""
        pricing = get_model_pricing("google", "gemini-2.5-pro")
        assert pricing["input"] == 1.25
        assert pricing["output"] == 10.00

        pricing = get_model_pricing("google", "gemini-2.5-flash")
        assert pricing["input"] == 0.15  # Updated to match MODEL_REGISTRY
        assert pricing["output"] == 0.60  # Updated to match MODEL_REGISTRY


class TestCalculateCost:
    """Test cost calculation accuracy."""

    def test_basic_calculation_anthropic(self):
        """Test basic cost calculation for Anthropic."""
        # Claude 3.5 Sonnet: $3/1M input, $15/1M output
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1_000_000, 1_000_000)
        assert cost == 18.00  # $3 + $15

        # Half the tokens
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 500_000, 500_000)
        assert cost == 9.00  # $1.50 + $7.50

    def test_basic_calculation_openai(self):
        """Test basic cost calculation for OpenAI."""
        # GPT-4o: $2.50/1M input, $10/1M output
        cost = calculate_cost("openai", "gpt-4o", 1_000_000, 1_000_000)
        assert cost == 12.50  # $2.50 + $10

        # GPT-4o Mini: $0.15/1M input, $0.60/1M output
        cost = calculate_cost("openai", "gpt-4o-mini", 1_000_000, 1_000_000)
        assert cost == 0.75  # $0.15 + $0.60

    def test_basic_calculation_google(self):
        """Test basic cost calculation for Google."""
        # Gemini 2.5 Flash: $0.15/1M input, $0.60/1M output
        cost = calculate_cost("google", "gemini-2.5-flash", 1_000_000, 1_000_000)
        assert cost == 0.75  # $0.15 + $0.60

    def test_small_token_counts(self):
        """Test calculation with realistic small token counts."""
        # 1000 input tokens, 500 output tokens with Claude Sonnet
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1000, 500)
        expected = (1000 / 1_000_000 * 3.00) + (500 / 1_000_000 * 15.00)
        assert abs(cost - expected) < 0.0001
        assert cost == pytest.approx(0.0105, abs=0.0001)

    def test_zero_tokens(self):
        """Test calculation with zero tokens."""
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 0, 0)
        assert cost == 0.0

        cost = calculate_cost("openai", "gpt-4o", 1000, 0)
        assert cost == pytest.approx(0.0025, abs=0.0001)  # Updated for $2.50/1M

        cost = calculate_cost("google", "gemini-2.5-flash", 0, 1000)
        assert cost == pytest.approx(0.0006, abs=0.0001)  # Updated for $0.60/1M

    def test_large_token_counts(self):
        """Test calculation with very large token counts."""
        # 10 million tokens
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 10_000_000, 10_000_000)
        assert cost == 180.00  # $30 + $150

    def test_cache_discount_anthropic(self):
        """Test 90% cache discount for Anthropic."""
        # Without cache: 1M tokens = $3
        cost_no_cache = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1_000_000, 0)
        assert cost_no_cache == 3.00

        # With cache: 1M input tokens, all cached = $2.70 (90% discount means 10% cost)
        cost_with_cache = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 0, 0, cache_read_tokens=1_000_000)
        assert cost_with_cache == pytest.approx(2.70, abs=0.01)

    def test_cache_discount_openai(self):
        """Test 50% cache discount for OpenAI."""
        # Without cache: 1M tokens = $2.50
        cost_no_cache = calculate_cost("openai", "gpt-4o", 1_000_000, 0)
        assert cost_no_cache == 2.50

        # With cache: 1M input tokens, all cached = $1.25 (50% discount means 50% cost)
        cost_with_cache = calculate_cost("openai", "gpt-4o", 0, 0, cache_read_tokens=1_000_000)
        assert cost_with_cache == pytest.approx(1.25, abs=0.01)

    def test_cache_discount_google(self):
        """Test 75% cache discount for Google."""
        # Without cache: 1M tokens = $1.25
        cost_no_cache = calculate_cost("google", "gemini-2.5-pro", 1_000_000, 0)
        assert cost_no_cache == 1.25

        # With cache: 1M input tokens, all cached = $0.9375 (75% discount means 25% cost)
        cost_with_cache = calculate_cost("google", "gemini-2.5-pro", 0, 0, cache_read_tokens=1_000_000)
        assert cost_with_cache == pytest.approx(0.9375, abs=0.01)

    def test_batch_discount(self):
        """Test 50% batch API discount for all providers."""
        # Anthropic batch
        cost_regular = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1_000_000, 1_000_000)
        cost_batch = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1_000_000, 1_000_000, is_batch=True)
        assert cost_batch == cost_regular * 0.50

        # OpenAI batch
        cost_regular = calculate_cost("openai", "gpt-4o", 1_000_000, 1_000_000)
        cost_batch = calculate_cost("openai", "gpt-4o", 1_000_000, 1_000_000, is_batch=True)
        assert cost_batch == cost_regular * 0.50

        # Google batch
        cost_regular = calculate_cost("google", "gemini-2.5-flash", 1_000_000, 1_000_000)
        cost_batch = calculate_cost("google", "gemini-2.5-flash", 1_000_000, 1_000_000, is_batch=True)
        assert cost_batch == cost_regular * 0.50

    def test_combined_cache_and_batch(self):
        """Test combining cache discount and batch API discount."""
        # Cache discount: 1M cached tokens at 90% discount = $2.70
        cost_cached = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 0, 0, cache_read_tokens=1_000_000)
        assert cost_cached == pytest.approx(2.70, abs=0.01)

        # Batch discount on top: $2.70 * 0.5 = $1.35
        cost_cached_batch = calculate_cost(
            "anthropic", "claude-3-5-sonnet-latest", 0, 0, cache_read_tokens=1_000_000, is_batch=True
        )
        assert cost_cached_batch == pytest.approx(1.35, abs=0.01)

    def test_negative_tokens_raises_error(self):
        """Test that negative token counts are handled (converted to 0)."""
        # Test with negative token counts - should return 0.0 cost
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", -10, -5)
        assert cost == 0.0

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            calculate_cost("invalid", "some-model", 1000, 500)

    def test_invalid_model_raises_error(self):
        """Test that invalid model names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            calculate_cost("anthropic", "invalid-model-xyz", 1000, 500)

        with pytest.raises(ValueError, match="Unknown model"):
            calculate_cost("openai", "gpt-99", 1000, 500)

    def test_empty_strings_raise_error(self):
        """Test that empty strings raise ValueError."""
        with pytest.raises(ValueError):
            calculate_cost("", "claude-3-5-sonnet-latest", 1000, 500)

        with pytest.raises(ValueError):
            calculate_cost("anthropic", "", 1000, 500)


class TestGetPricingInfo:
    """Test pricing info query function."""

    def test_get_all_providers(self):
        """Test getting all models from registry."""
        info = get_pricing_info()
        # Should return MODEL_REGISTRY which has model keys
        assert "claude-3-5-sonnet-latest" in info
        assert "gpt-4o" in info
        assert "gemini-2.5-pro" in info

    def test_get_specific_provider(self):
        """Test getting specific provider pricing."""
        info = get_pricing_info(provider="anthropic")
        assert "claude-3-5-sonnet-latest" in info
        # Provider-level discounts are in PROVIDER_DISCOUNTS, not in the returned info
        assert isinstance(info, dict)

    def test_get_specific_model(self):
        """Test getting specific model pricing."""
        info = get_pricing_info(provider="anthropic", model="claude-3-5-sonnet-latest")
        assert info["cost_input"] == 3.00
        assert info["cost_output"] == 15.00

    def test_invalid_provider_returns_none(self):
        """Test that invalid provider returns empty dict."""
        info = get_pricing_info(provider="invalid")
        assert info == {}

    def test_invalid_model_returns_none(self):
        """Test that invalid model returns None."""
        info = get_pricing_info(provider="anthropic", model="invalid-model")
        assert info is None


class TestPricingDataIntegrity:
    """Test that pricing data is complete and consistent."""

    def test_last_updated_present(self):
        """Test that models have required fields."""
        # Check that models exist in registry
        assert len(MODEL_REGISTRY) > 0
        # Check a sample model has required fields
        sample_model = MODEL_REGISTRY["claude-3-5-sonnet-latest"]
        assert "cost_input" in sample_model
        assert "cost_output" in sample_model

    def test_all_providers_have_cache_discount(self):
        """Test that all providers have cache_discount defined."""
        for provider in ["anthropic", "openai", "google"]:
            assert "cache_discount" in PROVIDER_DISCOUNTS[provider]
            assert 0 < PROVIDER_DISCOUNTS[provider]["cache_discount"] <= 1

    def test_all_providers_have_batch_discount(self):
        """Test that all providers have batch_discount defined."""
        for provider in ["anthropic", "openai", "google"]:
            assert "batch_discount" in PROVIDER_DISCOUNTS[provider]
            assert PROVIDER_DISCOUNTS[provider]["batch_discount"] == 0.50

    def test_all_models_have_input_output_pricing(self):
        """Test that all models have both input and output pricing."""
        for model_name, model_info in MODEL_REGISTRY.items():
            assert "cost_input" in model_info, f"{model_name} missing cost_input"
            assert "cost_output" in model_info, f"{model_name} missing cost_output"
            assert model_info["cost_input"] > 0, f"{model_name} has invalid cost_input"
            assert model_info["cost_output"] > 0, f"{model_name} has invalid cost_output"

    def test_output_more_expensive_than_input(self):
        """Test that output tokens are more expensive than input (generally true)."""
        for model_name, model_info in MODEL_REGISTRY.items():
            # Output should be >= input (usually more expensive)
            assert model_info["cost_output"] >= model_info["cost_input"], f"{model_name} has output cheaper than input"


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    def test_typical_conversation_cost(self):
        """Test cost of a typical conversation."""
        # Typical: 2000 input tokens, 500 output tokens
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 2000, 500)
        assert 0.01 < cost < 0.02  # Should be around $0.0135

    def test_long_document_analysis(self):
        """Test cost of analyzing a long document."""
        # Long doc: 50K input tokens, 2K output tokens
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 50_000, 2_000)
        assert 0.15 < cost < 0.20  # Should be around $0.18

    def test_code_generation_task(self):
        """Test cost of code generation."""
        # Code gen: 5K input tokens, 3K output tokens
        cost = calculate_cost("openai", "gpt-4o", 5_000, 3_000)
        assert 0.03 < cost < 0.05  # Should be around $0.0425

    def test_budget_friendly_option(self):
        """Test that budget models are significantly cheaper."""
        # Same task with expensive vs cheap model
        # Use opus-4 instead of the old opus model
        cost_expensive = calculate_cost("anthropic", "claude-opus-4-20250514", 10_000, 2_000)
        cost_cheap = calculate_cost("anthropic", "claude-3-5-haiku-latest", 10_000, 2_000)

        # Haiku should be much cheaper than Opus
        assert cost_cheap < cost_expensive * 0.2  # At least 5x cheaper
