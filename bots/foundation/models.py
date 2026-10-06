"""Supported LLM models: the single source of truth for model identity and metadata.

Each ``Model`` member is the model ID sent to the provider's API (members are
``str`` subclasses, so ``Model.CLAUDE46_SONNET == "claude-sonnet-4-6"``) and also
carries that model's metadata: provider, intelligence tier, output-token limit,
pricing, and lifecycle flags.

    >>> Model.CLAUDE46_SONNET.provider
    'anthropic'
    >>> Model.CLAUDE46_SONNET.cost_input
    3.0

"Latest" shortcuts
------------------
``Model.CLAUDE_HAIKU_LATEST``, ``Model.CLAUDE_SONNET_LATEST`` and
``Model.CLAUDE_OPUS_LATEST`` are not real model IDs. When a bot is created with
one of them, ``resolve_model`` asks the Anthropic API which models it currently
serves and picks the newest model in that family. The bot then stores the
concrete model, so a saved bot reloads with exactly the model it was using.

Resolution never falls back silently. It raises ``ModelResolutionError`` if the
API can't be reached, if no model in the family is served, or if the newest
served model isn't listed here yet (add it to ``Model`` to fix that).

Adding a model
--------------
Add one member below. ``bots.foundation.model_registry.MODEL_REGISTRY`` and the
CLI model lists are derived from this enum. Run
``python -m bots.dev.update_model_registry`` to compare against the live API.
"""

import contextlib
import contextvars
import logging
import os
import threading
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, Union

if TYPE_CHECKING:
    from bots.foundation.base import Bot, ConversationNode

logger = logging.getLogger(__name__)


class ModelResolutionError(RuntimeError):
    """Raised when a model can't be used: unknown, retired, or a "latest" shortcut that can't be resolved."""


@dataclass(frozen=True)
class ModelSpec:
    """Metadata for one model. Costs are USD per 1M tokens."""

    id: str
    provider: str
    intelligence: int  # 1 = fast/cheap, 2 = balanced, 3 = most capable
    max_tokens: Optional[int] = None
    cost_input: Optional[float] = None
    cost_output: Optional[float] = None
    deprecated: bool = False
    retired: bool = False
    retirement_date: Optional[str] = None
    alias_for: Optional[str] = None
    supports_temperature: bool = True
    latest_of: Optional[str] = None  # family name ("haiku", ...) for "latest" shortcuts

    def to_info(self) -> Dict[str, Any]:
        """Return the legacy registry dict (flags included only when set)."""
        info: Dict[str, Any] = {
            "provider": self.provider,
            "intelligence": self.intelligence,
            "max_tokens": self.max_tokens,
            "cost_input": self.cost_input,
            "cost_output": self.cost_output,
        }
        for key in ("deprecated", "retired", "retirement_date", "alias_for", "latest_of"):
            value = getattr(self, key)
            if value:
                info[key] = value
        return info


def _spec(model_id: str, provider: str, intelligence: int, max_tokens: int, cost_input: float, cost_output: float, **flags: Any) -> ModelSpec:
    return ModelSpec(model_id, provider, intelligence, max_tokens, cost_input, cost_output, **flags)


def _latest(model_id: str, family: str, intelligence: int) -> ModelSpec:
    return ModelSpec(model_id, "anthropic", intelligence, latest_of=family)


