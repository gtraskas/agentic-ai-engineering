"""AskGeorge — an AI representative that answers recruiter questions as George Traskas.

Loads George's professional background from the ``me/`` directory, grounds a
Gemini model in it, and serves a Gradio chat interface. Unknown questions and
interested visitors are captured via tool calls (Pushover push notification if
configured, application log otherwise).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
CHAT_MODEL: str = "gemini-2.5-flash"
DATA_DIR: Path = Path(__file__).parent / "me"
MAX_TOOL_ROUNDS: int = 3
PUSHOVER_API_URL: str = "https://api.pushover.net/1/messages.json"

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
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
    },
    {
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
    },
]


@dataclass(frozen=True)
class Profile:
    """George's background documents used to ground the assistant.

    Attributes:
        linkedin: Full LinkedIn profile export as plain text.
        summary: Distilled professional summary in Markdown.
        projects: Deep-dive project portfolio in Markdown.
    """

    linkedin: str
    summary: str
    projects: str

    @classmethod
    def load(cls, data_dir: Path = DATA_DIR) -> Profile:
        """Load all background documents from ``data_dir``.

        Args:
            data_dir: Directory containing linkedin.txt, summary.md, projects.md.

        Returns:
            A populated :class:`Profile`.

        Raises:
            FileNotFoundError: If any expected document is missing.
        """
        return cls(
            linkedin=(data_dir / "linkedin.txt").read_text(encoding="utf-8"),
            summary=(data_dir / "summary.md").read_text(encoding="utf-8"),
            projects=(data_dir / "projects.md").read_text(encoding="utf-8"),
        )

    def as_context(self) -> str:
        """Return the documents merged into a single prompt context block."""
        return (
            f"## Professional summary\n\n{self.summary}\n\n"
            f"## LinkedIn profile\n\n{self.linkedin}\n\n"
            f"## Project portfolio\n\n{self.projects}"
        )


class NotificationService:
    """Sends push notifications via Pushover, falling back to the app log.

    Attributes:
        is_configured: True when Pushover credentials are available.
    """

    def __init__(self) -> None:
        self._token: str | None = os.getenv("PUSHOVER_TOKEN")
        self._user: str | None = os.getenv("PUSHOVER_USER")

    @property
    def is_configured(self) -> bool:
        """Return True if Pushover credentials are present."""
        return bool(self._token and self._user)

    def notify(self, message: str) -> None:
        """Send ``message`` as a push notification, or log it as a fallback.

        Args:
            message: Human-readable notification text.
        """
        if not self.is_configured:
            logger.info("Notification (Pushover not configured): %s", message)
            return
        try:
            response = requests.post(
                PUSHOVER_API_URL,
                data={"token": self._token, "user": self._user, "message": message},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Pushover notification failed: %s", exc)


class AskGeorgeAgent:
    """Chat agent that answers questions in first person as George Traskas.

    Grounds every answer in the loaded :class:`Profile` and uses tool calls to
    capture unknown questions and visitor contact requests.
    """

    def __init__(
        self,
        profile: Profile,
        notifier: NotificationService,
        client: OpenAI | None = None,
    ) -> None:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if client is None and not api_key:
            raise EnvironmentError(
                "Set GOOGLE_API_KEY (or GEMINI_API_KEY) to run AskGeorge."
            )
        self._client = client or OpenAI(base_url=GEMINI_BASE_URL, api_key=api_key)
        self._notifier = notifier
        self._system_prompt = self._build_system_prompt(profile)

    def chat(self, message: str, history: list[dict[str, Any]]) -> str:
        """Answer one chat turn, resolving any tool calls along the way.

        Args:
            message: The visitor's latest message.
            history: Prior turns in Gradio "messages" format.

        Returns:
            The assistant's reply text.
        """
        messages: list[Any] = [
            {"role": "system", "content": self._system_prompt},
            *self._sanitize_history(history),
            {"role": "user", "content": message},
        ]
        for _ in range(MAX_TOOL_ROUNDS):
            choice = self._client.chat.completions.create(
                model=CHAT_MODEL, messages=messages, tools=TOOL_SCHEMAS
            ).choices[0]
            if choice.finish_reason != "tool_calls":
                return choice.message.content or ""
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls or []:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(self._dispatch_tool(tool_call)),
                    }
                )
        logger.warning("Tool-call rounds exceeded %d; returning fallback.", MAX_TOOL_ROUNDS)
        return "Sorry, something went wrong on my side — please try asking again."

    def _dispatch_tool(self, tool_call: Any) -> dict[str, str]:
        """Execute a single tool call and return its JSON-serializable result."""
        arguments = json.loads(tool_call.function.arguments or "{}")
        name = tool_call.function.name
        if name == "record_unknown_question":
            self._notifier.notify(f"AskGeorge could not answer: {arguments.get('question')}")
        elif name == "record_contact_request":
            self._notifier.notify(
                "AskGeorge contact request: "
                f"{arguments.get('name', 'unknown')} <{arguments.get('email')}> — "
                f"{arguments.get('notes', 'no notes')}"
            )
        else:
            logger.error("Unknown tool requested: %s", name)
            return {"status": "error", "detail": f"unknown tool {name}"}
        return {"status": "recorded"}

    @staticmethod
    def _sanitize_history(history: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Strip Gradio metadata, keeping only role and content keys."""
        return [
            {"role": turn["role"], "content": turn["content"]}
            for turn in history
            if turn.get("role") in {"user", "assistant"} and turn.get("content")
        ]

    @staticmethod
    def _build_system_prompt(profile: Profile) -> str:
        """Compose the grounded first-person system prompt."""
        return (
            "You are acting as Georgios (George) Traskas, answering questions on his "
            "professional page. Speak in the first person, as George, to visitors such "
            "as recruiters, hiring managers, and potential clients.\n\n"
            "Rules:\n"
            "- Be professional, warm, and concise; answer like a confident engineer in "
            "a friendly interview.\n"
            "- Ground every claim strictly in the background below. Never invent "
            "employers, dates, metrics, or skills.\n"
            "- If a question cannot be answered from the background, say so honestly "
            "and call record_unknown_question with the exact question.\n"
            "- If the visitor shows interest in working with George, ask for their "
            "email and call record_contact_request with it.\n"
            "- For follow-ups, share George's email (georgiost77@gmail.com), LinkedIn "
            "(linkedin.com/in/george-traskas), and GitHub (github.com/gtraskas).\n"
            "- Politely decline topics unrelated to George's professional profile.\n\n"
            f"# Background\n\n{profile.as_context()}"
        )


def build_demo() -> gr.ChatInterface:
    """Create the Gradio chat interface for AskGeorge.

    Returns:
        A configured, launchable :class:`gr.ChatInterface`.
    """
    load_dotenv(override=True)
    logging.basicConfig(level=logging.INFO)
    agent = AskGeorgeAgent(profile=Profile.load(), notifier=NotificationService())
    return gr.ChatInterface(
        fn=agent.chat,
        type="messages",
        title="AskGeorge",
        description=(
            "Hi, I'm George Traskas' AI representative — ask me anything about his "
            "experience, projects, and skills as a Data Scientist and AI/ML Engineer."
        ),
        examples=[
            "What is your experience with RAG in production?",
            "Tell me about your most recent project.",
            "Why should we hire you as an AI engineer?",
            "Are you open to remote roles?",
        ],
    )


if __name__ == "__main__":
    build_demo().launch()
