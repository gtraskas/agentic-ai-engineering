"""Prompt construction shared by both agent backends."""

from __future__ import annotations

from askgeorge.core.config import booking_url
from askgeorge.core.profile import Profile

_BASE_RULES: str = (
    "You are acting as Georgios (George) Traskas, answering questions on his "
    "professional page. Speak in the first person, as George, to visitors such "
    "as recruiters, hiring managers, and potential clients.\n\n"
    "Rules:\n"
    "- Be professional, warm, and concise; answer like a confident engineer in "
    "a friendly interview.\n"
    "- Ground every claim strictly in the pinned summary and the retrieved "
    "background context provided with each question. Never invent employers, "
    "dates, metrics, or skills.\n"
    "- If a question cannot be answered from the available background, say so "
    "honestly and call record_unknown_question with the exact question.\n"
    "- If the visitor shows interest in working with George, ask for their "
    "email and call record_contact_request with it.\n"
    "- For follow-ups, share George's email (georgiost77@gmail.com), LinkedIn "
    "(linkedin.com/in/george-traskas), and GitHub (github.com/gtraskas).\n"
    "- Politely decline topics unrelated to George's professional profile.\n"
)

_BOOKING_RULE: str = (
    "- If the visitor wants to talk to George directly, call schedule_intro_call "
    "to get his booking link and share it.\n"
)


def build_system_prompt(profile: Profile) -> str:
    """Compose the grounded first-person system prompt.

    Args:
        profile: The loaded background corpus (only the summary is pinned here;
            the rest arrives per-question via retrieval).

    Returns:
        The complete system prompt string.
    """
    rules = _BASE_RULES + (_BOOKING_RULE if booking_url() else "")
    return f"{rules}\n# Pinned professional summary\n\n{profile.summary}"


def augment_with_context(message: str, context: str) -> str:
    """Attach retrieved background context to the visitor's message.

    Args:
        message: The visitor's raw question.
        context: Retrieved background chunks (or the full corpus).

    Returns:
        The message the model actually receives; the UI keeps showing the raw one.
    """
    return (
        f"{message}\n\n"
        "<retrieved_background>\n"
        "Background retrieved for this question (ground your answer here and "
        f"in the pinned summary):\n\n{context}\n"
        "</retrieved_background>"
    )
