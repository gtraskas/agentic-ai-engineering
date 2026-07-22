"""Core building blocks for AskGeorge: config, knowledge, tools, and agent backends."""

from __future__ import annotations

from typing import Protocol

from askgeorge.core.config import agent_backend
from askgeorge.core.knowledge import BackgroundKnowledge, build_knowledge
from askgeorge.core.notifier import EmailNotifier
from askgeorge.core.profile import Profile
from askgeorge.core.tools import ToolDispatcher


class ChatAgent(Protocol):
    """Anything with a Gradio-compatible streaming ``chat`` callable."""

    def chat(self, message: str, history: list) -> object: ...


def create_agent() -> ChatAgent:
    """Assemble the configured chat agent (scratch or SDK backend).

    Returns:
        A ready-to-serve agent selected by the AGENT_BACKEND env var.

    Raises:
        ValueError: If AGENT_BACKEND holds an unknown backend name.
    """
    profile = Profile.load()
    knowledge = build_knowledge(profile)
    dispatcher = ToolDispatcher(EmailNotifier())
    backend = agent_backend()
    if backend == "scratch":
        from askgeorge.core.agent_scratch import ScratchAgent

        return ScratchAgent(profile, knowledge, dispatcher)
    if backend == "sdk":
        from askgeorge.core.agent_sdk import SdkAgent

        return SdkAgent(profile, knowledge, dispatcher)
    raise ValueError(f"Unknown AGENT_BACKEND {backend!r}; use 'scratch' or 'sdk'.")


__all__ = [
    "BackgroundKnowledge",
    "ChatAgent",
    "EmailNotifier",
    "Profile",
    "ToolDispatcher",
    "build_knowledge",
    "create_agent",
]
