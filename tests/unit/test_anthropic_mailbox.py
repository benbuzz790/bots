"""Regression tests for Anthropic message parameters and content blocks."""

from types import SimpleNamespace
from unittest.mock import Mock

import anthropic
import pytest

from bots.foundation.anthropic_bots import AnthropicBot, AnthropicMailbox
from bots.foundation.base import Engines


@pytest.mark.parametrize("temperature", [0, 0.3, 1])
@pytest.mark.parametrize(
    "engine, supports_temperature",
    [
        (Engines.CLAUDE47_OPUS, False),
        (Engines.CLAUDE48_OPUS, False),
        (Engines.CLAUDE5_SONNET, False),
        (Engines.CLAUDE5_OPUS, False),
        (Engines.CLAUDE55_SONNET, False),
        (Engines.CLAUDE55_OPUS, False),
        (Engines.CLAUDE46_SONNET, True),
    ],
)
def test_temperature_is_sent_only_when_supported(monkeypatch, engine, supports_temperature, temperature):
    client = Mock()
    client.messages.create.return_value = SimpleNamespace(content=[], role="assistant")
    monkeypatch.setattr(anthropic, "Anthropic", Mock(return_value=client))
    bot = AnthropicBot(api_key="test-key", model_engine=engine, temperature=temperature, autosave=False)
    bot.conversation = bot.conversation._add_reply(role="user", content="Hello")

    assert bot.mailbox.send_message(bot) is client.messages.create.return_value
    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["model"] == engine.value
    if supports_temperature:
        assert kwargs["temperature"] == temperature
    else:
        assert "temperature" not in kwargs


@pytest.mark.parametrize(
    "blocks, expected, inserts_placeholder",
    [
        ([{"type": "text", "text": "Answer"}], "Answer", False),
        ([{"type": "thinking", "thinking": "Reasoning"}, {"type": "text", "text": "Answer"}], "Answer", False),
        ([{"type": "tool_use"}, {"type": "text", "text": "Answer"}], "Answer", False),
        ([{"type": "text", "text": "First"}, {"type": "text", "text": "Second"}], "FirstSecond", False),
        ([{"type": "text", "text": ""}, {"type": "text", "text": "Answer"}], "Answer", False),
        (
            [{"type": "text", "text": "First "}, {"type": "tool_use"}, {"type": "text", "text": "Second"}],
            "First Second",
            False,
        ),
        ([{"type": "tool_use"}], "~", True),
        ([{"type": "thinking", "thinking": "Reasoning"}], "~", True),
        ([{"type": "text", "text": ""}], "~", True),
        ([], "~", True),
    ],
)
def test_response_combines_text_blocks(blocks, expected, inserts_placeholder):
    content = [SimpleNamespace(**block) for block in blocks]
    original_content = content.copy()
    response = SimpleNamespace(content=content, role="assistant")

    assert AnthropicMailbox().process_response(response, None) == (expected, "assistant", {})
    if inserts_placeholder:
        assert response.content[0].type == "text"
        assert response.content[0].text == "~"
        assert response.content[1:] == original_content
    else:
        assert response.content == original_content
