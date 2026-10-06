"""Tests for bots.foundation.models: the Model enum and "latest" model resolution."""

import pytest

from bots.foundation import models
from bots.foundation.models import Engines, Model, ModelResolutionError, resolve_model
from bots.foundation.model_registry import MODEL_REGISTRY, get_model_info

_REAL_FETCH = models._fetch_anthropic_models


def _served(monkeypatch, served, calls=None):
    """Patch the API model list. ``served`` is [(model_id, created_at), ...]."""

    def fake_fetch(api_key=None):
        if calls is not None:
            calls.append(api_key)
        return list(served)

    models.clear_model_cache()
    monkeypatch.setattr(models, "_fetch_anthropic_models", fake_fetch)


class TestSingleSourceOfTruth:
    def test_engines_is_model(self):
        import bots
        from bots.foundation.base import Engines as base_engines

        assert Engines is Model is base_engines is bots.Engines is bots.Model

    def test_members_are_model_id_strings(self):
        assert Model.CLAUDE46_SONNET == "claude-sonnet-4-6"
        assert Model("claude-sonnet-4-6") is Model.CLAUDE46_SONNET

    def test_metadata_lives_on_members(self):
        m = Model.CLAUDE46_SONNET
        assert (m.provider, m.intelligence, m.max_tokens, m.cost_input, m.cost_output) == ("anthropic", 2, 128_000, 3.0, 15.0)

    def test_registry_is_derived_from_enum(self):
        for m in Model:
            if m.is_latest_shortcut:
                assert m.value not in MODEL_REGISTRY
            else:
                assert MODEL_REGISTRY[m.value] == m.get_info()
                assert get_model_info(m) == m.get_info()

    def test_get_bot_class_uses_provider(self):
        from bots.foundation.anthropic_bots import AnthropicBot
        from bots.foundation.gemini_bots import GeminiBot
        from bots.foundation.openai_bots import ChatGPT_Bot

        assert Model.get_bot_class(Model.CLAUDE46_SONNET) is AnthropicBot
        assert Model.get_bot_class(Model.GPT4O) is ChatGPT_Bot
        assert Model.get_bot_class(Model.GEMINI25_PRO) is GeminiBot

    def test_previously_mislabeled_alias_is_retired(self):
        assert Model.CLAUDE35_HAIKU_LATEST.retired


class TestResolveLatest:
    SERVED = [
        ("claude-haiku-4-5-20251001", "2025-10-15"),
        ("claude-sonnet-4-6", "2026-02-17"),
        ("claude-sonnet-5-5", "2026-09-28"),
        ("claude-sonnet-5", "2026-06-29"),
        ("claude-opus-5-5", "2026-09-21"),
    ]

    @pytest.mark.parametrize(
        "shortcut, expected",
        [
            (Model.CLAUDE_HAIKU_LATEST, Model.CLAUDE45_HAIKU),
            (Model.CLAUDE_SONNET_LATEST, Model.CLAUDE55_SONNET),
            (Model.CLAUDE_OPUS_LATEST, Model.CLAUDE55_OPUS),
        ],
    )
    def test_picks_newest_in_family_by_release_date(self, monkeypatch, shortcut, expected):
        _served(monkeypatch, self.SERVED)
        assert resolve_model(shortcut) is expected

    def test_accepts_shortcut_string(self, monkeypatch):
        _served(monkeypatch, self.SERVED)
        assert resolve_model("claude-sonnet-latest") is Model.CLAUDE55_SONNET

    def test_api_queried_once_per_process(self, monkeypatch):
        calls = []
        _served(monkeypatch, self.SERVED, calls)
        resolve_model(Model.CLAUDE_HAIKU_LATEST)
        resolve_model(Model.CLAUDE_SONNET_LATEST)
        resolve_model(Model.CLAUDE_OPUS_LATEST)
        assert len(calls) == 1

    def test_concrete_models_never_call_api(self, monkeypatch):
        calls = []
        _served(monkeypatch, self.SERVED, calls)
        assert resolve_model(Model.CLAUDE46_SONNET) is Model.CLAUDE46_SONNET
        assert resolve_model("gpt-4o") is Model.GPT4O
        assert calls == []