class Model(str, Enum):
    """Supported LLM models. See the module docstring for details."""

    def __new__(cls, spec: ModelSpec) -> "Model":
        obj = str.__new__(cls, spec.id)
        obj._value_ = spec.id
        obj.spec = spec
        return obj

    # "Latest" shortcuts, resolved against the Anthropic API when a bot is created
    CLAUDE_HAIKU_LATEST = _latest("claude-haiku-latest", "haiku", 1)
    CLAUDE_SONNET_LATEST = _latest("claude-sonnet-latest", "sonnet", 2)
    CLAUDE_OPUS_LATEST = _latest("claude-opus-latest", "opus", 3)

    GPT35TURBO = _spec('gpt-3.5-turbo', 'openai', 1, 4_096, 0.5, 1.5)
    GPT35TURBO_16K = _spec('gpt-3.5-turbo-16k', 'openai', 1, 16_384, 3.00, 4.00)
    GPT35TURBO_0125 = _spec('gpt-3.5-turbo-0125', 'openai', 1, 4_096, 0.5, 1.5)
    GPT35TURBO_INSTRUCT = _spec('gpt-3.5-turbo-instruct', 'openai', 1, 4_096, 1.5, 2.00)
    GPT4 = _spec('gpt-4', 'openai', 2, 8_192, 30.00, 60.00)
    GPT41 = _spec('gpt-4.1', 'openai', 2, 8_192, 30.00, 60.00)
    GPT4_0613 = _spec('gpt-4-0613', 'openai', 2, 8_192, 30.00, 60.00)
    GPT4_32K = _spec('gpt-4-32k', 'openai', 3, 32_768, 60.00, 120.00)
    GPT4_32K_0613 = _spec('gpt-4-32k-0613', 'openai', 3, 32_768, 60.00, 120.00)
    GPT4O = _spec('gpt-4o', 'openai', 2, 16_384, 2.5, 10.00)
    GPT4O_MINI = _spec('gpt-4o-mini', 'openai', 1, 16_384, 0.15, 0.6)
    GPT52_INSTANT = _spec('gpt-5.2-instant', 'openai', 2, 128_000, 1.75, 14.00)
    GPT52_THINKING = _spec('gpt-5.2-thinking', 'openai', 3, 128_000, 1.75, 14.00)
    GPT52_PRO = _spec('gpt-5.2-pro', 'openai', 3, 128_000, 1.75, 14.00)
    CLAUDE3_HAIKU = _spec('claude-3-haiku-20240307', 'anthropic', 1, 4_096, 0.25, 1.25, retired=True, retirement_date='2026-04-19')
    CLAUDE3_SONNET = _spec('claude-3-sonnet-20240229', 'anthropic', 2, 4_096, 3.00, 15.00, deprecated=True, retired=True, retirement_date='2025-01-01')
    CLAUDE3_OPUS = _spec('claude-3-opus-20240229', 'anthropic', 3, 4_096, 15.00, 75.00, deprecated=True, retired=True, retirement_date='2026-01-05')
    CLAUDE35_SONNET_20241022 = _spec('claude-3-5-sonnet-20241022', 'anthropic', 2, 8_192, 3.00, 15.00, deprecated=True, retired=True, retirement_date='2025-01-01')
    CLAUDE35_SONNET_20240620 = _spec('claude-3-5-sonnet-20240620', 'anthropic', 2, 8_192, 3.00, 15.00, deprecated=True, retired=True, retirement_date='2025-01-01')
    CLAUDE4_SONNET = _spec('claude-sonnet-4-20250514', 'anthropic', 2, 64_000, 3.00, 15.00, deprecated=True, retired=True)
    CLAUDE4_OPUS = _spec('claude-opus-4-20250514', 'anthropic', 3, 64_000, 15.00, 75.00, deprecated=True, retired=True)
    CLAUDE41_OPUS = _spec('claude-opus-4-1-20250805', 'anthropic', 3, 64_000, 15.00, 75.00, retired=True)
    CLAUDE45_HAIKU = _spec('claude-haiku-4-5-20251001', 'anthropic', 1, 64_000, 1.00, 5.00)
    CLAUDE45_SONNET = _spec('claude-sonnet-4-5-20250929', 'anthropic', 2, 64_000, 3.00, 15.00)
    CLAUDE45_OPUS = _spec('claude-opus-4-5-20251101', 'anthropic', 3, 64_000, 5.00, 25.00)
    CLAUDE46_SONNET = _spec('claude-sonnet-4-6', 'anthropic', 2, 128_000, 3.00, 15.00)
    CLAUDE46_OPUS = _spec('claude-opus-4-6', 'anthropic', 3, 128_000, 5.00, 25.00)
    CLAUDE47_OPUS = _spec('claude-opus-4-7', 'anthropic', 3, 128_000, 5.00, 25.00, supports_temperature=False)
    CLAUDE48_OPUS = _spec('claude-opus-4-8', 'anthropic', 3, 128_000, 5.00, 25.00, supports_temperature=False)
    CLAUDE5_SONNET = _spec('claude-sonnet-5', 'anthropic', 2, 128_000, 2.00, 10.00, supports_temperature=False)
    CLAUDE5_OPUS = _spec('claude-opus-5', 'anthropic', 3, 128_000, 5.00, 25.00, supports_temperature=False)
    CLAUDE55_SONNET = _spec('claude-sonnet-5-5', 'anthropic', 2, 128_000, 2.00, 10.00, supports_temperature=False)
    CLAUDE55_OPUS = _spec('claude-opus-5-5', 'anthropic', 3, 128_000, 4.00, 20.00, supports_temperature=False)
    CLAUDE35_HAIKU_LATEST = _spec('claude-3-5-haiku-latest', 'anthropic', 1, 64_000, 1.00, 5.00, deprecated=True, retired=True, alias_for='claude-haiku-4-5-20251001')
    CLAUDE35_SONNET_LATEST = _spec('claude-3-5-sonnet-latest', 'anthropic', 2, 8_192, 3.00, 15.00, deprecated=True, retired=True, alias_for='claude-3-5-sonnet-20241022')
    CLAUDE_SONNET_4_LATEST = _spec('claude-sonnet-4-latest', 'anthropic', 2, 64_000, 3.00, 15.00, deprecated=True, retired=True, alias_for='claude-sonnet-4-20250514')
    CLAUDE_OPUS_4_LATEST = _spec('claude-opus-4-latest', 'anthropic', 3, 64_000, 15.00, 75.00, deprecated=True, retired=True, alias_for='claude-opus-4-20250514')
    GEMINI15_PRO = _spec('gemini-1.5-pro', 'google', 2, 8_192, 1.25, 10.00)
    GEMINI15_FLASH = _spec('gemini-1.5-flash', 'google', 1, 8_192, 0.075, 0.3)
    GEMINI20_FLASH = _spec('gemini-2.0-flash', 'google', 1, 8_192, 0.1, 0.4)
    GEMINI25_FLASH = _spec('gemini-2.5-flash', 'google', 1, 8_192, 0.15, 0.6)
    GEMINI25_FLASH_LITE = _spec('gemini-2.5-flash-lite', 'google', 1, 8_192, 0.1, 0.4)
    GEMINI25_PRO = _spec('gemini-2.5-pro', 'google', 2, 65_536, 1.25, 10.00)
    GEMINI3_FLASH = _spec('gemini-3-flash-preview', 'google', 1, 64_000, 0.5, 3.00)
    GEMINI3_PRO = _spec('gemini-3-pro-preview', 'google', 3, 64_000, 2.00, 12.00)
    CLAUDE45_HAIKU_ALIAS = _spec('claude-haiku-4-5', 'anthropic', 1, 64_000, 1.00, 5.00, alias_for='claude-haiku-4-5-20251001')
    GPT4_TURBO = _spec('gpt-4-turbo', 'openai', 2, 128_000, 10.00, 30.00)
    GEMINI20_PRO = _spec('gemini-2.0-pro', 'google', 2, 8_192, 1.25, 10.00)
    GEMINI25_PRO_LONG = _spec('gemini-2.5-pro-long', 'google', 2, 65_536, 2.5, 15.00)

    # ------------------------------------------------------------------ metadata

    @property
    def provider(self) -> str:
        return self.spec.provider

    @property
    def intelligence(self) -> int:
        return self.spec.intelligence

    @property
    def max_tokens(self) -> Optional[int]:
        return self.spec.max_tokens

    @property
    def cost_input(self) -> Optional[float]:
        return self.spec.cost_input

    @property
    def cost_output(self) -> Optional[float]:
        return self.spec.cost_output

    @property
    def retired(self) -> bool:
        return self.spec.retired

    @property
    def deprecated(self) -> bool:
        return self.spec.deprecated

    @property
    def supports_temperature(self) -> bool:
        return self.spec.supports_temperature

    @property
    def is_latest_shortcut(self) -> bool:
        """True for CLAUDE_*_LATEST, which must be resolved before use."""
        return self.spec.latest_of is not None

    def get_info(self) -> Dict[str, Any]:
        """Return this model's metadata as a dict (legacy registry format).

        Keys: provider, intelligence, max_tokens, cost_input, cost_output, plus
        deprecated / retired / retirement_date / alias_for / latest_of when set.
        For "latest" shortcuts, max_tokens and costs are None until resolved.
        """
        return self.spec.to_info()

    # ------------------------------------------------------------------ lookups

    @staticmethod
    def get(name: Union[str, "Model"]) -> Optional["Model"]:
        """Return the member whose model ID is ``name``, or None if unknown."""
        if isinstance(name, Model):
            return name
        try:
            return Model(name)
        except ValueError:
            return None

    @staticmethod
    def get_bot_class(model_engine: "Model") -> Type["Bot"]:
        """Return the Bot subclass for a model's provider."""
        from bots.foundation.anthropic_bots import AnthropicBot
        from bots.foundation.gemini_bots import GeminiBot
        from bots.foundation.openai_bots import ChatGPT_Bot

        bot_classes = {"anthropic": AnthropicBot, "openai": ChatGPT_Bot, "google": GeminiBot}
        model = Model.get(model_engine)
        if model is None or model.provider not in bot_classes:
            raise ValueError(f"Unsupported model engine: {model_engine}")
        return bot_classes[model.provider]

    @staticmethod
    def get_conversation_node_class(class_name: str) -> Type["ConversationNode"]:
        """Return the ConversationNode subclass named ``class_name`` (used when loading saved bots)."""
        from bots.foundation.anthropic_bots import AnthropicNode
        from bots.foundation.base import ConversationNode
        from bots.foundation.gemini_bots import GeminiNode
        from bots.foundation.openai_bots import OpenAINode
        from bots.testing.mock_bot import MockConversationNode

        node_classes = {
            "ConversationNode": ConversationNode,
            "OpenAINode": OpenAINode,
            "AnthropicNode": AnthropicNode,
            "GeminiNode": GeminiNode,
            "MockConversationNode": MockConversationNode,
        }
        if class_name not in node_classes:
            raise ValueError(f"Unsupported node class: {class_name}")
        return node_classes[class_name]


