"""From-scratch agent backend: a hand-rolled streaming tool-calling loop.

Kept as a first-class, runnable baseline alongside the SDK backend — it shows
exactly what a framework abstracts away.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from typing import Any

from openai import OpenAI

from askgeorge.core.config import (
    CHAT_MODEL,
    MAX_TOOL_ROUNDS,
    OPENROUTER_BASE_URL,
    TEMPERATURE,
    openrouter_extra_body,
)
from askgeorge.core.knowledge import BackgroundKnowledge
from askgeorge.core.language import SearchQueryTranslator
from askgeorge.core.profile import Profile
from askgeorge.core.prompts import augment_with_context, build_system_prompt
from askgeorge.core.tools import ToolDispatcher

logger = logging.getLogger(__name__)


class ScratchAgent:
    """Streaming chat agent built directly on the chat-completions API."""

    def __init__(
        self,
        profile: Profile,
        knowledge: BackgroundKnowledge,
        dispatcher: ToolDispatcher,
        client: OpenAI | None = None,
    ) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if client is None and not api_key:
            raise OSError("Set OPENROUTER_API_KEY to run AskGeorge.")
        self._client = client or OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        self._model = CHAT_MODEL
        self._knowledge = knowledge
        self._translator = SearchQueryTranslator(self._client)
        self._dispatcher = dispatcher
        self._system_prompt = build_system_prompt(profile)

    def chat(self, message: str, history: list[dict[str, Any]]) -> Iterator[str]:
        """Stream one chat turn token by token, resolving tool calls between rounds.

        Args:
            message: The visitor's latest message.
            history: Prior turns in Gradio "messages" format.

        Yields:
            The growing reply text, suitable for Gradio streaming.
        """
        # Retrieval searches an English corpus with an English-only
        # embedding model, so a non-English question is translated first
        context = self._knowledge.context_for(self._translator.to_english(message))
        messages: list[Any] = [
            {"role": "system", "content": self._system_prompt},
            *self._sanitize_history(history),
            {"role": "user", "content": augment_with_context(message, context)},
        ]
        for _ in range(MAX_TOOL_ROUNDS):
            content, tool_calls = "", {}
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=self._dispatcher.schemas(),
                stream=True,
                temperature=TEMPERATURE,
                extra_body=openrouter_extra_body(),
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta is None:
                    continue
                if delta.content:
                    content += delta.content
                    yield content
                for call_delta in delta.tool_calls or []:
                    slot = tool_calls.setdefault(
                        call_delta.index, {"id": "", "name": "", "arguments": ""}
                    )
                    slot["id"] = call_delta.id or slot["id"]
                    if call_delta.function is not None:
                        slot["name"] = call_delta.function.name or slot["name"]
                        slot["arguments"] += call_delta.function.arguments or ""
            if not tool_calls:
                if not content:
                    yield "Sorry, I could not produce an answer. Please try again."
                return
            messages.append(self._assistant_tool_message(content, tool_calls))
            for index in sorted(tool_calls):
                call = tool_calls[index]
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(
                            self._dispatcher.dispatch(call["name"], call["arguments"])
                        ),
                    }
                )
        logger.warning("Tool-call rounds exceeded %d; returning fallback.", MAX_TOOL_ROUNDS)
        yield "Sorry, something went wrong on my side. Please try asking again."

    @staticmethod
    def _assistant_tool_message(
        content: str, tool_calls: dict[int, dict[str, str]]
    ) -> dict[str, Any]:
        """Rebuild the assistant message that carried the streamed tool calls."""
        return {
            "role": "assistant",
            "content": content or None,
            "tool_calls": [
                {
                    "id": tool_calls[index]["id"],
                    "type": "function",
                    "function": {
                        "name": tool_calls[index]["name"],
                        "arguments": tool_calls[index]["arguments"],
                    },
                }
                for index in sorted(tool_calls)
            ],
        }

    @staticmethod
    def _sanitize_history(history: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Strip Gradio metadata, keeping only role and content keys."""
        return [
            {"role": turn["role"], "content": turn["content"]}
            for turn in history
            if turn.get("role") in {"user", "assistant"} and turn.get("content")
        ]
