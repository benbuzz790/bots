"""Model registry checks must include every API page and fail on API errors."""

from types import SimpleNamespace
from unittest.mock import Mock

import anthropic
import pytest
from anthropic._models import FinalRequestOptions
from anthropic.pagination import SyncPage
from anthropic.types import ModelInfo

from bots.dev.update_model_registry import update_model_registry
from bots.dev.validate_models_hook import check_model_registry
from bots.foundation import model_registry


@pytest.fixture
def model_api(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = Mock()
    monkeypatch.setattr(anthropic, "Anthropic", Mock(return_value=client))
    monkeypatch.setattr(
        model_registry,
        "MODEL_REGISTRY",
        {
            "first": {"provider": "anthropic"},
            "second": {"provider": "anthropic"},
            "retired": {"provider": "anthropic", "retired": True},
            "alias": {"provider": "anthropic", "alias_for": "first"},
            "other": {"provider": "openai"},
        },
    )
    pages = []
    for model_id, has_more in [("first", True), ("second", False)]:
        model = ModelInfo(
            id=model_id,
            type="model",
            created_at="2026-01-01T00:00:00Z",
            display_name=model_id.title(),
            max_input_tokens=200000,
            max_tokens=64000,
        )
        page = SyncPage[ModelInfo](data=[model], has_more=has_more, last_id=model_id)
        page._set_private_attributes(
            client=client, model=ModelInfo, options=FinalRequestOptions.construct(method="get", url="/v1/models", params={})
        )
        pages.append(page)
    client.models.list.return_value = pages[0]
    client._request_api_list.return_value = pages[1]
    return client


def test_validation_reads_every_page(model_api, capsys):
    assert check_model_registry() == 0
    model_api._request_api_list.assert_called_once()
    assert "up-to-date" in capsys.readouterr().out


def test_update_counts_and_displays_every_page(model_api, capsys):
    assert update_model_registry() == 0
    output = capsys.readouterr().out
    assert "Found 2 models" in output
    assert "[OK] second" in output
    assert "Max Input: 200,000 tokens" in output
    assert "Max Output: 64,000 tokens" in output
    assert "[NEEDS MARKING] second" not in output
    model_api._request_api_list.assert_called_once()


@pytest.mark.parametrize("failure_on_next_page", [False, True])
def test_validation_fails_on_api_error(model_api, failure_on_next_page, capsys):
    method = model_api._request_api_list if failure_on_next_page else model_api.models.list
    method.side_effect = RuntimeError("API unavailable")
    assert check_model_registry() == 1
    assert "ERROR: Error checking model registry" in capsys.readouterr().out


def test_validation_detects_unknown_model_on_later_page(model_api, capsys):
    model_api._request_api_list.return_value.data.append(SimpleNamespace(id="new-model"))
    assert check_model_registry() == 1
    assert "new-model" in capsys.readouterr().out


def test_validation_skips_without_key(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client_factory = Mock(side_effect=AssertionError("Must not contact API without a key"))
    monkeypatch.setattr(anthropic, "Anthropic", client_factory)
    assert check_model_registry() == 0
    client_factory.assert_not_called()
    assert "skipping model validation" in capsys.readouterr().out


@pytest.mark.parametrize("limits", [{}, {"max_input_tokens": None, "max_tokens": None}])
def test_update_handles_missing_limits(model_api, capsys, limits):
    model_api.models.list.return_value = [
        ModelInfo(id="first", type="model", created_at="2026-01-01T00:00:00Z", display_name="First", **limits)
    ]
    assert update_model_registry() == 0
    output = capsys.readouterr().out
    assert "Max Input: Unknown tokens" in output
    assert "Max Output: Unknown tokens" in output
