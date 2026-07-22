"""OpenAI Agents SDK backend: same behavior as the scratch loop, framework-managed.

Follows the production guidance for the SDK: a single agent, function tools,
no handoffs, tracing disabled (no OpenAI key in this deployment), and a
non-OpenAI model wired via ``OpenAIChatCompletionsModel`` over OpenRouter.
"""

from __future__ import annotations

import logging
import os
from typing import Any, AsyncIterator

from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner, function_tool
from agents import set_tracing_disabled
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent

from askgeorge.core.config import OPENROUTER_BASE_URL, chat_model
from askgeorge.core.knowledge import BackgroundKnowledge
from askgeorge.core.profile import Profile
from askgeorge.core.prompts import augment_with_context, build_system_prompt
from askgeorge.core.tools import ToolDispatcher

logger = logging.getLogger(__name__)


class SdkAgent:
    """Streaming chat agent built on the OpenAI Agents SDK."""

    def __init__(
        self,
        profile: Profile,
        knowledge: BackgroundKnowledge,
        dispatcher: ToolDispatcher,
    ) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise EnvironmentError("Set OPENROUTER_API_KEY to run AskGeorge.")
        set_tracing_disabled(True)
        self._knowledge = knowledge
        model = OpenAIChatCompletionsModel(
            model=chat_model(),
            openai_client=AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key),
        )
        self._agent = Agent(
            name="AskGeorge",
            instructions=build_system_prompt(profile),
            model=model,
            model_settings=ModelSettings(temperature=0.7),
            tools=self._build_tools(dispatcher),
        )

    async def chat(
        self, message: str, history: list[dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Stream one chat turn token by token via ``Runner.run_streamed``.

        Args:
            message: The visitor's latest message.
            history: Prior turns in Gradio "messages" format.

        Yields:
            The growing reply text, suitable for Gradio streaming.
        """
        context = self._knowledge.context_for(message)
        input_items = [
            *self._sanitize_history(history),
            {"role": "user", "content": augment_with_context(message, context)},
        ]
        result = Runner.run_streamed(self._agent, input=input_items)
        reply = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(
                event.data, ResponseTextDeltaEvent
            ):
                reply += event.data.delta
                yield reply
        if not reply:
            final = str(result.final_output or "")
            yield final or "Sorry — I could not produce an answer. Please try again."

    @staticmethod
    def _build_tools(dispatcher: ToolDispatcher) -> list[Any]:
        """Wrap the shared dispatcher methods as SDK function tools."""

        @function_tool
        def record_unknown_question(question: str) -> dict[str, str]:
            """Record a question that could not be answered from George's background.

            Args:
                question: The exact question that could not be answered.
            """
            return dispatcher.record_unknown_question(question)

        @function_tool
        def record_contact_request(
            email: str, name: str = "unknown", notes: str = "no notes"
        ) -> dict[str, str]:
            """Record contact details of a visitor who wants to reach George.

            Args:
                email: Visitor's email address.
                name: Visitor's name, if given.
                notes: Context worth remembering, e.g. company or role.
            """
            return dispatcher.record_contact_request(email, name, notes)

        @function_tool
        def schedule_intro_call(topic: str = "not specified") -> dict[str, str]:
            """Get George's calendar booking link for an intro call.

            Args:
                topic: What the visitor wants to discuss, if known.
            """
            return dispatcher.schedule_intro_call(topic)

        tools: list[Any] = [record_unknown_question, record_contact_request]
        if any(s["function"]["name"] == "schedule_intro_call" for s in dispatcher.schemas()):
            tools.append(schedule_intro_call)
        return tools

    @staticmethod
    def _sanitize_history(history: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Strip Gradio metadata, keeping only role and content keys."""
        return [
            {"role": turn["role"], "content": turn["content"]}
            for turn in history
            if turn.get("role") in {"user", "assistant"} and turn.get("content")
        ]
