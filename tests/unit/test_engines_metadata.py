"""Unit tests for Engines metadata functionality."""

from bots.foundation.base import MODEL_INFO, Engines


class TestEnginesMetadata:
    """Test that all engines have proper metadata."""

    def test_all_engines_have_metadata(self):
        """Verify every engine has an entry in MODEL_INFO."""
        for engine in Engines:
            assert engine in MODEL_INFO, f"Engine {engine} missing from MODEL_INFO"

    def test_metadata_returns_correct_type(self):
        """Verify get_info() returns a dictionary."""
        info = Engines.CLAUDE45_SONNET.get_info()
        assert isinstance(info, dict)

    def test_metadata_has_required_fields(self):
        """Verify all metadata entries have required fields."""
        required_fields = ["provider", "intelligence", "max_tokens", "cost_input", "cost_output"]
        for engine in Engines:
            info = engine.get_info()
            for field in required_fields:
                assert field in info, f"Engine {engine} missing field {field}"

    def test_metadata_provider_matches_engine(self):
        """Verify provider field matches the engine name pattern."""
        for engine in Engines:
            info = engine.get_info()
            provider = info["provider"]
            engine_value = engine.value.lower()
            if provider == "anthropic":
                assert "claude" in engine_value
            elif provider == "openai":
                assert "gpt" in engine_value
            elif provider == "google":
                assert "gemini" in engine_value

    def test_intelligence_ratings_valid(self):
        """Verify intelligence ratings are 1-3."""
        for engine in Engines:
            info = engine.get_info()
            intelligence = info["intelligence"]
            assert 1 <= intelligence <= 3, f"Engine {engine} has invalid intelligence: {intelligence}"

    def test_token_limits_positive(self):
        """Verify max_tokens are positive integers."""
        for engine in Engines:
            info = engine.get_info()
            max_tokens = info["max_tokens"]
            assert isinstance(max_tokens, int)
            assert max_tokens > 0, f"Engine {engine} has invalid max_tokens: {max_tokens}"

    def test_costs_positive(self):
        """Verify costs are positive numbers."""
        for engine in Engines:
            info = engine.get_info()
            cost_input = info["cost_input"]
            cost_output = info["cost_output"]
            assert cost_input >= 0, f"Engine {engine} has negative cost_input: {cost_input}"
            assert cost_output >= 0, f"Engine {engine} has negative cost_output: {cost_output}"


class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    def test_engines_as_strings_still_work(self):
        """Verify engines can still be used as strings."""
        engine = Engines.CLAUDE45_SONNET
        assert engine.value == "claude-sonnet-4-5-20250929"
        # Engines inherit from str, so they work as strings
        assert engine == "claude-sonnet-4-5-20250929"

    def test_get_method_unchanged(self):
        """Verify Engines.get() still works."""
        engine = Engines.get("claude-sonnet-4-5-20250929")
        assert engine == Engines.CLAUDE45_SONNET

    def test_get_bot_class_unchanged(self):
        """Verify get_bot_class() still works."""
        from bots.foundation.anthropic_bots import AnthropicBot

        bot_class = Engines.get_bot_class(Engines.CLAUDE45_SONNET)
        assert bot_class == AnthropicBot

    def test_get_conversation_node_class_unchanged(self):
        """Verify get_conversation_node_class() still works."""
        from bots.foundation.anthropic_bots import AnthropicNode

        node_class = Engines.get_conversation_node_class("AnthropicNode")
        assert node_class == AnthropicNode


class TestMetadataConsistency:
    """Test consistency between MODEL_INFO and other data sources."""

    def test_all_anthropic_models_have_correct_provider(self):
        """Verify all Claude models have provider='anthropic'."""
        anthropic_engines = [e for e in Engines if "claude" in e.value.lower()]
        for engine in anthropic_engines:
            info = engine.get_info()
            assert info["provider"] == "anthropic", f"{engine} should have provider='anthropic'"

    def test_all_openai_models_have_correct_provider(self):
        """Verify all GPT models have provider='openai'."""
        openai_engines = [e for e in Engines if "gpt" in e.value.lower()]
        for engine in openai_engines:
            info = engine.get_info()
            assert info["provider"] == "openai", f"{engine} should have provider='openai'"

    def test_all_google_models_have_correct_provider(self):
        """Verify all Gemini models have provider='google'."""
        google_engines = [e for e in Engines if "gemini" in e.value.lower()]
        for engine in google_engines:
            info = engine.get_info()
            assert info["provider"] == "google", f"{engine} should have provider='google'"