# Backward-compatible name. New code should use Model.
Engines = Model


# ---------------------------------------------------------------------- resolution

_cache_lock = threading.Lock()
_anthropic_models_cache: Optional[List[Tuple[str, Any]]] = None

# The model listing is one small request made while _cache_lock is held, so it
# must fail fast: a short timeout and no SDK retries. A network outage then
# raises ModelResolutionError in seconds instead of blocking every thread that
# creates a shortcut-based bot for the SDK's default timeout and retry policy.
MODEL_LIST_TIMEOUT_SECONDS = 10.0

# Set only while a saved bot is being rebuilt (see allow_retired_models).
_allow_retired: contextvars.ContextVar[bool] = contextvars.ContextVar("bots_allow_retired_models", default=False)


@contextlib.contextmanager
def allow_retired_models():
    """Let resolve_model accept retired models inside this block.

    Used when loading saved bots, so a conversation saved with a now-retired
    model can still be opened (and moved to a current model with /switch).
    New bots are still rejected if they ask for a retired model.
    """
    token = _allow_retired.set(True)
    try:
        yield
    finally:
        _allow_retired.reset(token)


def _fetch_anthropic_models(api_key: Optional[str]) -> List[Tuple[str, Any]]:
    """Return [(model_id, created_at), ...] from the Anthropic API. Tests patch this."""
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ModelResolutionError(
            "Can't resolve a CLAUDE_*_LATEST model: no Anthropic API key. "
            "Set ANTHROPIC_API_KEY or pass api_key, or use a specific model such as Model.CLAUDE46_SONNET."
        )
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key, timeout=MODEL_LIST_TIMEOUT_SECONDS, max_retries=0)
        return [(m.id, m.created_at) for m in client.models.list(limit=1000)]
    except Exception as e:
        raise ModelResolutionError(
            f"Can't resolve a CLAUDE_*_LATEST model: listing models from the Anthropic API failed ({type(e).__name__}: {e}). "
            "Check your network and API key, or use a specific model such as Model.CLAUDE46_SONNET."
        ) from e


