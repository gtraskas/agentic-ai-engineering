"""AskGeorge — an AI representative that answers recruiter questions as George Traskas.

Loads George's professional background from the ``me/`` directory, grounds an
LLM (any model via OpenRouter) in it, and serves a streaming Gradio chat
interface. Unknown questions and interested visitors are captured via tool
calls and emailed to George through Gmail SMTP (application log fallback).
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Iterator

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
DEFAULT_CHAT_MODEL: str = "google/gemini-3.5-flash"
DATA_DIR: Path = Path(__file__).parent / "me"
MAX_TOOL_ROUNDS: int = 3
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 465

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
        linkedin: Full LinkedIn profile export in Markdown.
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
            data_dir: Directory containing linkedin.md, summary.md, projects.md.

        Returns:
            A populated :class:`Profile`.

        Raises:
            FileNotFoundError: If any expected document is missing.
        """
        return cls(
            linkedin=(data_dir / "linkedin.md").read_text(encoding="utf-8"),
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


class EmailNotifier:
    """Emails notifications from George's Gmail to itself via SMTP.

    Uses a Gmail App Password (GMAIL_ADDRESS / GMAIL_APP_PASSWORD env vars).
    Falls back to the application log when not configured, so nothing is ever
    written to the container's ephemeral filesystem.
    """

    def __init__(self) -> None:
        self._address: str | None = os.getenv("GMAIL_ADDRESS")
        self._app_password: str | None = os.getenv("GMAIL_APP_PASSWORD")

    @property
    def is_configured(self) -> bool:
        """Return True if Gmail SMTP credentials are present."""
        return bool(self._address and self._app_password)

    def notify(self, subject: str, body: str) -> None:
        """Send a notification email, or log it as a fallback.

        Args:
            subject: Email subject line.
            body: Plain-text email body.
        """
        if not self.is_configured:
            logger.info("Notification (email not configured): %s — %s", subject, body)
            return
        email = EmailMessage()
        email["From"] = self._address
        email["To"] = self._address
        email["Subject"] = subject
        email.set_content(body)
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.login(self._address or "", self._app_password or "")
                server.send_message(email)
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("Email notification failed: %s", exc)


class AskGeorgeAgent:
    """Streaming chat agent that answers in first person as George Traskas.

    Grounds every answer in the loaded :class:`Profile` and uses tool calls to
    capture unknown questions and visitor contact requests.
    """

    def __init__(
        self,
        profile: Profile,
        notifier: EmailNotifier,
        client: OpenAI | None = None,
    ) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if client is None and not api_key:
            raise EnvironmentError("Set OPENROUTER_API_KEY to run AskGeorge.")
        self._client = client or OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
        self._model = os.getenv("OPENROUTER_MODEL", DEFAULT_CHAT_MODEL)
        self._notifier = notifier
        self._system_prompt = self._build_system_prompt(profile)

    def chat(self, message: str, history: list[dict[str, Any]]) -> Iterator[str]:
        """Stream one chat turn token by token, resolving tool calls between rounds.

        Args:
            message: The visitor's latest message.
            history: Prior turns in Gradio "messages" format.

        Yields:
            The growing reply text, suitable for Gradio streaming.
        """
        messages: list[Any] = [
            {"role": "system", "content": self._system_prompt},
            *self._sanitize_history(history),
            {"role": "user", "content": message},
        ]
        for _ in range(MAX_TOOL_ROUNDS):
            content, tool_calls = "", {}
            stream = self._client.chat.completions.create(
                model=self._model, messages=messages, tools=TOOL_SCHEMAS, stream=True
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
                    yield "Sorry — I could not produce an answer. Please try again."
                return
            messages.append(self._assistant_tool_message(content, tool_calls))
            for index in sorted(tool_calls):
                call = tool_calls[index]
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(
                            self._dispatch_tool(call["name"], call["arguments"])
                        ),
                    }
                )
        logger.warning("Tool-call rounds exceeded %d; returning fallback.", MAX_TOOL_ROUNDS)
        yield "Sorry, something went wrong on my side — please try asking again."

    def _dispatch_tool(self, name: str, arguments_json: str) -> dict[str, str]:
        """Execute a single tool call and return its JSON-serializable result.

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
        if name == "record_unknown_question":
            self._notifier.notify(
                subject="AskGeorge: unanswered question",
                body=f"A visitor asked something I could not answer:\n\n{arguments.get('question')}",
            )
        elif name == "record_contact_request":
            self._notifier.notify(
                subject="AskGeorge: new contact request",
                body=(
                    f"Name: {arguments.get('name', 'unknown')}\n"
                    f"Email: {arguments.get('email')}\n"
                    f"Notes: {arguments.get('notes', 'no notes')}"
                ),
            )
        else:
            logger.error("Unknown tool requested: %s", name)
            return {"status": "error", "detail": f"unknown tool {name}"}
        return {"status": "recorded"}

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
        A configured, launchable :class:`gr.ChatInterface` with streaming replies.
    """
    load_dotenv(override=True)
    logging.basicConfig(level=logging.INFO)
    agent = AskGeorgeAgent(profile=Profile.load(), notifier=EmailNotifier())
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