class TestErrorsNotFallbacks:
    def test_api_failure_raises(self, monkeypatch):
        import anthropic

        class Boom:
            def __init__(self, *a, **k):
                raise ConnectionError("network down")

        models.clear_model_cache()
        monkeypatch.setattr(models, "_fetch_anthropic_models", _REAL_FETCH)
        monkeypatch.setattr(anthropic, "Anthropic", Boom)
        with pytest.raises(ModelResolutionError, match="network down"):
            resolve_model(Model.CLAUDE_SONNET_LATEST, api_key="sk-test")

    def test_missing_api_key_raises(self, monkeypatch):
        models.clear_model_cache()
        monkeypatch.setattr(models, "_fetch_anthropic_models", _REAL_FETCH)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ModelResolutionError, match="no Anthropic API key"):
            resolve_model(Model.CLAUDE_SONNET_LATEST)

    def test_failure_is_not_cached(self, monkeypatch):
        attempts = []

        def flaky(api_key=None):
            attempts.append(1)
            if len(attempts) == 1:
                raise ModelResolutionError("transient")
            return [("claude-sonnet-4-6", "2026-02-17")]

        models.clear_model_cache()
        monkeypatch.setattr(models, "_fetch_anthropic_models", flaky)
        with pytest.raises(ModelResolutionError):
            resolve_model(Model.CLAUDE_SONNET_LATEST)
        assert resolve_model(Model.CLAUDE_SONNET_LATEST) is Model.CLAUDE46_SONNET

    def test_no_model_in_family_raises(self, monkeypatch):
        _served(monkeypatch, [("claude-sonnet-4-6", "2026-02-17")])
        with pytest.raises(ModelResolutionError, match="no claude-haiku models"):
            resolve_model(Model.CLAUDE_HAIKU_LATEST)

    def test_newest_unknown_to_enum_raises_instead_of_using_older(self, monkeypatch):
        _served(monkeypatch, [("claude-sonnet-4-6", "2026-02-17"), ("claude-sonnet-9", "2030-01-01")])
        with pytest.raises(ModelResolutionError, match="claude-sonnet-9"):
            resolve_model(Model.CLAUDE_SONNET_LATEST)

    def test_retired_model_rejected(self):
        with pytest.raises(ModelResolutionError, match="retired"):
            resolve_model(Model.CLAUDE3_HAIKU)

    def test_unknown_model_rejected(self):
        with pytest.raises(ModelResolutionError, match="Unknown model"):
            resolve_model("claude-does-not-exist")


class TestBotIntegration:
    def test_anthropic_bot_defaults_to_sonnet_latest(self, monkeypatch):
        import inspect

        from bots.foundation.anthropic_bots import AnthropicBot

        default = inspect.signature(AnthropicBot.__init__).parameters["model_engine"].default
        assert default is Model.CLAUDE_SONNET_LATEST

    def test_bot_stores_concrete_model(self, monkeypatch):
        from bots.foundation.anthropic_bots import AnthropicBot

        _served(monkeypatch, [("claude-sonnet-4-6", "2026-02-17")])
        bot = AnthropicBot(api_key="sk-test", autosave=False)
        assert bot.model_engine is Model.CLAUDE46_SONNET

    def test_bot_with_retired_model_fails_at_creation(self):
        from bots.foundation.anthropic_bots import AnthropicBot

        with pytest.raises(ModelResolutionError, match="retired"):
            AnthropicBot(api_key="sk-test", model_engine=Model.CLAUDE3_HAIKU, autosave=False)

    def test_saved_bot_keeps_its_model(self, monkeypatch, tmp_path):
        from bots.foundation.anthropic_bots import AnthropicBot
        from bots.foundation.base import Bot

        _served(monkeypatch, [("claude-sonnet-4-6", "2026-02-17")])
        bot = AnthropicBot(api_key="sk-test", autosave=False)
        path = str(tmp_path / "saved.bot")
        bot.save(path)

        # A newer Sonnet ships after the save
        _served(monkeypatch, [("claude-sonnet-4-6", "2026-02-17"), ("claude-sonnet-5-5", "2026-09-28")])
        loaded = Bot.load(path, api_key="sk-test")
        assert loaded.model_engine is Model.CLAUDE46_SONNET
        assert AnthropicBot(api_key="sk-test", autosave=False).model_engine is Model.CLAUDE55_SONNET

    def test_mock_bot_never_calls_api(self, monkeypatch):
        from bots.testing.mock_bot import MockBot

        def fail(api_key=None):
            raise AssertionError("MockBot must not call the API")

        models.clear_model_cache()
        monkeypatch.setattr(models, "_fetch_anthropic_models", fail)
        bot = MockBot(model_engine=Model.CLAUDE_SONNET_LATEST)
        assert not bot.model_engine.is_latest_shortcut
        assert MockBot(model_engine=Model.CLAUDE3_HAIKU).model_engine is Model.CLAUDE3_HAIKU
