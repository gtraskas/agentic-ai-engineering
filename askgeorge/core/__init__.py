"""Core building blocks for AskGeorge: config, knowledge, tools, and agents."""

from __future__ import annotations

from typing import Protocol

from askgeorge.core.config import agent_backend
from askgeorge.core.jobfit import JobFitAnalyzer
from askgeorge.core.knowledge import BackgroundKnowledge, build_knowledge
from askgeorge.core.notifier import EmailNotifier
from askgeorge.core.profile import Profile
from askgeorge.core.tools import ToolDispatcher


class ChatAgent(Protocol):
    """Anything with a Gradio-compatible streaming ``chat`` callable."""

    def chat(self, message: str, history: list) -> object: ...


def _build_agent(
    profile: Profile,
    knowledge: BackgroundKnowledge,
    dispatcher: ToolDispatcher,
) -> ChatAgent:
    """Build the chat agent for the configured backend.

    Raises:
        ValueError: If AGENT_BACKEND holds an unknown backend name.
    """
    backend = agent_backend()
    if backend == "scratch":
        from askgeorge.core.agent_scratch import ScratchAgent

        return ScratchAgent(profile, knowledge, dispatcher)
    if backend == "sdk":
        from askgeorge.core.agent_sdk import SdkAgent

        return SdkAgent(profile, knowledge, dispatcher)
    raise ValueError(f"Unknown AGENT_BACKEND {backend!r}; use 'scratch' or 'sdk'.")


def create_agent() -> ChatAgent:
    """Assemble just the chat agent (scratch or SDK backend).

    Returns:
        A ready-to-serve agent selected by the AGENT_BACKEND env var.
    """
    profile = Profile.load()
    knowledge = build_knowledge(profile)
    dispatcher = ToolDispatcher(EmailNotifier())
    return _build_agent(profile, knowledge, dispatcher)


def create_app_components() -> tuple[ChatAgent, JobFitAnalyzer]:
    """Build the chat agent and the job-fit analyzer, sharing one RAG index.

    Loading the profile and knowledge once avoids embedding the corpus twice
    and keeps startup fast.

    Returns:
        A tuple of (chat agent, job-fit analyzer).
    """
    profile = Profile.load()
    knowledge = build_knowledge(profile)
    notifier = EmailNotifier()
    dispatcher = ToolDispatcher(notifier)
    agent = _build_agent(profile, knowledge, dispatcher)
    analyzer = JobFitAnalyzer(profile, knowledge, notifier)
    return agent, analyzer


__all__ = [
    "BackgroundKnowledge",
    "ChatAgent",
    "EmailNotifier",
    "JobFitAnalyzer",
    "Profile",
    "ToolDispatcher",
    "build_knowledge",
    "create_agent",
    "create_app_components",
]
