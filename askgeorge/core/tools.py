"""Agent tools: schemas for the scratch backend and a shared dispatcher."""

from __future__ import annotations

import json
import logging
from typing import Any

from askgeorge.core.config import booking_url
from askgeorge.core.notifier import EmailNotifier

logger = logging.getLogger(__name__)

_RECORD_UNKNOWN_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "record_unknown_question",
        "description": (
            "Record any question that could not be answered from George's "
            "background, so he can follow up personally."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question that could not be answered.",
                }
            },
            "required": ["question"],
        },
    },
}

_RECORD_CONTACT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "record_contact_request",
        "description": (
            "Record contact details of a visitor who wants to get in touch "
            "with George (e.g. a recruiter interested in his profile)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Visitor's email address."},
                "name": {"type": "string", "description": "Visitor's name, if given."},
                "notes": {
                    "type": "string",
                    "description": "Context worth remembering, e.g. company or role.",
                },
            },
            "required": ["email"],
        },
    },
}

_SCHEDULE_CALL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "schedule_intro_call",
        "description": (
            "Get George's calendar booking link for an intro call. Call this "
            "when a visitor wants to talk to George directly, then share the "
            "returned link with them."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "What the visitor wants to discuss, if known.",
                }
            },
            "required": [],
        },
    },
}


class ToolDispatcher:
    """Executes agent tools, notifying George by email where appropriate."""

    def __init__(self, notifier: EmailNotifier) -> None:
        self._notifier = notifier

    def schemas(self) -> list[dict[str, Any]]:
        """Return the OpenAI tool schemas active for this deployment."""
        active = [_RECORD_UNKNOWN_SCHEMA, _RECORD_CONTACT_SCHEMA]
        if booking_url():
            active.append(_SCHEDULE_CALL_SCHEMA)
        return active

    def record_unknown_question(self, question: str) -> dict[str, str]:
        """Email George a question the assistant could not answer."""
        self._notifier.notify(
            subject="AskGeorge: unanswered question",
            body=f"A visitor asked something I could not answer:\n\n{question}",
        )
        return {"status": "recorded"}

    def record_contact_request(
        self, email: str, name: str = "unknown", notes: str = "no notes"
    ) -> dict[str, str]:
        """Email George a visitor's contact details and context."""
        self._notifier.notify(
            subject="AskGeorge: new contact request",
            body=f"Name: {name}\nEmail: {email}\nNotes: {notes}",
        )
        return {"status": "recorded"}

    def schedule_intro_call(self, topic: str = "not specified") -> dict[str, str]:
        """Return George's booking link and email him the visitor's topic."""
        url = booking_url()
        if not url:
            return {"status": "error", "detail": "booking link not configured"}
        self._notifier.notify(
            subject="AskGeorge: intro call requested",
            body=f"A visitor asked to book an intro call.\nTopic: {topic}",
        )
        return {"status": "ok", "booking_url": url}

    def dispatch(self, name: str, arguments_json: str) -> dict[str, str]:
        """Execute a tool by name with JSON-encoded arguments (scratch backend).

        Args:
            name: Tool name requested by the model.
            arguments_json: JSON-encoded tool arguments.

        Returns:
            A status dict fed back to the model as the tool result.
        """
        try:
            arguments = json.loads(arguments_json or "{}")
        except json.JSONDecodeError as exc:
            logger.error("Malformed tool arguments for %s: %s", name, exc)
            return {"status": "error", "detail": "malformed arguments"}
        handlers = {
            "record_unknown_question": self.record_unknown_question,
            "record_contact_request": self.record_contact_request,
            "schedule_intro_call": self.schedule_intro_call,
        }
        handler = handlers.get(name)
        if handler is None:
            logger.error("Unknown tool requested: %s", name)
            return {"status": "error", "detail": f"unknown tool {name}"}
        return handler(**arguments)
