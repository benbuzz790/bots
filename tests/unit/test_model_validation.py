"""
Test to validate that all models in the registry are actually available via their APIs.

This helps us detect when models are deprecated/retired so we can update the registry faster.
"""

import os

import pytest

from bots.foundation.base import Engines
from bots.foundation.model_registry import MODEL_REGISTRY


class TestModelAvailability:
    """Test that models are actually available from their providers."""

    @pytest.mark.parametrize(
        "model_name",
        [
            # Anthropic Claude 4.6 Models (Latest)
            "claude-sonnet-4-6",
            "claude-opus-4-6",
            # Anthropic Claude 4.5 Models
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-5-20251101",
            # Anthropic Claude 4.1 Models
            "claude-opus-4-1-20250805",
            # Anthropic Claude 4 Models
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            # Anthropic Claude 3 Models (only test non-retired ones)
            "claude-3-haiku-20240307",
        ],
    )
    def test_anthropic_model_availability(self, model_name):
        """Test that Anthropic models respond to a simple request.

        This test makes a real API call to verify the model exists.
        It will be skipped if ANTHROPIC_API_KEY is not set.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        # Skip retired models
        model_info = MODEL_REGISTRY.get(model_name)
        if model_info and model_info.get("retired"):
            pytest.skip(f"Model {model_name} is retired")

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)

            # Make a minimal request
            response = client.messages.create(
                model=model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'ok'"}],
            )

            # If we get here, the model exists and responded
            assert response.content is not None
            assert len(response.content) > 0

        except anthropic.NotFoundError as e:
            # Model doesn't exist - this is what we want to catch
            pytest.fail(f"Model {model_name} not found in Anthropic API. " f"It may have been retired. Error: {e}")
        except anthropic.AuthenticationError:
            pytest.skip("Invalid ANTHROPIC_API_KEY")
        except Exception as e:
            # Other errors (rate limits, etc.) shouldn't fail the test
            pytest.skip(f"API error (not model availability issue): {e}")

    def test_model_registry_completeness(self):
        """Verify that all Engines enum values are in the model registry."""
        missing_models = []

        for engine in Engines:
            if engine.value not in MODEL_REGISTRY:
                missing_models.append(engine.value)

        assert not missing_models, f"The following models are in Engines enum but not in MODEL_REGISTRY: " f"{missing_models}"

    def test_no_invalid_models_in_registry(self):
        """Check for known invalid/retired models in the registry."""
        # Models that are known to be retired and should be marked as such
        known_retired = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
        ]

        found_retired = []
        for model in known_retired:
            if model in MODEL_REGISTRY:
                model_info = MODEL_REGISTRY[model]
                # It's OK if it's marked as retired, but it shouldn't be unmarked
                if not model_info.get("retired"):
                    found_retired.append(model)

        assert not found_retired, (
            f"The following retired models are in MODEL_REGISTRY without 'retired' flag: " f"{found_retired}"
        )

    def test_deprecated_models_marked(self):
        """Verify that deprecated models are properly marked."""
        # Models that should be marked as deprecated or retired
        should_be_deprecated = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
        ]

        not_marked = []
        for model in should_be_deprecated:
            if model in MODEL_REGISTRY:
                model_info = MODEL_REGISTRY[model]
                if not model_info.get("deprecated") and not model_info.get("retired"):
                    not_marked.append(model)

        assert not not_marked, f"The following models should be marked as deprecated: {not_marked}"
