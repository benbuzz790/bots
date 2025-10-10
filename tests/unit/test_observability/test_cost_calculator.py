"""
Unit tests for cost_calculator module.

Tests cost calculation accuracy for all providers, models, and edge cases.
Critical for business - pricing accuracy is essential for monetization.
"""

import pytest

from bots.observability.cost_calculator import (
    PRICING_DATA,
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
        assert normalize_model("claude-3-5-sonnet-latest", "anthropic") == "claude-3-5-sonnet-latest"
        assert normalize_model("gpt-4o", "openai") == "gpt-4o"
        assert normalize_model("gemini-2.5-flash", "google") == "gemini-2.5-flash"

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert normalize_model("CLAUDE-3-5-SONNET-LATEST", "anthropic") == "claude-3-5-sonnet-latest"
        assert normalize_model("GPT-4O", "openai") == "gpt-4o"

    def test_partial_match(self):
        """Test partial model name matching."""
        # Should match claude-3-5-sonnet-latest
        assert "sonnet" in normalize_model("sonnet", "anthropic").lower()

        # Should match gpt-4o
        assert normalize_model("gpt-4o-2024", "openai") == "gpt-4o"

    def test_unknown_model(self):
        """Test that unknown models raise ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            normalize_model("unknown-model-xyz", "anthropic")


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

        pricing = get_model_pricing("anthropic", "claude-3-opus-20240229")
        assert pricing["input"] == 15.00
        assert pricing["output"] == 75.00

    def test_openai_models(self):
        """Test pricing for all OpenAI models."""
        pricing = get_model_pricing("openai", "gpt-4o")
        assert pricing["input"] == 3.00
        assert pricing["output"] == 10.00

        pricing = get_model_pricing("openai", "gpt-4o-mini")
        assert pricing["input"] == 0.15
        assert pricing["output"] == 0.60

        pricing = get_model_pricing("openai", "gpt-3.5-turbo")
        assert pricing["input"] == 0.50
        assert pricing["output"] == 1.50

    def test_google_models(self):
        """Test pricing for all Google models."""
        pricing = get_model_pricing("google", "gemini-2.5-pro")
        assert pricing["input"] == 1.25
        assert pricing["output"] == 10.00

        pricing = get_model_pricing("google", "gemini-2.5-flash")
        assert pricing["input"] == 0.30
        assert pricing["output"] == 2.50

        pricing = get_model_pricing("google", "gemini-2.0-flash")
        assert pricing["input"] == 0.15
        assert pricing["output"] == 0.60


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
        # GPT-4o: $3/1M input, $10/1M output
        cost = calculate_cost("openai", "gpt-4o", 1_000_000, 1_000_000)
        assert cost == 13.00  # $3 + $10

        # GPT-4o Mini: $0.15/1M input, $0.60/1M output
        cost = calculate_cost("openai", "gpt-4o-mini", 1_000_000, 1_000_000)
        assert cost == 0.75  # $0.15 + $0.60

    def test_basic_calculation_google(self):
        """Test basic cost calculation for Google."""
        # Gemini 2.5 Flash: $0.30/1M input, $2.50/1M output
        cost = calculate_cost("google", "gemini-2.5-flash", 1_000_000, 1_000_000)
        assert cost == 2.80  # $0.30 + $2.50

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
        assert cost == pytest.approx(0.003, abs=0.0001)

        cost = calculate_cost("google", "gemini-2.5-flash", 0, 1000)
        assert cost == pytest.approx(0.0025, abs=0.0001)

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

        # With cache: 1M input tokens, all cached = $0.30 (90% discount)
        cost_with_cache = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1_000_000, 0, cached_tokens=1_000_000)
        assert cost_with_cache == pytest.approx(0.30, abs=0.01)

    def test_cache_discount_openai(self):
        """Test 50% cache discount for OpenAI."""
        # Without cache: 1M tokens = $3
        cost_no_cache = calculate_cost("openai", "gpt-4o", 1_000_000, 0)
        assert cost_no_cache == 3.00

        # With cache: 1M input tokens, all cached = $1.50 (50% discount)
        cost_with_cache = calculate_cost("openai", "gpt-4o", 1_000_000, 0, cached_tokens=1_000_000)
        assert cost_with_cache == pytest.approx(1.50, abs=0.01)

    def test_cache_discount_google(self):
        """Test 75% cache discount for Google."""
        # Without cache: 1M tokens = $1.25
        cost_no_cache = calculate_cost("google", "gemini-2.5-pro", 1_000_000, 0)
        assert cost_no_cache == 1.25

        # With cache: 1M input tokens, all cached = $0.3125 (75% discount)
        cost_with_cache = calculate_cost("google", "gemini-2.5-pro", 1_000_000, 0, cached_tokens=1_000_000)
        assert cost_with_cache == pytest.approx(0.3125, abs=0.01)

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
        # Cache discount: 1M cached tokens at 90% off = $0.30
        cost_cached = calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1_000_000, 0, cached_tokens=1_000_000)
        assert cost_cached == pytest.approx(0.30, abs=0.01)

        # Batch discount on top: $0.30 * 0.5 = $0.15
        cost_cached_batch = calculate_cost(
            "anthropic", "claude-3-5-sonnet-latest", 1_000_000, 0, cached_tokens=1_000_000, is_batch=True
        )
        assert cost_cached_batch == pytest.approx(0.15, abs=0.01)

    def test_negative_tokens_raises_error(self):
        """Test that negative token counts raise ValueError."""
        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            calculate_cost("anthropic", "claude-3-5-sonnet-latest", -100, 500)

        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1000, -500)

        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            calculate_cost("anthropic", "claude-3-5-sonnet-latest", 1000, 500, cached_tokens=-100)

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
        """Test getting all provider names."""
        info = get_pricing_info()
        assert "anthropic" in info
        assert "openai" in info
        assert "google" in info
        assert "last_updated" in info

    def test_get_specific_provider(self):
        """Test getting specific provider pricing."""
        info = get_pricing_info(provider="anthropic")
        assert "claude-3-5-sonnet-latest" in info
        assert "cache_discount" in info
        assert "batch_discount" in info

    def test_get_specific_model(self):
        """Test getting specific model pricing."""
        info = get_pricing_info(provider="anthropic", model="claude-3-5-sonnet-latest")
        assert info["input"] == 3.00
        assert info["output"] == 15.00

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
        """Test that last_updated timestamp is present."""
        assert "last_updated" in PRICING_DATA
        assert PRICING_DATA["last_updated"] == "2025-10-09"

    def test_all_providers_have_cache_discount(self):
        """Test that all providers have cache_discount defined."""
        for provider in ["anthropic", "openai", "google"]:
            assert "cache_discount" in PRICING_DATA[provider]
            assert 0 < PRICING_DATA[provider]["cache_discount"] < 1

    def test_all_providers_have_batch_discount(self):
        """Test that all providers have batch_discount defined."""
        for provider in ["anthropic", "openai", "google"]:
            assert "batch_discount" in PRICING_DATA[provider]
            assert PRICING_DATA[provider]["batch_discount"] == 0.50

    def test_all_models_have_input_output_pricing(self):
        """Test that all models have both input and output pricing."""
        for provider in ["anthropic", "openai", "google"]:
            for model, pricing in PRICING_DATA[provider].items():
                if model not in ["cache_discount", "batch_discount"]:
                    assert "input" in pricing, f"{provider}/{model} missing input price"
                    assert "output" in pricing, f"{provider}/{model} missing output price"
                    assert pricing["input"] > 0, f"{provider}/{model} has invalid input price"
                    assert pricing["output"] > 0, f"{provider}/{model} has invalid output price"

    def test_output_more_expensive_than_input(self):
        """Test that output tokens are more expensive than input (generally true)."""
        for provider in ["anthropic", "openai", "google"]:
            for model, pricing in PRICING_DATA[provider].items():
                if model not in ["cache_discount", "batch_discount"]:
                    # Output should be >= input (usually more expensive)
                    assert pricing["output"] >= pricing["input"], f"{provider}/{model} has output cheaper than input"


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
        assert 0.04 < cost < 0.06  # Should be around $0.045

    def test_budget_friendly_option(self):
        """Test that budget models are significantly cheaper."""
        # Same task with expensive vs cheap model
        cost_expensive = calculate_cost("anthropic", "claude-3-opus-20240229", 10_000, 2_000)
        cost_cheap = calculate_cost("anthropic", "claude-3-5-haiku-latest", 10_000, 2_000)

        # Haiku should be much cheaper than Opus
        assert cost_cheap < cost_expensive * 0.2  # At least 5x cheaper
