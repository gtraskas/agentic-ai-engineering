"""Central configuration: paths, model settings, and environment accessors.

Deliberately minimal: the only environment variables the app reads are
OPENROUTER_API_KEY, AGENT_BACKEND, ASKGEORGE_RAG, CALENDAR_BOOKING_URL,
GMAIL_ADDRESS, and GMAIL_APP_PASSWORD. Everything else (models, sampling,
reasoning effort) is a constant here — change it in code, not in env.
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR: Path = Path(__file__).parent.parent
DATA_DIR: Path = PACKAGE_DIR / "me"
ASSETS_DIR: Path = PACKAGE_DIR / "ui" / "assets"

PUBLIC_BASE_URL: str = "https://gtraskas--askgeorge-web.modal.run"

OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
# Fast, consistent, and cheap (~$0.10/M input tokens); with the global
# 100-messages/day rate cap the worst-case spend is pennies. The fallback
# is the best free model from the Aug 2026 benchmark (gemma: 4/4 clean
# runs, obeys formatting rules, correct tool calls, valid guardrail
# structured output), covering paid-model outages at zero cost.
CHAT_MODEL: str = "google/gemini-3.1-flash-lite"
FALLBACK_MODEL: str = "google/gemma-4-26b-a4b-it:free"
REASONING_EFFORT: str = "low"
TEMPERATURE: float = 0.7
MAX_TOOL_ROUNDS: int = 3

EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
SPARSE_EMBEDDING_MODEL: str = "Qdrant/bm25"
RAG_COLLECTION: str = "background"
RAG_TOP_K: int = 10
CHUNK_MAX_CHARS: int = 1_200

JOBFIT_MIN_CHARS: int = 120
JOBFIT_MAX_CHARS: int = 8_000

SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 465


def openrouter_api_key() -> str | None:
    """Return the OpenRouter API key, if configured."""
    return os.getenv("OPENROUTER_API_KEY")


def openrouter_extra_body() -> dict[str, object]:
    """Return the OpenRouter extra body shared by every LLM call.

    Two concerns travel here. ``reasoning``: reasoning-capable models think
    silently before writing, which delays the first streamed token, so the
    effort is capped low. ``models``: OpenRouter's server-side fallback
    chain, so a rate-limited or unavailable primary silently falls through
    to the free fallback instead of failing the visitor's request.
    """
    return {
        "reasoning": {"effort": REASONING_EFFORT},
        "models": [CHAT_MODEL, FALLBACK_MODEL],
    }


def agent_backend() -> str:
    """Return the selected agent backend: 'sdk' (default) or 'scratch'."""
    return os.getenv("AGENT_BACKEND", "sdk").strip().lower()


def rag_enabled() -> bool:
    """Return True unless RAG is disabled with ASKGEORGE_RAG=0."""
    return os.getenv("ASKGEORGE_RAG", "1") != "0"


def booking_url() -> str | None:
    """Return the Google Calendar booking-page URL, if configured."""
    return os.getenv("CALENDAR_BOOKING_URL")
