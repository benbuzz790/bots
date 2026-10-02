"""Pre-commit hook to validate model registry against Anthropic API.
This hook checks that the model registry is up-to-date with the latest
models available from Anthropic's API.
"""
import os
import sys
from typing import Dict, List, Set
def check_model_registry() -> int:
    """Check if model registry is up-to-date with Anthropic API.
    Returns:
        0 if validation passes, 1 if there are issues
    """
    # Only run if ANTHROPIC_API_KEY is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set - skipping model validation")
        return 0
    try:
        import anthropic
        from bots.foundation.model_registry import MODEL_REGISTRY
        # Get current models from API
        client = anthropic.Anthropic(api_key=api_key)
        response = client.models.list()
        # Extract model IDs from API
        api_models: Set[str] = {model.id for model in response.data}
        # Extract non-retired models from registry
        registry_models: Set[str] = {
            model_id for model_id, info in MODEL_REGISTRY.items()
            if info.get("provider") == "anthropic" 
            and not info.get("retired", False)
            and not info.get("alias_for")  # Skip aliases
        }
        # Find models in API but not in registry
        missing_models: Set[str] = api_models - registry_models
        # Find models in registry but not in API (potentially retired)
        extra_models: Set[str] = registry_models - api_models
        issues_found = False
        if missing_models:
            issues_found = True
            print("ERROR: New models found in Anthropic API but not in registry:")
            for model in sorted(missing_models):
                print(f"   - {model}")
            print()
        if extra_models:
            issues_found = True
            print("WARNING: Models in registry but not found in API (may be retired):")
            for model in sorted(extra_models):
                print(f"   - {model}")
            print()
        if issues_found:
            print("Please update bots/foundation/model_registry.py")
            print("Run: python -m bots.dev.update_model_registry")
            return 1
        print("OK: Model registry is up-to-date")
        return 0
    except ImportError:
        print("WARNING: anthropic package not installed - skipping model validation")
        return 0
    except Exception as e:
        print(f"WARNING: Error checking model registry: {e}")
        print("Continuing with commit...")
        return 0
if __name__ == "__main__":
    sys.exit(check_model_registry())