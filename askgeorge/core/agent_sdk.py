"""OpenAI Agents SDK backend: same behavior as the scratch loop, framework-managed.

Follows the production guidance for the SDK: a single agent, function tools,
no handoffs, tracing disabled (no OpenAI key in this deployment), and a
non-OpenAI model wired via ``OpenAIChatCompletionsModel`` over OpenRouter.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from agents import (
    Agent,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from agents.exceptions import InputGuardrailTripwireTriggered
from openai import AsyncOpenAI
from openai.types.responses import ResponseCreatedEvent, ResponseTextDeltaEvent

from askgeorge.core.config import (
    CHAT_MODEL,
    OPENROUTER_BASE_URL,
    TEMPERATURE,
    openrouter_extra_body,
)
from askgeorge.core.guardrail import GUARDRAIL_REFUSAL, build_scope_guardrail
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
            raise OSError("Set OPENROUTER_API_KEY to run AskGeorge.")
        set_tracing_disabled(True)
        self._knowledge = knowledge
        model = OpenAIChatCompletionsModel(
            model=CHAT_MODEL,
            openai_client=AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key),
        )
        self._agent = Agent(
            name="AskGeorge",
            instructions=build_system_prompt(profile),
            model=model,
            model_settings=ModelSettings(
                temperature=TEMPERATURE, extra_body=openrouter_extra_body()
            ),
            tools=self._build_tools(dispatcher),
            input_guardrails=[build_scope_guardrail(model)],
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
        # The raw message travels as the run context so the scope guardrail can
        # judge what the visitor actually typed, not the augmented prompt.
        result = Runner.run_streamed(self._agent, input=input_items, context=message)
        reply = ""
        # Reset the reply only when a tool call actually started a fresh model
        # turn. Resetting on every ResponseCreatedEvent wiped the answer
        # mid-stream when a provider split one reply across response events,
        # leaving visitors a garbage tail fragment.
        tool_round_started = False
        try:
            async for event in result.stream_events():
                if (
                    event.type == "run_item_stream_event"
                    and getattr(event.item, "type", "") == "tool_call_item"
                ):
                    tool_round_started = True
                    continue
                if event.type != "raw_response_event":
                    continue
                if isinstance(event.data, ResponseCreatedEvent):
                    if tool_round_started:
                        reply = ""
                        tool_round_started = False
                elif isinstance(event.data, ResponseTextDeltaEvent):
                    reply += event.data.delta
                    yield reply
        except InputGuardrailTripwireTriggered:
            yield GUARDRAIL_REFUSAL
            return
        if not reply:
            final = str(result.final_output or "")
            yield final or "Sorry, I could not produce an answer. Please try again."

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
            """Notify George that a visitor wants to be contacted.

            Call as soon as the visitor shares their email address. Never
            invent or guess an email.

            Args:
                email: Visitor's email address.
                name: Visitor's name, if given.
                notes: Everything known: who they are, company, role.
            """
            return dispatcher.record_contact_request(email, name, notes)

        return [record_unknown_question, record_contact_request]

    @staticmethod
    def _sanitize_history(history: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Strip Gradio metadata, keeping only role and content keys."""
        return [
            {"role": turn["role"], "content": turn["content"]}
            for turn in history
            if turn.get("role") in {"user", "assistant"} and turn.get("content")
        ]
