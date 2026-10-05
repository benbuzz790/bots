"""Script to update model registry from Anthropic API.
This script fetches the latest model information from Anthropic's API
and updates the model registry accordingly.
"""

import os
import sys


def update_model_registry() -> int:
    """Update model registry with latest models from Anthropic API.
    Returns:
        0 if successful, 1 if there are errors
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return 1
    try:
        import anthropic

        from bots.foundation.model_registry import MODEL_REGISTRY

        # Get current models from API
        client = anthropic.Anthropic(api_key=api_key)
        models = list(client.models.list())
        print("Fetched models from Anthropic API")
        print(f"Found {len(models)} models\n")
        # Display models and their details
        print("Available Models:")
        print("=" * 80)
        for model in models:
            in_registry = model.id in MODEL_REGISTRY
            status = "OK" if in_registry else "NEW"
            print(f"[{status}] {model.id}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Created: {model.created_at}")
            for label, attribute in [("Max Input", "max_input_tokens"), ("Max Output", "max_tokens")]:
                limit = getattr(model, attribute, None)
                formatted_limit = f"{limit:,}" if limit is not None else "Unknown"
                print(f"   {label}: {formatted_limit} tokens")
            if not in_registry:
                print("   WARNING: Not in registry - needs to be added")
            elif MODEL_REGISTRY[model.id].get("retired"):
                print("   WARNING: Marked as retired in registry")
            print()
        # Check for models in registry not in API
        api_model_ids = {model.id for model in models}
        registry_anthropic_models = {
            model_id
            for model_id, info in MODEL_REGISTRY.items()
            if info.get("provider") == "anthropic" and not info.get("alias_for")
        }
        retired_models = registry_anthropic_models - api_model_ids
        if retired_models:
            print("\n" + "=" * 80)
            print("Models in registry but not in API (potentially retired):")
            for model_id in sorted(retired_models):
                is_marked_retired = MODEL_REGISTRY[model_id].get("retired", False)
                status = "OK (marked)" if is_marked_retired else "NEEDS MARKING"
                print(f"[{status}] {model_id}")
        print("\n" + "=" * 80)
        print("\nTo add new models, update bots/foundation/model_registry.py")
        print("To add to Engines enum, update bots/foundation/base.py")
        return 0
    except ImportError:
        print("ERROR: anthropic package not installed")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(update_model_registry())
