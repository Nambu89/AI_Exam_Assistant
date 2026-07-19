"""Agent factory — the single place that touches Microsoft Agent Framework.

Why this module exists
----------------------
Research on the GA release (Agent Framework 1.11, July 2026) found that the
public docs show two constructor surfaces living side by side during the
post-GA stabilisation: ``chat_client.as_agent(...)`` (newest pages) and
``ChatAgent(chat_client=...)`` (API reference). To keep the rest of the codebase
immune to that drift, *all* agent creation goes through :func:`make_agent`, which
tries the newest surface first and falls back gracefully.

Every agent returned here — real or offline — exposes the same tiny surface::

    result = await agent.run(prompt)   # -> AgentRunResult
    result.text                        # -> str

Offline mode
------------
When ``MODEL_PROVIDER=local`` the factory returns a :class:`LocalAgent` that
produces deterministic output from a caller-supplied ``offline_fn``. That lets
the entire multi-agent graph, the FastAPI app and the test-suite run with zero
Azure/OpenAI credentials — the "clone and run" experience.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.config import ModelProvider, get_settings

# Type of an offline responder: (prompt) -> str, sync or async.
OfflineFn = Callable[[str], "str | Awaitable[str]"]


@dataclass(slots=True)
class AgentRunResult:
    """Normalised result so callers never depend on the framework's result type."""

    text: str
    raw: Any = None


@runtime_checkable
class AgentLike(Protocol):
    name: str

    async def run(self, prompt: str) -> AgentRunResult: ...


class LocalAgent:
    """Deterministic, credential-free agent used in offline mode."""

    def __init__(self, name: str, instructions: str, offline_fn: OfflineFn | None = None):
        self.name = name
        self.instructions = instructions
        self._offline_fn = offline_fn

    async def run(self, prompt: str) -> AgentRunResult:
        if self._offline_fn is None:
            return AgentRunResult(
                text=f"[offline:{self.name}] no local responder configured.",
            )
        out = self._offline_fn(prompt)
        if inspect.isawaitable(out):
            out = await out
        return AgentRunResult(text=str(out))


class _FrameworkAgent:
    """Thin wrapper around a real Microsoft Agent Framework agent."""

    def __init__(self, name: str, af_agent: Any):
        self.name = name
        self._agent = af_agent

    async def run(self, prompt: str) -> AgentRunResult:
        result = await self._agent.run(prompt)
        # Agent Framework results expose `.text`; be defensive across versions.
        text = getattr(result, "text", None)
        if text is None:
            text = str(result)
        return AgentRunResult(text=text, raw=result)


def _build_chat_client(model: str) -> Any:
    """Create the provider-specific Agent Framework chat client.

    Import paths are resolved lazily so the package imports cleanly even when
    the (heavy) framework extras are not installed — important for the offline
    path and for unit tests.
    """
    settings = get_settings()
    provider = settings.model_provider

    if provider == ModelProvider.FOUNDRY:
        # Azure AI Foundry project (Hosted Agents + Foundry IQ).
        from agent_framework.foundry import FoundryChatClient  # type: ignore
        from azure.identity import DefaultAzureCredential

        return FoundryChatClient(
            project_endpoint=settings.foundry_project_endpoint,
            model=model,
            credential=DefaultAzureCredential(),
        )

    if provider == ModelProvider.AZURE_OPENAI:
        from agent_framework.azure import AzureOpenAIChatClient  # type: ignore

        if settings.azure_openai_api_key:
            return AzureOpenAIChatClient(
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                deployment_name=model,
            )
        from azure.identity import DefaultAzureCredential

        return AzureOpenAIChatClient(
            endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            deployment_name=model,
            credential=DefaultAzureCredential(),
        )

    if provider == ModelProvider.OPENAI:
        from agent_framework.openai import OpenAIChatClient  # type: ignore

        return OpenAIChatClient(api_key=settings.openai_api_key, model_id=model)

    raise RuntimeError(f"No chat client for provider {provider!r}")


def _agent_from_client(chat_client: Any, name: str, instructions: str, tools: Sequence[Any]) -> Any:
    """Create an agent, tolerating both post-GA constructor surfaces."""
    kwargs: dict[str, Any] = {"name": name, "instructions": instructions}
    if tools:
        kwargs["tools"] = list(tools)

    # Newest docs (Learn, 2026-07): factory method on the chat client.
    as_agent = getattr(chat_client, "as_agent", None)
    if callable(as_agent):
        return as_agent(**kwargs)

    # Fallback: explicit ChatAgent constructor (API reference surface).
    from agent_framework import ChatAgent  # type: ignore

    return ChatAgent(chat_client=chat_client, **kwargs)


def make_agent(
    name: str,
    instructions: str,
    *,
    tools: Sequence[Any] | None = None,
    model: str | None = None,
    offline_fn: OfflineFn | None = None,
) -> AgentLike:
    """Return an agent exposing ``async run(prompt) -> AgentRunResult``.

    In offline mode a :class:`LocalAgent` is returned (using ``offline_fn``);
    otherwise a real Microsoft Agent Framework agent is built for the configured
    provider.
    """
    settings = get_settings()
    if settings.model_provider == ModelProvider.LOCAL:
        return LocalAgent(name, instructions, offline_fn)

    chat_client = _build_chat_client(model or settings.chat_model)
    af_agent = _agent_from_client(chat_client, name, instructions, tools or [])
    return _FrameworkAgent(name, af_agent)