def _anthropic_models(api_key: Optional[str]) -> List[Tuple[str, Any]]:
    """Fetch the served-model list once per process (successful results only)."""
    global _anthropic_models_cache
    with _cache_lock:
        if _anthropic_models_cache is None:
            _anthropic_models_cache = _fetch_anthropic_models(api_key)
        return _anthropic_models_cache


def clear_model_cache() -> None:
    """Forget the cached API model list, so the next "latest" resolution queries the API again."""
    global _anthropic_models_cache
    with _cache_lock:
        _anthropic_models_cache = None


def _resolve_latest(shortcut: Model, api_key: Optional[str]) -> Model:
    family = shortcut.spec.latest_of
    served = [(mid, created) for mid, created in _anthropic_models(api_key) if mid.startswith(f"claude-{family}-")]
    if not served:
        raise ModelResolutionError(f"Can't resolve {shortcut.value}: the Anthropic API lists no claude-{family} models.")
    newest_id = max(served, key=lambda item: item[1])[0]
    model = Model.get(newest_id)
    if model is None:
        raise ModelResolutionError(
            f"Can't resolve {shortcut.value}: the newest {family} model the API serves is '{newest_id}', "
            "which isn't in bots.foundation.models.Model yet. Add it there (run "
            "`python -m bots.dev.update_model_registry` for details), or use a specific model."
        )
    if model.retired:
        raise ModelResolutionError(
            f"Can't resolve {shortcut.value}: the API serves '{newest_id}', but Model marks it retired. Fix the retired flag in bots/foundation/models.py."
        )
    logger.info("Resolved %s to %s", shortcut.value, model.value)
    return model


def resolve_model(model: Union[str, Model], api_key: Optional[str] = None) -> Model:
    """Turn a model name or member into a concrete, usable Model.

    - Strings are looked up by model ID.
    - CLAUDE_*_LATEST shortcuts are resolved against the Anthropic API (cached per process).
    - Retired models are rejected, except inside allow_retired_models() (used when
      loading saved bots).

    Raises:
        ModelResolutionError: unknown model, retired model, or a shortcut that can't be resolved.
    """
    member = Model.get(model)
    if member is None:
        raise ModelResolutionError(f"Unknown model '{model}'. See bots.foundation.models.Model for supported models.")
    if member.is_latest_shortcut:
        member = _resolve_latest(member, api_key)
    if member.retired:
        if _allow_retired.get():
            logger.warning(
                "Loaded a bot that uses retired model '%s'; API calls will fail until you switch "
                "to a current model (e.g. /switch in the CLI, or set bot.model_engine).",
                member.value,
            )
            return member
        raise ModelResolutionError(
            f"Model '{member.value}' is retired and no longer served by {member.provider}. "
            f"Use a current model, e.g. Model.CLAUDE_SONNET_LATEST."
        )
    return member
